FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/config/ ./config/
COPY src/models/ ./models/
COPY src/rabbitmq_support/ ./rabbitmq_support/
COPY src/data_source_simulator/ ./data_source_simulator/

# Consider adding Healthcheck in the future

# Command to run the litterbox edge device simulator
CMD ["python", "litterbox_edge_device_simulator.py"]

