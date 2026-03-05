"""MongoDB gateway for secondary storage of litterbox usage events."""

from typing import Any, Dict, List

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError
from pymongo.server_api import ServerApi

from config.logging import get_logger

logger = get_logger(__name__)

# Default collection and database names
DEFAULT_DB_NAME = "litterbox"
USAGE_COLLECTION_NAME = "litterbox_usage"


def _usage_record_to_doc(record: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a usage record (with UUID/datetime) to a MongoDB document (JSON-serializable)."""
    doc = dict(record)
    if "id" in doc:
        doc["id"] = str(doc["id"])
    if "litterbox_edge_device_id" in doc:
        doc["litterbox_edge_device_id"] = str(doc["litterbox_edge_device_id"])
    for field in ("enter_time", "exit_time", "created_at"):
        if field in doc and doc[field] is not None:
            val = doc[field]
            if hasattr(val, "isoformat"):
                doc[field] = val.isoformat()
    return doc


class MongoDBGateway:
    """MongoDB client for writing litterbox usage data as a secondary store."""

    def __init__(self, uri: str, db_name: str = DEFAULT_DB_NAME):
        self.uri = uri
        self.db_name = db_name
        self._client: MongoClient | None = None
        self._db: Database | None = None

    def connect(self) -> None:
        """Establish connection to MongoDB (Stable API v1 for Atlas compatibility)."""
        try:
            self._client = MongoClient(self.uri, server_api=ServerApi("1"))
            # Trigger connection
            self._client.admin.command("ping")
            self._db = self._client[self.db_name]
            logger.info("MongoDB connection established.")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed.")

    @property
    def collection(self) -> Collection:
        """Return the litterbox_usage collection. Raises if not connected."""
        if self._db is None:
            raise RuntimeError("MongoDB not connected")
        return self._db[USAGE_COLLECTION_NAME]

    def insert_litterbox_usage_batch(self, records: List[Dict[str, Any]]) -> None:
        """Insert a batch of litterbox usage records. Idempotent by _id (usage id)."""
        if not records:
            return
        docs = [_usage_record_to_doc(r) for r in records]
        # Use usage id as _id for idempotency and deduplication; keep "id" for API consistency
        for doc in docs:
            doc["_id"] = doc.get("id") or doc.get("_id")
        try:
            # ordered=False: one duplicate _id does not abort the rest
            self.collection.insert_many(docs, ordered=False)
            logger.info(f"Inserted {len(docs)} usage records into MongoDB.")
        except BulkWriteError as e:
            # Duplicate key (11000) is acceptable for secondary store / replay
            if e.details and e.details.get("writeErrors"):
                non_dup = [
                    err for err in e.details["writeErrors"] if err.get("code") != 11000
                ]
                if non_dup:
                    logger.error(f"MongoDB batch write errors: {non_dup}")
                    raise
            inserted = e.details.get("nInserted", 0) if e.details else 0
            logger.info(f"MongoDB: {inserted} inserted, some duplicates skipped.")
        except Exception as e:
            logger.error(f"MongoDB batch insert failed: {e}")
            raise
