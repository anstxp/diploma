FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY risk_api/ ./risk_api/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/risk/healthz')" || exit 1

CMD ["uvicorn", "risk_api.app:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
