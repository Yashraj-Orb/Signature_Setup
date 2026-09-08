# Orbrick Signature Studio

The project runs as one deployable Railway service:

- `api.py` is the FastAPI backend. It loads the `rembg` model once during application startup, configures ONNX Runtime, and serves the frontend and API from the same process.
- `frontend/` is the custom HTML, CSS, and JavaScript frontend. It calls `/remove-background` on the same origin.

## Run locally

Install the API dependencies:

```powershell
pip install -r requirements-api.txt
```

Start the application:

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

Open the frontend at `http://localhost:8000`.

The readiness endpoint is `GET /health/ready`. It returns `503` until the model session has loaded, then `200`.

## Docker and Railway

The `Dockerfile` installs the API, downloads the configured `u2net` model during image build, and starts Uvicorn. FastAPI serves the custom frontend on the same public port as the API. Railway should run this Dockerfile as one persistent service with one replica. `railway.json` health-checks the public root route.

Optional Railway variables:

```text
REMBG_MODEL=u2net
MAX_CONCURRENT_TASKS=1
ONNX_INTRA_OP_THREADS=1
ONNX_INTER_OP_THREADS=1
```

No separate frontend service or frontend URL variable is required because the browser calls the API on the same origin.

Keep the service on one worker and one replica. Each additional worker or replica loads another copy of the model into memory.

## Baseline benchmark

Record these values from the Railway deployment before changing concurrency or replicas:

1. Build time and container startup time until `/health/ready` returns `200`.
2. Peak RAM and CPU during startup and one inference.
3. `X-Inference-Seconds` from the image response for several small, medium, and large images.
4. End-to-end upload time, including network transfer.

The first request should no longer download the model; the model is present in the image and loaded before the service is marked ready.

## Local Docker verification

Build the image from the project root:

```powershell
docker build -t orbrick-background-app:local .
```

Run it:

```powershell
docker run --rm --name orbrick-background-app -p 8000:8000 orbrick-background-app:local
```

Open `http://localhost:8000`, upload a photo, and verify the generated signature. Inspect the startup logs to confirm that the model loads once before the API becomes ready.

The frontend preserves the existing controls and signature output while replacing the Streamlit interface with a custom responsive editor.
