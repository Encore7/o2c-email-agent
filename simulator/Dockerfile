FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md /app/
COPY app /app/app
COPY data /app/data

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

CMD ["python", "-m", "app.main", "--tenant-id", "tenant_id", "--date", "2026-01-20", "--mode", "ordered", "--backend-url", "http://backend:8000", "--postgres-dsn", "postgresql://o2c:o2c@postgres:5432/o2c"]
