FROM golden:latest

WORKDIR /app

# Install deps first (layer cache)
COPY ../../requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
COPY ../.. .

# FastAPI runs on 8000 in this image
EXPOSE 443

# Simple healthcheck (FastAPI always serves openapi.json)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -fsS https://127.0.0.1/openapi.json >/dev/null || exit 1

# Run with uvicorn (uses app.py -> app = FastAPI(...))
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "443"]
