FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY api_data ./api_data
COPY scripts ./scripts

EXPOSE 8000
CMD ["sh", "-c", "python -c 'from app.database import ensure_schema; ensure_schema()' && python scripts/import_api_data.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
