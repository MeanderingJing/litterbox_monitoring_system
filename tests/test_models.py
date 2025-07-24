import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.litterbox_usage_data import Base, LitterboxUsageData


@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a database session for testing."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "id": uuid.uuid4(),
        "cat_id": 1,
        "litterbox_id": 2,
        "enter_time": datetime(2024, 1, 15, 10, 30, 0),
        "exit_time": datetime(2024, 1, 15, 10, 35, 0),
        "weight_enter": 4.5,
        "weight_exit": 4.3,
        "timestamp": datetime(2024, 1, 15, 10, 35, 30),
    }


@pytest.fixture
def sample_dict_data():
    """Sample dictionary data for testing from_dict method."""
    return {
        "cat_id": 3,
        "litterbox_id": 1,
        "enter_time": datetime(2024, 2, 20, 14, 15, 0),
        "exit_time": datetime(2024, 2, 20, 14, 18, 0),
        "weight_enter": 3.8,
        "weight_exit": 3.6,
        "timestamp": datetime(2024, 2, 20, 14, 18, 30),
    }


class TestLitterboxUsageDataModel:
    """Test cases for LitterboxUsageData model."""

    def test_create_instance_with_all_fields(self, sample_data: dict):
        """Test creating an instance with all required fields."""
        usage = LitterboxUsageData(**sample_data)

        assert usage.id == sample_data["id"]
        assert usage.cat_id == sample_data["cat_id"]
        assert usage.litterbox_id == sample_data["litterbox_id"]
        assert usage.enter_time == sample_data["enter_time"]
        assert usage.exit_time == sample_data["exit_time"]
        assert usage.weight_enter == sample_data["weight_enter"]
        assert usage.weight_exit == sample_data["weight_exit"]
        assert usage.timestamp == sample_data["timestamp"]

    def test_repr_method(self, sample_data):
        """Test the __repr__ method."""
        usage = LitterboxUsageData(**sample_data)
        repr_str = repr(usage)

        assert f"id={sample_data['id']}" in repr_str
        assert f"cat_id={sample_data['cat_id']}" in repr_str
        assert f"litterbox_id={sample_data['litterbox_id']}" in repr_str
        assert "LitterboxUsageData" in repr_str

    def test_from_dict_with_id(self, sample_dict_data: dict):
        """Test from_dict class method with provided ID."""
        test_id = uuid.uuid4()
        sample_dict_data["id"] = test_id

        usage = LitterboxUsageData.from_dict(sample_dict_data)

        assert usage.id == test_id
        assert usage.cat_id == sample_dict_data["cat_id"]
        assert usage.litterbox_id == sample_dict_data["litterbox_id"]
        assert usage.enter_time == sample_dict_data["enter_time"]
        assert usage.exit_time == sample_dict_data["exit_time"]
        assert usage.weight_enter == sample_dict_data["weight_enter"]
        assert usage.weight_exit == sample_dict_data["weight_exit"]
        assert usage.timestamp == sample_dict_data["timestamp"]

    def test_from_dict_without_id_generates_uuid(self, sample_dict_data):
        """Test from_dict class method without ID. uuid will be generated."""
        usage = LitterboxUsageData.from_dict(sample_dict_data)

        assert isinstance(usage.id, uuid.UUID)
        assert usage.cat_id == sample_dict_data["cat_id"]

    def test_to_dict_method(self, sample_data):
        """Test to_dict method."""
        usage = LitterboxUsageData(**sample_data)
        result_dict = usage.to_dict()

        assert result_dict["id"] == str(sample_data["id"])
        assert result_dict["cat_id"] == sample_data["cat_id"]
        assert result_dict["litterbox_id"] == sample_data["litterbox_id"]
        assert result_dict["enter_time"] == sample_data["enter_time"].isoformat()
        assert result_dict["exit_time"] == sample_data["exit_time"].isoformat()
        assert result_dict["weight_enter"] == sample_data["weight_enter"]
        assert result_dict["weight_exit"] == sample_data["weight_exit"]
        assert result_dict["timestamp"] == sample_data["timestamp"].isoformat()

    def test_to_dict_datetime_serialization(self):
        """Test that to_dict properly serializes datetime objects."""
        enter_time = datetime(2024, 3, 15, 9, 30, 45)
        usage = LitterboxUsageData(
            cat_id=1,
            litterbox_id=1,
            enter_time=enter_time,
            exit_time=datetime(2024, 3, 15, 9, 35, 45),
            weight_enter=4.0,
            weight_exit=3.8,
            timestamp=datetime(2024, 3, 15, 9, 36, 0),
        )

        result = usage.to_dict()
        assert result["enter_time"] == "2024-03-15T09:30:45"

    def test_from_dict_to_dict_roundtrip(self, sample_dict_data):
        """Test roundtrip conversion from dict to model and back."""
        # Add ID to ensure consistent roundtrip
        test_id = uuid.uuid4()
        sample_dict_data["id"] = test_id

        usage = LitterboxUsageData.from_dict(sample_dict_data)
        result_dict = usage.to_dict()

        assert result_dict["id"] == str(test_id)
        assert result_dict["cat_id"] == sample_dict_data["cat_id"]
        # Note: datetime objects are serialized to ISO format strings
        assert result_dict["enter_time"] == sample_dict_data["enter_time"].isoformat()


