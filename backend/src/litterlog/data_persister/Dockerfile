# Export locked dependencies from Poetry, then install with pip (no Poetry in final image).
FROM python:3.12-slim AS deps

RUN pip install --no-cache-dir poetry==1.8.3

WORKDIR /build
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --without-hashes --only main -o requirements.txt

FROM python:3.11-slim

# Install gcc and libpq-dev for PostgreSQL support when building psycopg2 from source
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=deps /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/litterlog/ ./litterlog/

ENV PYTHONPATH=/app

RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "-m", "litterlog.data_persister.data_persister"]
