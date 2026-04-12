FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY --from=builder /install /usr/local

# Copy engine + API code (NOT weights — those mount as volume)
COPY neuro_api/ ./neuro_api/

# Strip out weights from the image — they should be volume-mounted
RUN rm -rf neuro_api/weights/*.pt neuro_api/weights/*.bak 2>/dev/null || true

RUN chown -R app:app /app
USER app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    LOG_LEVEL=INFO

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/neuro/healthz')" || exit 1

CMD ["uvicorn", "neuro_api.app:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "2"]