# class TestLitterboxUsageDataDatabase:
#     """Test database operations for LitterboxUsageData model."""

#     def test_save_to_database(self, session, sample_data):
#         """Test saving a LitterboxUsageData instance to the database."""
#         usage = LitterboxUsageData(**sample_data)
#         session.add(usage)
#         session.commit()

#         # Query back from database
#         saved_usage = session.query(LitterboxUsageData).filter_by(id=usage.id).first()
#         assert saved_usage is not None
#         assert saved_usage.cat_id == sample_data["cat_id"]
#         assert saved_usage.weight_enter == sample_data["weight_enter"]

#     def test_query_by_cat_id(self, session, sample_data):
#         """Test querying by cat_id (which has an index)."""
#         usage1 = LitterboxUsageData(**sample_data)

#         # Create second usage data with different cat_id
#         sample_data2 = sample_data.copy()
#         sample_data2["id"] = uuid.uuid4()
#         sample_data2["cat_id"] = 2
#         usage2 = LitterboxUsageData(**sample_data2)

#         session.add_all([usage1, usage2])
#         session.commit()

#         # Query by cat_id
#         cat_1_usages = session.query(LitterboxUsageData).filter_by(cat_id=1).all()
#         assert len(cat_1_usages) == 1
#         assert cat_1_usages[0].cat_id == 1

#     def test_query_by_timestamp_index(self, session):
#         """Test querying by timestamp (which has an index)."""
#         base_time = datetime(2024, 1, 15, 10, 0, 0)

#         # Create multiple usage records with different timestamps
#         usages = []
#         for i in range(3):
#             usage = LitterboxUsageData(
#                 cat_id=1,
#                 litterbox_id=1,
#                 enter_time=base_time,
#                 exit_time=base_time,
#                 weight_enter=4.0,
#                 weight_exit=3.8,
#                 timestamp=datetime(2024, 1, 15, 10, i * 10, 0),  # Different timestamps
#             )
#             usages.append(usage)

#         session.add_all(usages)
#         session.commit()

#         # Query by timestamp range
#         start_time = datetime(2024, 1, 15, 10, 5, 0)
#         end_time = datetime(2024, 1, 15, 10, 25, 0)

#         filtered_usages = (
#             session.query(LitterboxUsageData)
#             .filter(LitterboxUsageData.timestamp.between(start_time, end_time))
#             .all()
#         )

#         assert len(filtered_usages) == 2

#     def test_update_record(self, session, sample_data):
#         """Test updating a record in the database."""
#         usage = LitterboxUsageData(**sample_data)
#         session.add(usage)
#         session.commit()

#         # Update the record
#         usage.weight_exit = 4.0
#         session.commit()

#         # Verify update
#         updated_usage = session.query(LitterboxUsageData).filter_by(id=usage.id).first()
#         assert updated_usage.weight_exit == 4.0

#     def test_delete_record(self, session, sample_data):
#         """Test deleting a record from the database."""
#         usage = LitterboxUsageData(**sample_data)
#         session.add(usage)
#         session.commit()

#         # Delete the record
#         session.delete(usage)
#         session.commit()

#         # Verify deletion
#         deleted_usage = session.query(LitterboxUsageData).filter_by(id=usage.id).first()
#         assert deleted_usage is None

