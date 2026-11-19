# pa-api: the FastAPI layer over the existing Python engine (task T-40).
# Based on the production Dockerfile (same base, Tesseract and spaCy model). The build context is
# the repository root, so Railway's "Dockerfile path" for this service is backend/Dockerfile.
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# The engine's packages (includes the spaCy name model) plus the API's own.
COPY requirements.txt ./requirements.txt
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r backend/requirements.txt

COPY . .

# Name detection for redaction. Without it the sanitizer only catches names after labels such as
# "Borrower:", and the Spanish Reply tool refuses to translate (it fails closed).
ENV PII_NER_MODEL=en_core_web_md

EXPOSE 8080

# Railway sets PORT. /api/health is the health check.
CMD ["sh", "-c", "uvicorn backend.pa_api.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
