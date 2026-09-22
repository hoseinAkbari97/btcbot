FROM python:3.12-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache gcc musl-dev postgresql-dev && rm -rf /var/cache/apk/*

# Copy pyproject.toml and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .[dev]

# Copy application code
COPY backend/ ./app/

# Create data directories
RUN mkdir -p /app/data/raw /app/data/parquet

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]