#     def test_multiple_records_same_cat(self, session):
#         """Test storing multiple records for the same cat."""
#         cat_id = 1
#         records = []

#         for i in range(3):
#             usage = LitterboxUsageData(
#                 cat_id=cat_id,
#                 litterbox_id=i + 1,
#                 enter_time=datetime(2024, 1, 15, 10, i * 10, 0),
#                 exit_time=datetime(2024, 1, 15, 10, i * 10 + 5, 0),
#                 weight_enter=4.0 + i * 0.1,
#                 weight_exit=3.8 + i * 0.1,
#                 timestamp=datetime(2024, 1, 15, 10, i * 10 + 6, 0),
#             )
#             records.append(usage)

#         session.add_all(records)
#         session.commit()

#         # Verify all records saved
#         saved_records = session.query(LitterboxUsageData).filter_by(cat_id=cat_id).all()
#         assert len(saved_records) == 3

#     def test_table_name(self):
#         """Test that the table name is set correctly."""
#         assert LitterboxUsageData.__tablename__ == "litterbox_usage_data"

#     def test_primary_key_constraint(self, session):
#         """Test primary key constraint."""
#         test_id = uuid.uuid4()
#         usage1 = LitterboxUsageData(
#             id=test_id,
#             cat_id=1,
#             litterbox_id=1,
#             enter_time=datetime.now(),
#             exit_time=datetime.now(),
#             weight_enter=4.0,
#             weight_exit=3.8,
#             timestamp=datetime.now(),
#         )

#         usage2 = LitterboxUsageData(
#             id=test_id,  # Same ID
#             cat_id=2,
#             litterbox_id=2,
#             enter_time=datetime.now(),
#             exit_time=datetime.now(),
#             weight_enter=4.0,
#             weight_exit=3.8,
#             timestamp=datetime.now(),
#         )

#         session.add(usage1)
#         session.commit()

#         session.add(usage2)
#         with pytest.raises(IntegrityError):
#             session.commit()


# class TestLitterboxUsageDataValidation:
#     """Test validation and edge cases for LitterboxUsageData model."""

#     def test_missing_required_fields(self):
#         """Test that missing required fields raise appropriate errors."""
#         with pytest.raises(TypeError):
#             LitterboxUsageData()  # Missing required fields

#     def test_weight_calculations(self, sample_data):
#         """Test weight difference calculations."""
#         usage = LitterboxUsageData(**sample_data)
#         weight_diff = usage.weight_enter - usage.weight_exit
#         assert weight_diff == 0.2  # 4.5 - 4.3

#     def test_duration_calculation(self, sample_data):
#         """Test duration calculation between enter and exit times."""
#         usage = LitterboxUsageData(**sample_data)
#         duration = usage.exit_time - usage.enter_time
#         assert duration.total_seconds() == 300  # 5 minutes

#     def test_negative_weights(self):
#         """Test handling of negative weights."""
#         usage = LitterboxUsageData(
#             cat_id=1,
#             litterbox_id=1,
#             enter_time=datetime.now(),
#             exit_time=datetime.now(),
#             weight_enter=-1.0,  # Negative weight
#             weight_exit=3.8,
#             timestamp=datetime.now(),
#         )
#         # Model should accept negative weights (validation can be added at application level)
#         assert usage.weight_enter == -1.0

#     def test_zero_weights(self):
#         """Test handling of zero weights."""
#         usage = LitterboxUsageData(
#             cat_id=1,
#             litterbox_id=1,
#             enter_time=datetime.now(),
#             exit_time=datetime.now(),
#             weight_enter=0.0,
#             weight_exit=0.0,
#             timestamp=datetime.now(),
#         )
#         assert usage.weight_enter == 0.0
#         assert usage.weight_exit == 0.0

#     def test_exit_before_enter_time(self):
#         """Test when exit time is before enter time."""
#         enter_time = datetime(2024, 1, 15, 10, 30, 0)
#         exit_time = datetime(2024, 1, 15, 10, 25, 0)  # 5 minutes earlier

#         usage = LitterboxUsageData(
#             cat_id=1,
#             litterbox_id=1,
#             enter_time=enter_time,
#             exit_time=exit_time,
#             weight_enter=4.0,
#             weight_exit=3.8,
#             timestamp=datetime.now(),
#         )

#         # Model accepts this (validation can be added at application level)
#         assert usage.enter_time > usage.exit_time
