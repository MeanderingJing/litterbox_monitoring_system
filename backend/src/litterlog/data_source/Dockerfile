# Export locked dependencies from Poetry, then install with pip (no Poetry in final image).
FROM python:3.12-slim AS deps

RUN pip install --no-cache-dir poetry==1.8.3

WORKDIR /build
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --without-hashes --only main -o requirements.txt

FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
# Security Principle: Principle of Least Privilege
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=deps /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application package
COPY src/litterlog/ ./litterlog/

# Consider adding Healthcheck in the future

ENV PYTHONPATH=/app

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Command to run the litterbox edge device simulator
CMD ["python", "-m", "litterlog.data_source.litterbox_edge_device_simulator"]
