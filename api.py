import asyncio
import logging
import os
import tempfile
import time
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from rembg import new_session, remove
import onnxruntime as ort


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("background-removal-api")

MODEL_NAME = os.getenv("REMBG_MODEL", "u2net")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(15 * 1024 * 1024)))
INFERENCE_TIMEOUT_SECONDS = float(os.getenv("INFERENCE_TIMEOUT_SECONDS", "120"))
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "1"))
ONNX_INTRA_OP_THREADS = int(os.getenv("ONNX_INTRA_OP_THREADS", "1"))
ONNX_INTER_OP_THREADS = int(os.getenv("ONNX_INTER_OP_THREADS", "1"))
executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASKS)


def configured_origins() -> list[str]:
    value = os.getenv("CORS_ORIGINS", "http://localhost:8501")
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def create_rembg_session():
    session_options = ort.SessionOptions()
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session_options.intra_op_num_threads = ONNX_INTRA_OP_THREADS
    session_options.inter_op_num_threads = ONNX_INTER_OP_THREADS
    return new_session(MODEL_NAME, sess_opts=session_options)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rembg_session = None
    app.state.model_loaded_at = None
    started_at = time.perf_counter()

    logger.info("Loading rembg model '%s'", MODEL_NAME)
    app.state.rembg_session = create_rembg_session()
    app.state.model_loaded_at = time.time()
    logger.info("Model ready in %.2fs", time.perf_counter() - started_at)

    try:
        yield
    finally:
        executor.shutdown(wait=True, cancel_futures=True)


app = FastAPI(title="Background Removal API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)


def process_image(image_bytes: bytes, session) -> bytes:
    """Run inference in an isolated temporary workspace and clean it up."""
    with tempfile.TemporaryDirectory(prefix="rembg-") as temp_dir:
        input_path = os.path.join(temp_dir, "input")
        output_path = os.path.join(temp_dir, "output.png")
        with open(input_path, "wb") as input_file:
            input_file.write(image_bytes)

        with open(input_path, "rb") as input_file:
            output_bytes = remove(input_file.read(), session=session)

        with open(output_path, "wb") as output_file:
            output_file.write(output_bytes)
        with open(output_path, "rb") as output_file:
            return output_file.read()


@app.get("/api-info")
async def root():
    return {"service": "background-removal-api", "model": MODEL_NAME}


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    if app.state.rembg_session is None:
        raise HTTPException(status_code=503, detail="rembg model is still loading")
    return {
        "status": "ready",
        "model": MODEL_NAME,
        "model_loaded_at": app.state.model_loaded_at,
    }


@app.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    session = app.state.rembg_session
    if session is None:
        raise HTTPException(status_code=503, detail="rembg model is not ready")

    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the upload limit")
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    started_at = time.perf_counter()
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(executor, process_image, image_bytes, session)
    try:
        output_bytes = await asyncio.wait_for(future, timeout=INFERENCE_TIMEOUT_SECONDS)
    except asyncio.TimeoutError as exc:
        logger.warning("Inference timed out after %.1fs", INFERENCE_TIMEOUT_SECONDS)
        raise HTTPException(status_code=504, detail="Background removal timed out") from exc
    except Exception:
        logger.exception("Background removal failed")
        raise HTTPException(status_code=500, detail="Background removal failed")

    inference_seconds = time.perf_counter() - started_at
    return Response(
        content=output_bytes,
        media_type="image/png",
        headers={"X-Inference-Seconds": f"{inference_seconds:.3f}"},
    )


@app.get("/", include_in_schema=False)
async def frontend():
    return FileResponse("frontend/index.html")


@app.get("/signature", include_in_schema=False)
@app.get("/signature/", include_in_schema=False)
async def signature_frontend():
    return FileResponse("frontend/signature/index.html")


app.mount("/assets", StaticFiles(directory="frontend"), name="frontend-assets")
app.mount("/backgrounds", StaticFiles(directory="frontend/backgrounds", html=True), name="background-generator")
