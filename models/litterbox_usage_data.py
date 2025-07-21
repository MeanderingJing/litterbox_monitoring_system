from typing import Optional, List
from datetime import datetime
import uuid 
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class LitterboxUsageData(Base):
    __tablename__ = 'litterbox_usage_data'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    cat_id = Mapped[int] = mapped_column(nullable=False)
    litterbox_id: Mapped[int] = mapped_column(nullable=False)
    enter_time: Mapped[datetime] = mapped_column(nullable=False)
    exit_time: Mapped[datetime] = mapped_column(nullable=False)
    weight_enter: Mapped[float] = mapped_column(nullable=False)
    weight_exit: Mapped[float] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)

    # Define index for cat_id and litterbox_id for faster queries
    __table_args__ = (
        Index('idx_cat_id', 'cat_id'),
        Index('idx_litterbox_usage_timestamp', 'timestamp'),
    )

    def __repr__(self) -> str:
        return (f"<LitterboxUsageData(id={self.id}, cat_id={self.cat_id}, "
                f"litterbox_id={self.litterbox_id}, enter_time={self.enter_time}, "
                f"exit_time={self.exit_time}, weight_enter={self.weight_enter}, "
                f"weight_exit={self.weight_exit}, timestamp={self.timestamp})>")
    

    @classmethod
    def from_dict(cls, data: dict) -> 'LitterboxUsageData':
        """Create an instance from a dictionary."""
        return cls(
            id=data.get('id', uuid.uuid4()),
            cat_id=data['cat_id'],
            litterbox_id=data['litterbox_id'],
            enter_time=data['enter_time'],
            exit_time=data['exit_time'],
            weight_enter=data['weight_enter'],
            weight_exit=data['weight_exit'],
            timestamp=data['timestamp']
        )
    
    def to_dict(self) -> dict:
        """Convert the instance to a dictionary."""
        return {
            'id': str(self.id),
            'cat_id': self.cat_id,
            'litterbox_id': self.litterbox_id,
            'enter_time': self.enter_time.isoformat(),
            'exit_time': self.exit_time.isoformat(),
            'weight_enter': self.weight_enter,
            'weight_exit': self.weight_exit,
            'timestamp': self.timestamp.isoformat()
        }
    
    

