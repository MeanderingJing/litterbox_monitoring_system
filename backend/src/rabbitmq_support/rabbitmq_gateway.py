import os
import pika
from contextlib import contextmanager

from config.logging import get_logger

logger = get_logger(__name__)

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "192.168.40.159")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")
EXCHANGE_NAME = "litterbox_events"
EXCHANGE_TYPE = "fanout"
ROUTING_KEY = "litterbox.usage"
QUEUE_NAME = "litterbox_usage_queue"

CONNECTION_PARAMS = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    virtual_host=RABBITMQ_VHOST,
    credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD),
    heartbeat=600,
    blocked_connection_timeout=300,
)


@contextmanager
def get_rabbitmq_connection():
    """Context manager for RabbitMQ conenctions"""
    connection = None
    try:
        connection = pika.BlockingConnection(CONNECTION_PARAMS)
        channel = connection.channel()

        yield channel

    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise
    except Exception as e:
        logger.error(f"RabbitMQ operation failed: {e}")
        raise
    finally:
        if connection and not connection.is_closed:
            connection.close()
