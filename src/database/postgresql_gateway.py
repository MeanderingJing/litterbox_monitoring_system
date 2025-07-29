"""SQLAlchemy PostgreSQL implmentation of database gateway."""

from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.logging import get_logger
from models.models import Base, LitterboxUsageData

from .gateway import DatabaseGateway


class PostgreSQLGateway(DatabaseGateway):
    """PostgreSQL implementation of the DatabaseGateway interface."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)  # thread safe

        # Set up logging
        self.logger = get_logger(__name__)

    def connect(self) -> None:
        """Establish and test a connection to the database."""
        try:
            # Trigger actual connection
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            self.logger.info("✅ Successfully connected to the database.")
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            raise

    def disconnect(self) -> None:
        """Dispose of the database engine connection pool"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.logger.info("✅ Database connection closed.")

    def create_tables(self) -> None:
        """Create necessary tables in the database."""
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("✅ Tables created successfully.")
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")

    def insert_litterbox_usage_data(self, data: List[Dict]) -> None:
        """Insert litterbox usage data into the database."""
        self.logger.info(f"Attempting to insert {len(data)} records into the database.")
        try:
            with self.SessionLocal() as session:
                inserted_count = 0

                for record in data:
                    # check if record already exists
                    existing_record = (
                        session.query(LitterboxUsageData)
                        .filter_by(id=record["id"])
                        .first()
                    )
                    if existing_record:
                        self.logger.error(
                            f"Record with ID {record['id']} already exists. Investigate this issue."
                        )
                        raise ValueError(
                            f"Record with ID {record['id']} already exists."
                        )
                    new_record = LitterboxUsageData.from_dict(record)
                    session.add(new_record)
                    inserted_count += 1
                session.commit()
                self.logger.info(
                    f"✅ Successfully inserted {inserted_count} records into the database."
                )

        except Exception as e:
            self.logger.error(f"❌ Error inserting data: {e}")
            raise

    def get_litterbox_usage_data(self) -> List[Dict[str, Any]]:
        """Retrieve litterbox usage data from the database."""
        try:
            with self.SessionLocal() as session:
                records = session.query(LitterboxUsageData).all()
                return [record.__dict__ for record in records]
        except Exception as e:
            self.logger.error(f"Error retrieving litterbox usage data: {e}")
            return []

    def get_latest_litterbox_usage_timestamp(self) -> Optional[str]:
        """Get the latest usage timestamp from the database."""
        try:
            with self.SessionLocal() as session:
                latest_record = (
                    session.query(LitterboxUsageData)
                    .order_by(LitterboxUsageData.timestamp.desc())
                    .first()
                )

                if latest_record:
                    self.logger.info(
                        f"Latest usage timestamp: {latest_record.timestamp}"
                    )
                    return latest_record.timestamp.isoformat()
                else:
                    self.logger.info("No usage data found in the database.")
                    return None
        except Exception as e:
            self.logger.error(f"❌ Error retrieving latest usage timestamp: {e}")
            return None
