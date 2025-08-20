"""
Main data collector and synchronizer service.
It fetches data from the Litterbox API and synchronizes it with the database.
"""

from typing import Any, Dict, List, Optional

from config.logging import get_logger
from data_persister.db_writer import get_litterbox_usage_data
from database.postgresql_gateway import PostgreSQLGateway

logger = get_logger(__name__)
DATABASE_URL = (
    "postgresql://example_user:example_password@192.168.40.159:5435/example_db"
)


class DataSynchronizer:
    """Service to synchronize data between the Litterbox API and the database."""

    def __init__(self, db_url: str):
        self.gateway = PostgreSQLGateway(db_url)

    def synchronize(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> None:
        """Fetch data from the Litterbox API and insert it into the database."""
        try:
            self.gateway.connect()
            self.gateway.create_tables()

            # Fetch data from the Litterbox API
            data: List[Dict[str, Any]] = get_litterbox_usage_data(
                start_date=start_date, end_date=end_date
            )
            if not data:
                logger.info("No new data to insert.")
                return

            # Insert data into the database
            self.gateway.insert_litterbox_usage_data(data)
            logger.info(f"Inserted {len(data)} records into the database.")

        except Exception as e:
            logger.error(f"Data synchronization failed: {e}")
        finally:
            self.gateway.disconnect()


data_synchronizer = DataSynchronizer(DATABASE_URL)
data_synchronizer.synchronize()  # Example usage, can be called with specific dates
