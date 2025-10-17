FROM python:3.11-slim

# Install system dependencies
# Install gcc and libpq-dev for PostgreSQL support to assist building psycopg2 from source
# Recommended for production use
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
# Security Principle: Principle of Least Privilege
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/config/ ./config/
COPY src/models/ ./models/
COPY src/rabbitmq_support/ ./rabbitmq_support/
COPY src/data_source/ ./data_source/

# Consider adding Healthcheck in the future

ENV PYTHONPATH=/app

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Command to run the litterbox edge device simulator
CMD ["python", "data_source/litterbox_edge_device_simulator.py"]

