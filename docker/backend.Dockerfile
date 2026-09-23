FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install uv for rapid dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml README.md ./

# Install dependencies first (without building the local package)
RUN uv pip install --system --no-cache -r pyproject.toml --extra dev

# Copy the actual code
COPY backend/ ./backend/
COPY --chmod=755 scripts/backend-entrypoint.sh /usr/local/bin/backend-entrypoint

# Install the project itself (editable or standard)
RUN uv pip install --system --no-cache --no-deps -e .

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data/raw /app/data/parquet && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["backend-entrypoint"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
