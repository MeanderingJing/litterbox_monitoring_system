import uuid
import random
import schedule
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import json
import logging
import pika

from models.models import LitterboxUsageData
from rabbitmq_support.rabbitmq_gateway import (
    CONNECTION_PARAMS,
    EXCHANGE_NAME,
    EXCHANGE_TYPE,
    get_rabbitmq_connection,
)
from config.logging import get_logger

logger = get_logger(__name__)

# Optionally reduce Pika log verbosity
get_logger("pika").setLevel(logging.WARNING)

# Pre-defined edge device ID
EDGE_DEVICE_ID = uuid.UUID("12345678-1234-5678-9012-123456789abc")

EMPTY_LITTERBOX_WEIGHT = 5  # lbs


class LitterboxSimulator:
    def __init__(self):
        # Set start date to 7 days ago from today
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.current_week_start = today - timedelta(days=7)

        logger.info(f"Simulator initialized with edge device ID: {EDGE_DEVICE_ID}")
        logger.info(f"Initial week start (7 days ago): {self.current_week_start}")
        logger.info(f"Initial week end: {self.current_week_start + timedelta(days=6)}")

        # Initialize RabbitMQ connection parameters
        self.connection_params = CONNECTION_PARAMS

    def publish_to_rabbitmq(self, channel, data: Dict):
        """Publish a single message to RabbitMQ"""
        try:
            # Declare exchange (idempotent operation)
            channel.exchange_declare(
                exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE, durable=True
            )
            # Convert datetime objects to ISO format strings for JSON serialization
            serializable_data = self.prepare_data_for_serialization(data)
            message_body = json.dumps(serializable_data, default=str)
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key="",  # routing_key is ignored for 'fanout'
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json",
                    timestamp=int(time.time()),
                    message_id=str(data.get("id", uuid.uuid4())),
                    headers={
                        "edge_device_id": str(data.get("litterbox_edge_device_id")),
                        "data_type": "litterbox_usage",
                    },
                ),
            )
            logger.debug(f"Published message for usage ID: {data.get('id')}")

        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {e}")
            raise

    def prepare_data_for_serialization(self, data: Dict) -> Dict:
        """Convert data types for JSON serialization"""
        serializable_data = data.copy()

        # Convert UUIDs to strings
        if "id" in serializable_data:
            serializable_data["id"] = str(serializable_data["id"])
        if "litterbox_edge_device_id" in serializable_data:
            serializable_data["litterbox_edge_device_id"] = str(
                serializable_data["litterbox_edge_device_id"]
            )

        # Convert datetime objects to ISO format
        for key, value in serializable_data.items():
            if isinstance(value, datetime):
                serializable_data[key] = value.isoformat()

        return serializable_data

    def generate_realistic_usage_times(self, base_date: datetime) -> List[datetime]:
        """Generate realistic litterbox usage times for a day"""
        usage_times = []

        # Cats typically use litterbox 2-4 times per day
        daily_uses = random.randint(2, 4)

        # Define time periods with different probabilities
        # Morning (6-10): 30% chance
        # Midday (10-16): 20% chance
        # Evening (16-20): 35% chance
        # Night (20-6): 15% chance

        time_periods = [
            (6, 10, 0.30),  # Morning
            (10, 16, 0.20),  # Midday
            (16, 20, 0.35),  # Evening
            (20, 24, 0.10),  # Night early
            (0, 6, 0.05),  # Night late
        ]

        for _ in range(daily_uses):
            # Choose time period based on probability
            period_choice = random.random()
            cumulative_prob = 0

            for start_hour, end_hour, prob in time_periods:
                cumulative_prob += prob
                if period_choice <= cumulative_prob:
                    # Generate time within this period
                    hour = random.randint(start_hour, end_hour - 1)
                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)

                    usage_time = base_date.replace(
                        hour=hour, minute=minute, second=second
                    )
                    usage_times.append(usage_time)
                    break

        return sorted(usage_times)

    def generate_weight_data(self) -> tuple[float, float]:
        """Generate realistic enter and exit weights measured by litterbox sensor (in pounds)"""
        # Litterbox base components (in pounds):
        # - Empty litterbox: 4.4-8.8 lbs (2-4 kg converted)
        # - Litter (clean): 17.6-33.1 lbs (8-15 kg converted)
        # - Cat weight: 6.6-13.2 lbs (3-6 kg converted)

        empty_litterbox_weight = EMPTY_LITTERBOX_WEIGHT  # lbs
        litter_weight = random.uniform(17.6, 33.1)  # lbs
        cat_weight = random.uniform(6.6, 13.2)  # lbs

        # Weight when cat enters = litterbox + litter + cat
        weight_enter = empty_litterbox_weight + litter_weight + cat_weight

        # Weight when cat exits = litterbox + litter + waste left behind
        # Typical waste weights (in pounds):
        # - Urine: 0.044-0.11 lbs (20-50g converted)
        # - Feces: 0.022-0.066 lbs (10-30g converted)
        # - Most visits are just urine (~70%), some are both (~25%), few are just feces (~5%)

        visit_type = random.random()
        if visit_type < 0.70:  # 70% urine only
            waste_weight = random.uniform(
                0.011, 0.033
            )  # 5-15g converted to lbs (mostly absorbed)
        elif visit_type < 0.95:  # 25% both urine and feces
            urine_weight = random.uniform(0.011, 0.033)  # 5-15g converted to lbs
            feces_weight = random.uniform(0.022, 0.066)  # 10-30g converted to lbs
            waste_weight = urine_weight + feces_weight
        else:  # 5% feces only
            waste_weight = random.uniform(0.022, 0.066)  # 10-30g converted to lbs

        # Weight when cat exits = litterbox + litter + waste (no cat)
        weight_exit = empty_litterbox_weight + litter_weight + waste_weight

        # Round to realistic sensor precision (typically 0.1lb resolution)
        weight_enter = round(weight_enter, 1)
        weight_exit = round(weight_exit, 1)

        return weight_enter, weight_exit

    def generate_session_duration(self) -> timedelta:
        """Generate realistic session duration"""
        # Typical litterbox session: 30 seconds to 5 minutes
        # Most sessions: 1-3 minutes
        duration_seconds = random.normalvariate(120, 60)  # Mean 2 minutes, std 1 minute
        duration_seconds = max(
            30, min(300, duration_seconds)
        )  # Clamp between 30s and 5 minutes
        return timedelta(seconds=int(duration_seconds))

    def generate_week_data(self, week_start: datetime) -> List[LitterboxUsageData]:
        """Generate a full week's worth of litterbox usage data"""
        usage_data = []

        logger.info(f"Generating data for week starting: {week_start}")

        for day_offset in range(7):
            current_day = week_start + timedelta(days=day_offset)
            daily_usage_times = self.generate_realistic_usage_times(current_day)

            for enter_time in daily_usage_times:
                # Generate session duration and exit time
                session_duration = self.generate_session_duration()
                exit_time = enter_time + session_duration

                # Generate weights
                weight_enter, weight_exit = self.generate_weight_data()

                # Create usage data record
                usage_record = {
                    "id": uuid.uuid4(),
                    "litterbox_edge_device_id": EDGE_DEVICE_ID,
                    "enter_time": enter_time,
                    "exit_time": exit_time,
                    "weight_enter": weight_enter,
                    "weight_exit": weight_exit,
                    "created_at": datetime.now(timezone.utc),
                }

                usage_data.append(usage_record)

        logger.info(f"Generated {len(usage_data)} usage records for the past week")
        return usage_data

    def save_data_to_file(self, data: List[Dict], filename: str = None):
        """Save generated data to JSON file for inspection/testing"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"litterbox_data_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Data saved to {filename}")

    def process_data(self, data: List[Dict]):
        """
        Process the generated data by sending each record to RabbitMQ. If RabbitMQ is unavailable,
        fall back to saving the data to a local file.
        """
        logger.info(f"Processing {len(data)} usage records...")

        successful_publishes = 0
        failed_publishes = 0

        # Sending to a message queue
        try:
            # Test connection first
            with get_rabbitmq_connection() as channel:
                logger.info("Successfully connected to RabbitMQ")

                # Process each record
                for i, record in enumerate(data, 1):
                    try:
                        self.publish_to_rabbitmq(channel, record)
                        successful_publishes += 1

                        # Log progress for large batches
                        if i % 10 == 0 or i == len(data):
                            logger.info(
                                f"Published {i}/{len(data)} messages to RabbitMQ"
                            )

                    except Exception as e:
                        failed_publishes += 1
                        logger.error(
                            f"Failed to publish record {record.get('id', 'unknown')}: {e}"
                        )

                        # Continue processing other records even if one fails
                        continue

            # Summary
            logger.info(
                f"Data processing completed: {successful_publishes} successful, {failed_publishes} failed"
            )

            # Also save to file as backup
            if successful_publishes > 0:
                self.save_data_to_file(
                    data,
                    f"backup_litterbox_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                )

        except pika.exceptions.AMQPConnectionError:
            logger.error(
                "Could not connect to RabbitMQ. Falling back to file storage only."
            )
            self.save_data_to_file(data)
        except Exception as e:
            logger.error(f"Unexpected error during data processing: {e}")
            # Fallback to file storage
            self.save_data_to_file(data)

    def generate_initial_week(self):
        """Generate initial week's worth of data and send to RabbitMQ."""
        logger.info("Generating initial week's data...")
        data = self.generate_week_data(self.current_week_start)
        self.process_data(data)

    def _check_and_generate_next_batch(self):
        """Check if it's time to generate the next 7-day batch"""
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Calculate when the next batch should be generated
        # (7 days after the current week start)
        next_batch_date = self.current_week_start + timedelta(days=7)

        if today >= next_batch_date:
            self.generate_next_week()

    def generate_next_week(self):
        """Generate next week's data (scheduled task) and send to RabbitMQ."""
        logger.info("Generating next week's data...")
        # Move to the next 7-day period
        self.current_week_start += timedelta(days=7)
        data = self.generate_week_data(self.current_week_start)
        self.process_data(data)

    def start_simulator(self):
        """Start the simulator with initial data generation and scheduling"""
        logger.info("Starting Litterbox Edge Device Simulator...")

        # Generate initial week's data
        self.generate_initial_week()

        # Schedule data generation every 7 days
        # Run daily at 00:01 and check if it's time for next batch
        schedule.every().day.at("00:01").do(self._check_and_generate_next_batch)

        logger.info(
            "Simulator started. Scheduled to generate new 7-day batch every 7 days at 00:01"
        )
        logger.info("Press Ctrl+C to stop the simulator")

        # Keep the simulator running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Simulator stopped by user")


def main():
    """Main function to run the simulator"""
    simulator = LitterboxSimulator()
    # data = simulator.generate_week_data(simulator.current_week_start)
    # simulator.process_data(data)
    simulator.start_simulator()


if __name__ == "__main__":
    main()
