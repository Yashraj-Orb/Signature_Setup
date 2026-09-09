# Orbrick Studio

The project runs as one deployable FastAPI service with two browser tools:

- `/signature/` is the email signature generator. It calls `/remove-background` on the same origin.
- `/backgrounds/` is the browser-only Teams background generator. It creates 1920x1080 PNGs locally with Canvas and does not require a backend endpoint.
- `/` is the tool selector.
- `api.py` loads the `rembg` model once during application startup, configures ONNX Runtime, and serves both tools and the API from the same process.
- `frontend/` contains the selector, signature tool, background generator, and its bundled background images.

## Run locally

Install the API dependencies:

```powershell
pip install -r requirements-api.txt
```

Start the application:

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

Open the tool selector at `http://localhost:8000`.

The individual tools are available at:

- `http://localhost:8000/signature/`
- `http://localhost:8000/backgrounds/`

The readiness endpoint is `GET /health/ready`. It returns `503` until the model session has loaded, then `200`.

## Docker deployment

The `Dockerfile` installs the API, downloads the configured `u2net` model during image build, and starts Uvicorn. FastAPI serves the custom frontend on the same port as the API. The image uses the platform-provided `PORT` variable when available and defaults to `8000` locally.

Optional environment variables:

```text
REMBG_MODEL=u2net
MAX_CONCURRENT_TASKS=1
ONNX_INTRA_OP_THREADS=1
ONNX_INTER_OP_THREADS=1
```

No separate frontend service or frontend URL variable is required because the browser calls the API on the same origin. The image health check uses `GET /health/ready` and waits for the rembg model to load.

Keep the service on one worker and one replica unless the deployment platform has enough memory for each additional model copy. The first request should not download the model; it is present in the image and loaded before the service is marked ready.

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

The signature tool preserves its existing controls and output. The background generator is integrated from the standalone browser project without changing its template selection, custom image upload, editable fields, or PNG download behavior.
