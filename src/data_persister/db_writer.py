import json
import pika
import os
import signal
import sys
import time
from typing import Dict, List
from datetime import datetime
import uuid

from config.logging import get_logger
from rabbitmq_support.rabbitmq_gateway import (
    CONNECTION_PARAMS,
    EXCHANGE_NAME,
    ROUTING_KEY,
    QUEUE_NAME,
)
from database.postgresql_gateway import PostgreSQLGateway

logger = get_logger(__name__)

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://example_user:example_password@localhost:5435/example_db",
)

# Consumer Configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))  # Process messages in batches
BATCH_TIMEOUT = int(os.getenv("BATCH_TIMEOUT", "30"))  # Max seconds to wait for batch
PREFETCH_COUNT = int(os.getenv("PREFETCH_COUNT", "50"))  # How many messages to prefetch


class LitterboxConsumer:
    def __init__(self):
        self.db_gateway = PostgreSQLGateway(DATABASE_URL)
        self.connection = None
        self.channel = None
        self.should_stop = False
        self.message_batch = []
        self.last_batch_time = time.time()

        # Set up connection parameters
        self.connection_params = CONNECTION_PARAMS

        logger.info(
            f"Consumer initialized with batch size: {BATCH_SIZE}, timeout: {BATCH_TIMEOUT}s"
        )

    def setup_database(self):
        """Initialize database connection and create tables if needed"""
        try:
            self.db_gateway.connect()
            self.db_gateway.create_tables()
            logger.info("Database setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise

    def setup_rabbitmq(self):
        """Setup RabbitMQ connection, channel, and queue"""
        try:
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()

            # Declare exchange (should match producer)
            self.channel.exchange_declare(
                exchange=EXCHANGE_NAME, exchange_type="topic", durable=True
            )

            # Declare queue and bind to exchange
            self.channel.queue_declare(
                queue=QUEUE_NAME, durable=True, exclusive=False, auto_delete=False
            )

            # Bind queue to exchange with routing key
            self.channel.queue_bind(
                exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY
            )

            # Set QoS to control message prefetching
            self.channel.basic_qos(prefetch_count=PREFETCH_COUNT)

            logger.info(
                f"RabbitMQ setup completed. Queue '{QUEUE_NAME}' bound to exchange '{EXCHANGE_NAME}'"
            )

        except Exception as e:
            logger.error(f"Failed to setup RabbitMQ: {e}")
            raise

    def _parse_message(self, body: bytes) -> Dict:
        """Helper function to parse and validate incoming message"""
        try:
            message_data = json.loads(body.decode("utf-8"))

            # Convert string UUIDs back to UUID objects for database
            if "id" in message_data:
                message_data["id"] = uuid.UUID(message_data["id"])
            if "litterbox_edge_device_id" in message_data:
                message_data["litterbox_edge_device_id"] = uuid.UUID(
                    message_data["litterbox_edge_device_id"]
                )

            # Convert ISO format datetime strings back to datetime objects
            datetime_fields = ["enter_time", "exit_time", "created_at"]
            for field in datetime_fields:
                if field in message_data and isinstance(message_data[field], str):
                    message_data[field] = datetime.fromisoformat(
                        message_data[field].replace("Z", "+00:00")
                    )

            return message_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse message data: {e}")
            raise

    def process_batch(self):
        """
        Process accumulated batch of messages by inserting batch litterbox usage records into db,
        and
        manually acknowledging messages.
        """
        if not self.message_batch:
            return

        logger.info(f"Processing batch of {len(self.message_batch)} messages")

        try:
            # Prepare data for database insertion
            db_records = []
            delivery_tags = []

            for message_data, delivery_tag in self.message_batch:
                db_records.append(message_data)
                delivery_tags.append(delivery_tag)

            # Insert into database
            self.db_gateway.insert_litterbox_usage_data(db_records)

            # Manually acknowledge all messages in batch
            for delivery_tag in delivery_tags:
                self.channel.basic_ack(delivery_tag=delivery_tag)

            logger.info(
                f"Successfully processed batch of {len(self.message_batch)} messages"
            )

        except Exception as e:
            logger.error(f"Failed to process batch: {e}")

            # Reject all messages in batch (they'll be requeued)
            for _, delivery_tag in self.message_batch:
                self.channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

            logger.info(
                f"Rejected batch of {len(self.message_batch)} messages for reprocessing"
            )

        finally:
            # Clear the batch
            self.message_batch.clear()
            self.last_batch_time = time.time()

    def _should_process_batch(self) -> bool:
        """Helper function to determine if batch should be processed now"""
        batch_full = len(self.message_batch) >= BATCH_SIZE
        batch_timeout = time.time() - self.last_batch_time >= BATCH_TIMEOUT
        return batch_full or (self.message_batch and batch_timeout)

    def store_batch_to_db(self, channel, method, properties, body):
        """Callback function fo handling incoming messages"""
        try:
            # Parse the message
            message_data = self._parse_message(body)

            logger.debug(f"Received message: {message_data.get('id', 'unknown')}")

            # Add to batch
            self.message_batch.append((message_data, method.delivery_tag))

            # Process batch if ready
            if self._should_process_batch():
                self.process_batch()

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Reject the message (will be requeued)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.should_stop = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start_consuming(self):
        """Start consuming messages"""
        logger.info("Starting message consumption...")

        try:
            # Setup consumer
            self.channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=self.store_batch_to_db,
                auto_ack=False,  # Manual acknowledgment for reliability
            )

            logger.info(
                f"Consumer started. Waiting for messages from queue '{QUEUE_NAME}'..."
            )
            logger.info("Press Ctrl+C to stop gracefully")

            # Start consuming with periodic batch checking
            while not self.should_stop:
                # Process any pending messages
                self.connection.process_data_events(time_limit=1)

                # Check if we should process a partial batch due to timeout
                if self._should_process_batch():
                    self.process_batch()

                time.sleep(0.1)  # Small sleep to prevent busy waiting

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.should_stop = True
        except Exception as e:
            logger.error(f"Error during message consumption: {e}")
            raise

    def shutdown(self):
        """Gracefully shutdown the consumer"""
        logger.info("Shutting down consumer...")

        # Process any remaining messages in batch
        if self.message_batch:
            logger.info("Processing remaining messages in batch...")
            self.process_batch()

        # Stop consuming
        if self.channel and not self.channel.is_closed:
            self.channel.stop_consuming()

        # Close RabbitMQ connection
        if self.connection and not self.connection.is_closed:
            self.connection.close()

        # Close database connection
        self.db_gateway.disconnect()

        logger.info("Consumer shutdown completed")

    def run(self):
        """Main run method"""
        try:
            # Setup signal handlers
            self.setup_signal_handlers()

            # Initialize database
            self.setup_database()

            # Initialize RabbitMQ
            self.setup_rabbitmq()

            # Start consuming
            self.start_consuming()

        except Exception as e:
            logger.error(f"Consumer failed: {e}")
            sys.exit(1)
        finally:
            self.shutdown()


def main():
    """Main function to run the consumer"""
    logger.info("Starting Litterbox Data Consumer...")

    consumer = LitterboxConsumer()
    consumer.run()


if __name__ == "__main__":
    main()
