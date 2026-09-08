FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    U2NET_HOME=/root/.u2net \
    REMBG_MODEL=u2net \
    MAX_CONCURRENT_TASKS=1

WORKDIR /app

COPY requirements-api.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-api.txt

# Download the model while building the image, not during the first request.
RUN python -c "from rembg import new_session; new_session('u2net')"

COPY api.py ./
COPY frontend ./frontend

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
