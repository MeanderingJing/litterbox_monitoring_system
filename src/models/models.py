from typing import Any, Dict
import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class UserInfo(Base):
    __tablename__ = "user_info"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=lambda: datetime.now(timezone.utc), nullable=True
    )

    # Relationship with CatInfo
    cats: Mapped[list["CatInfo"]] = relationship(
        "CatInfo", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UserInfo(id={self.id}, username={self.username}, email={self.email})>"


    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert UserInfo instance to dictionary."""
        result = {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_relationships and hasattr(self, 'cats'):
            result["cats"] = [cat.to_dict() for cat in self.cats]
            
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserInfo":
        """Create UserInfo instance from dictionary."""
        # Convert string UUID back to UUID object if present
        if "id" in data and isinstance(data["id"], str):
            data["id"] = uuid.UUID(data["id"])
        
        # Convert ISO datetime strings back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        # Remove relationships from data as they should be handled separately
        clean_data = {k: v for k, v in data.items() if k not in ["cats"]}
        
        return cls(**clean_data)


class CatInfo(Base):
    __tablename__ = "cat_info"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_info.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    breed: Mapped[str] = mapped_column(nullable=True)
    age: Mapped[int] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=lambda: datetime.now(timezone.utc), nullable=True
    )

    # Relationships with UserInfo, LitterboxInfo, and LitterboxUsageData
    owner: Mapped["UserInfo"] = relationship("UserInfo", back_populates="cats")
    litterbox: Mapped["LitterboxInfo"] = relationship(
        "LitterboxInfo", back_populates="cat"
    )

    def __repr__(self) -> str:
        return f"<CatInfo(id={self.id}, owner_id={self.owner_id}, name={self.name}, breed={self.breed}, age={self.age})>"

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert CatInfo instance to dictionary."""
        result = {
            "id": str(self.id),
            "owner_id": str(self.owner_id),
            "name": self.name,
            "breed": self.breed,
            "age": self.age,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_relationships:
            if hasattr(self, 'owner') and self.owner:
                result["owner"] = self.owner.to_dict()
            if hasattr(self, 'litterbox') and self.litterbox:
                result["litterbox"] = self.litterbox.to_dict()
                
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CatInfo":
        """Create CatInfo instance from dictionary."""
        # Convert string UUIDs back to UUID objects
        if "id" in data and isinstance(data["id"], str):
            data["id"] = uuid.UUID(data["id"])
        if "owner_id" in data and isinstance(data["owner_id"], str):
            data["owner_id"] = uuid.UUID(data["owner_id"])
        
        # Convert ISO datetime strings back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        # Remove relationships from data
        clean_data = {k: v for k, v in data.items() if k not in ["owner", "litterbox"]}
        
        return cls(**clean_data)
    
class LitterboxInfo(Base):
    __tablename__ = "litterbox_info"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cat_info.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=lambda: datetime.now(timezone.utc), nullable=True
    )

    # Relationships
    cat: Mapped["CatInfo"] = relationship("CatInfo", back_populates="litterbox")
    litterbox_edge_device: Mapped["LitterboxEdgeDeviceInfo"] = relationship(
        "LitterboxEdgeDeviceInfo", back_populates="litterbox", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<LitterboxInfo(id={self.id}, cat_id={self.cat_id}, name={self.name})>"
        )
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert LitterboxInfo instance to dictionary."""
        result = {
            "id": str(self.id),
            "cat_id": str(self.cat_id),
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_relationships:
            if hasattr(self, 'cat') and self.cat:
                result["cat"] = self.cat.to_dict()
            if hasattr(self, 'litterbox_usage_data'):
                result["litterbox_usage_data"] = [usage.to_dict() for usage in self.litterbox_usage_data]
                
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LitterboxInfo":
        """Create LitterboxInfo instance from dictionary."""
        # Convert string UUIDs back to UUID objects
        if "id" in data and isinstance(data["id"], str):
            data["id"] = uuid.UUID(data["id"])
        if "cat_id" in data and isinstance(data["cat_id"], str):
            data["cat_id"] = uuid.UUID(data["cat_id"])
        
        # Convert ISO datetime strings back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        # Remove relationships from data
        clean_data = {k: v for k, v in data.items() if k not in ["cat", "litterbox_usage_data"]}
        
        return cls(**clean_data)
    
class LitterboxEdgeDeviceInfo(Base):
    __tablename__ = "litterbox_edge_device_info"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    ) # Must be provided by the user
    litterbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("litterbox_info.id"), nullable=False
    )
    device_name: Mapped[str] = mapped_column(nullable=False)
    device_type: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    litterbox: Mapped["LitterboxInfo"] = relationship(
        "LitterboxInfo", back_populates="litterbox_edge_device"
    )
    litterbox_usage_data: Mapped[list["LitterboxUsageData"]] = relationship(
        "LitterboxUsageData", back_populates="litterbox_edge_device", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<LitterboxEdgeDeviceInfo(id={self.id}, litterbox_id={self.litterbox_id},"
            f"device_name={self.device_name}, device_type={self.device_type},"
            f"created_at={self.created_at})>"
        )

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert LitterboxEdgeDeviceInfo instance to dictionary."""
        result = {
            "id": str(self.id),
            "litterbox_id": str(self.litterbox_id),
            "device_name": self.device_name,
            "device_type": self.device_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_relationships:
            if hasattr(self, 'litterbox') and self.litterbox:
                result["litterbox"] = self.litterbox.to_dict()
            if hasattr(self, 'litterbox_usage_data'):
                result["litterbox_usage_data"] = [usage.to_dict() for usage in self.litterbox_usage_data]
                
        return result
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LitterboxEdgeDeviceInfo":
        """Create LitterboxEdgeDeviceInfo instance from dictionary."""

        # Convert string UUIDs back to UUID objects
        if "id" in data and isinstance(data["id"], str):
            data["id"] = uuid.UUID(data["id"])
        if "litterbox_id" in data and isinstance(data["litterbox_id"], str):
            data["litterbox_id"] = uuid.UUID(data["litterbox_id"])
        
        # Convert ISO datetime strings back to datetime objects
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        # Remove relationships from data
        clean_data = {k: v for k, v in data.items() if k not in ["litterbox", "litterbox_usage_data"]}
        
        return cls(**clean_data)


class LitterboxUsageData(Base):
    __tablename__ = "litterbox_usage_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    litterbox_edge_device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("litterbox_edge_device_info.id"), nullable=False
    )
    enter_time: Mapped[datetime] = mapped_column(nullable=False)
    exit_time: Mapped[datetime] = mapped_column(nullable=False)
    weight_enter: Mapped[float] = mapped_column(nullable=False)
    weight_exit: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    

    # Relationship
    litterbox_edge_device: Mapped["LitterboxEdgeDeviceInfo"] = relationship(
        "LitterboxEdgeDeviceInfo", back_populates="litterbox_usage_data"
    )

    def __repr__(self) -> str:
        return (
            f"<LitterboxUsageData(id={self.id}, litterbox_edge_device_id={self.litterbox_edge_device_id},"
            f"enter_time={self.enter_time}, exit_time={self.exit_time},"
            f"weight_enter={self.weight_enter}, weight_exit={self.weight_exit},"
            f"created_at={self.created_at})>"
        )
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert LitterboxUsageData instance to dictionary."""
        result = {
            "id": str(self.id),
            "litterbox_edge_device_id": str(self.litterbox_edge_device_id),
            "enter_time": self.enter_time.isoformat() if self.enter_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "weight_enter": self.weight_enter,
            "weight_exit": self.weight_exit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_relationships:
            if hasattr(self, 'litterbox') and self.litterbox_edge_device:
                result["litterbox_edge_device"] = self.litterbox_edge_device.to_dict()
                
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LitterboxUsageData":
        """Create LitterboxUsageData instance from dictionary."""
        # Convert string UUIDs back to UUID objects
        if "id" in data and isinstance(data["id"], str):
            data["id"] = uuid.UUID(data["id"])
        if "litterbox_edge_device_id" in data and isinstance(data["litterbox_edge_device_id"], str):
            data["litterbox_edge_device_id"] = uuid.UUID(data["litterbox_edge_device_id"])
        
        # Convert ISO datetime strings back to datetime objects
        datetime_fields = ["enter_time", "exit_time", "created_at"]
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Remove relationships from data
        clean_data = {k: v for k, v in data.items() if k not in ["litterbox_edge_device"]}
        
        return cls(**clean_data)

