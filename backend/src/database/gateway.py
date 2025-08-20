"""Abstract database gateway interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class DatabaseGateway(ABC):
    """Abstract base class for database gateways."""

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the database."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to the database."""

    @abstractmethod
    def create_tables(self) -> None:
        """Create necessary tables in the database."""

    @abstractmethod
    def insert_litterbox_usage_data(self) -> None:
        """Insert litterbox usage data into the database."""

    @abstractmethod
    def get_litterbox_usage_data(self) -> List[Dict[str, Any]]:
        """Retrieve litterbox usage data from the database."""

    @abstractmethod
    def get_latest_litterbox_usage_timestamp(self) -> Optional[str]:
        """Get the latest usage timestamp from the database."""

    # @abstractmethod
    # def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    #     """Execute a query and return the results."""
    #     pass

    # @abstractmethod
    # def commit(self) -> None:
    #     """Commit the current transaction."""
    #     pass

    # @abstractmethod
    # def rollback(self) -> None:
    #     """Rollback the current transaction."""
    #     pass
