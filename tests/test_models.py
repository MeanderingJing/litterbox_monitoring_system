import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Import your models (adjust the import path as needed)
from models.models import (
    Base,
    UserInfo,
    CatInfo,
    LitterboxInfo,
    LitterboxEdgeDeviceInfo,
    LitterboxUsageData,
)


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return UserInfo(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password_123",
    )


@pytest.fixture
def sample_cat(sample_user):
    """Create a sample cat for testing."""
    return CatInfo(owner_id=sample_user.id, name="Fluffy", breed="Persian", age=3)


@pytest.fixture
def sample_litterbox(sample_cat):
    """Create a sample litterbox for testing."""
    return LitterboxInfo(cat_id=sample_cat.id, name="Main Litterbox")


@pytest.fixture
def sample_edge_device(sample_litterbox):
    """Create a sample edge device for testing."""
    return LitterboxEdgeDeviceInfo(
        id=uuid.uuid4(),  # Must be provided by user
        litterbox_id=sample_litterbox.id,
        device_name="Smart Litterbox Sensor",
        device_type="weight_sensor",
    )


@pytest.fixture
def sample_usage_data(sample_edge_device):
    """Create sample usage data for testing."""
    enter_time = datetime.now(timezone.utc)
    exit_time = datetime.now(timezone.utc)
    return LitterboxUsageData(
        litterbox_edge_device_id=sample_edge_device.id,
        enter_time=enter_time,
        exit_time=exit_time,
        weight_enter=5.2,
        weight_exit=5.0,
    )


class TestUserInfo:
    """Tests for UserInfo model."""

    def test_user_creation(self, db_session, sample_user):
        """Test creating a user."""
        db_session.add(sample_user)
        db_session.commit()

        assert sample_user.id is not None
        assert isinstance(sample_user.id, uuid.UUID)
        assert sample_user.username == "testuser"
        assert sample_user.email == "test@example.com"
        assert sample_user.created_at is not None
        assert sample_user.updated_at is None

    def test_user_unique_constraints(self, db_session):
        """Test that username and email must be unique."""
        user1 = UserInfo(
            username="user1", email="user1@example.com", password_hash="hash1"
        )
        user2 = UserInfo(
            username="user1", email="user2@example.com", password_hash="hash2"
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_repr(self, sample_user):
        """Test user string representation."""
        repr_str = repr(sample_user)
        assert "UserInfo" in repr_str
        assert sample_user.username in repr_str
        assert sample_user.email in repr_str

    def test_user_to_dict(self, sample_user):
        """Test converting user to dictionary."""
        user_dict = sample_user.to_dict()

        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["password_hash"] == "hashed_password_123"
        assert isinstance(user_dict["id"], str)
        assert "cats" not in user_dict

    def test_user_to_dict_with_relationships(self, db_session, sample_user, sample_cat):
        """Test converting user to dictionary with relationships."""
        sample_cat.owner = sample_user
        db_session.add(sample_user)
        db_session.add(sample_cat)
        db_session.commit()

        user_dict = sample_user.to_dict(include_relationships=True)

        assert "cats" in user_dict
        assert len(user_dict["cats"]) == 1
        assert user_dict["cats"][0]["name"] == "Fluffy"

    def test_user_from_dict(self):
        """Test creating user from dictionary."""
        user_id = uuid.uuid4()
        created_at = datetime.now(timezone.utc)

        data = {
            "id": str(user_id),
            "username": "dictuser",
            "email": "dict@example.com",
            "password_hash": "dict_hash",
            "created_at": created_at.isoformat(),
            "cats": [],  # This should be filtered out
        }

        user = UserInfo.from_dict(data)

        assert user.id == user_id
        assert user.username == "dictuser"
        assert user.email == "dict@example.com"
        assert user.created_at == created_at


class TestCatInfo:
    """Tests for CatInfo model."""

    def test_cat_creation(self, db_session, sample_user, sample_cat):
        """Test creating a cat."""
        db_session.add(sample_user)
        db_session.commit()
        # Make sure sample_cat.owner_id is set properly
        sample_cat.owner_id = sample_user.id
        db_session.add(sample_cat)
        db_session.commit()

        assert sample_cat.id is not None
        assert isinstance(sample_cat.id, uuid.UUID)
        assert sample_cat.name == "Fluffy"
        assert sample_cat.breed == "Persian"
        assert sample_cat.age == 3
        assert sample_cat.owner_id == sample_user.id

    def test_cat_owner_relationship(self, db_session, sample_user, sample_cat):
        """Test cat-owner relationship."""
        sample_cat.owner = sample_user
        db_session.add(sample_user)
        db_session.add(sample_cat)
        db_session.commit()

        assert sample_cat.owner == sample_user
        assert sample_cat in sample_user.cats

    def test_cat_repr(self, sample_cat):
        """Test cat string representation."""
        repr_str = repr(sample_cat)
        assert "CatInfo" in repr_str
        assert sample_cat.name in repr_str
        assert sample_cat.breed in repr_str

    def test_cat_to_dict(self, sample_cat):
        """Test converting cat to dictionary."""
        cat_dict = sample_cat.to_dict()

        assert cat_dict["name"] == "Fluffy"
        assert cat_dict["breed"] == "Persian"
        assert cat_dict["age"] == 3
        assert isinstance(cat_dict["owner_id"], str)

    def test_cat_from_dict(self):
        """Test creating cat from dictionary."""
        cat_id = uuid.uuid4()
        owner_id = uuid.uuid4()

        data = {
            "id": str(cat_id),
            "owner_id": str(owner_id),
            "name": "Whiskers",
            "breed": "Siamese",
            "age": 2,
            "owner": {},  # Should be filtered out
            "litterbox": {},  # Should be filtered out
        }

        cat = CatInfo.from_dict(data)

        assert cat.id == cat_id
        assert cat.owner_id == owner_id
        assert cat.name == "Whiskers"
        assert cat.breed == "Siamese"
        assert cat.age == 2


class TestLitterboxInfo:
    """Tests for LitterboxInfo model."""

    def test_litterbox_creation(
        self, db_session, sample_user, sample_cat, sample_litterbox
    ):
        """Test creating a litterbox."""
        db_session.add(sample_user)
        sample_cat.owner = sample_user
        db_session.add(sample_cat)
        sample_litterbox.cat = sample_cat
        db_session.add(sample_litterbox)
        db_session.commit()

        assert sample_litterbox.id is not None
        assert isinstance(sample_litterbox.id, uuid.UUID)
        assert sample_litterbox.name == "Main Litterbox"
        assert sample_litterbox.cat_id == sample_cat.id

    def test_litterbox_cat_relationship(
        self, db_session, sample_user, sample_cat, sample_litterbox
    ):
        """Test litterbox-cat relationship."""
        sample_litterbox.cat = sample_cat
        db_session.add(sample_user)
        sample_cat.owner = sample_user
        db_session.add(sample_cat)
        db_session.add(sample_litterbox)
        db_session.commit()

        assert sample_litterbox.cat == sample_cat
        assert sample_cat.litterbox == sample_litterbox

    def test_litterbox_repr(self, sample_litterbox):
        """Test litterbox string representation."""
        repr_str = repr(sample_litterbox)
        assert "LitterboxInfo" in repr_str
        assert sample_litterbox.name in repr_str

    def test_litterbox_to_dict(self, sample_litterbox):
        """Test converting litterbox to dictionary."""
        litterbox_dict = sample_litterbox.to_dict()

        assert litterbox_dict["name"] == "Main Litterbox"
        assert isinstance(litterbox_dict["cat_id"], str)

    def test_litterbox_from_dict(self):
        """Test creating litterbox from dictionary."""
        litterbox_id = uuid.uuid4()
        cat_id = uuid.uuid4()

        data = {
            "id": str(litterbox_id),
            "cat_id": str(cat_id),
            "name": "Secondary Box",
            "cat": {},  # Should be filtered out
            "litterbox_usage_data": [],  # Should be filtered out
        }

        litterbox = LitterboxInfo.from_dict(data)

        assert litterbox.id == litterbox_id
        assert litterbox.cat_id == cat_id
        assert litterbox.name == "Secondary Box"


class TestLitterboxEdgeDeviceInfo:
    """Tests for LitterboxEdgeDeviceInfo model."""

    def test_edge_device_creation(
        self, db_session, sample_user, sample_cat, sample_litterbox, sample_edge_device
    ):
        """Test creating an edge device."""
        db_session.add(sample_user)
        sample_cat.owner = sample_user
        db_session.add(sample_cat)
        sample_litterbox.cat = sample_cat
        db_session.add(sample_litterbox)
        sample_edge_device.litterbox = sample_litterbox
        db_session.add(sample_edge_device)
        db_session.commit()

        assert sample_edge_device.id is not None
        assert isinstance(sample_edge_device.id, uuid.UUID)
        assert sample_edge_device.device_name == "Smart Litterbox Sensor"
        assert sample_edge_device.device_type == "weight_sensor"
        assert sample_edge_device.litterbox_id == sample_litterbox.id

    def test_edge_device_litterbox_relationship(
        self, db_session, sample_user, sample_cat, sample_litterbox, sample_edge_device
    ):
        """Test edge device-litterbox relationship."""
        sample_edge_device.litterbox = sample_litterbox
        db_session.add(sample_user)
        sample_cat.owner = sample_user
        db_session.add(sample_cat)
        sample_litterbox.cat = sample_cat
        db_session.add(sample_litterbox)
        db_session.add(sample_edge_device)
        db_session.commit()

        assert sample_edge_device.litterbox == sample_litterbox
        assert sample_litterbox.litterbox_edge_device == sample_edge_device

    def test_edge_device_repr(self, sample_edge_device):
        """Test edge device string representation."""
        repr_str = repr(sample_edge_device)
        assert "LitterboxEdgeDeviceInfo" in repr_str
        assert sample_edge_device.device_name in repr_str
        assert sample_edge_device.device_type in repr_str

    def test_edge_device_to_dict(self, sample_edge_device):
        """Test converting edge device to dictionary."""
        device_dict = sample_edge_device.to_dict()

        assert device_dict["device_name"] == "Smart Litterbox Sensor"
        assert device_dict["device_type"] == "weight_sensor"
        assert isinstance(device_dict["litterbox_id"], str)

    def test_edge_device_from_dict(self):
        """Test creating edge device from dictionary."""
        device_id = uuid.uuid4()
        litterbox_id = uuid.uuid4()
        created_at = datetime.now(timezone.utc)

        data = {
            "id": str(device_id),
            "litterbox_id": str(litterbox_id),
            "device_name": "Test Sensor",
            "device_type": "motion_sensor",
            "created_at": created_at.isoformat(),
            "litterbox": {},  # Should be filtered out
            "litterbox_usage_data": [],  # Should be filtered out
        }

        device = LitterboxEdgeDeviceInfo.from_dict(data)

        assert device.id == device_id
        assert device.litterbox_id == litterbox_id
        assert device.device_name == "Test Sensor"
        assert device.device_type == "motion_sensor"
        assert device.created_at == created_at


class TestLitterboxUsageData:
    """Tests for LitterboxUsageData model."""

    def test_usage_data_creation(
        self,
        db_session,
        sample_user,
        sample_cat,
        sample_litterbox,
        sample_edge_device,
        sample_usage_data,
    ):
        """Test creating usage data."""
        db_session.add(sample_user)
        sample_cat.owner = sample_user
        db_session.add(sample_cat)
        sample_litterbox.cat = sample_cat
        db_session.add(sample_litterbox)
        sample_edge_device.litterbox = sample_litterbox
        db_session.add(sample_edge_device)
        sample_usage_data.litterbox_edge_device = sample_edge_device
        db_session.add(sample_usage_data)
        db_session.commit()

        assert sample_usage_data.id is not None
        assert isinstance(sample_usage_data.id, uuid.UUID)
        assert sample_usage_data.weight_enter == 5.2
        assert sample_usage_data.weight_exit == 5.0
        assert sample_usage_data.litterbox_edge_device_id == sample_edge_device.id

    def test_usage_data_edge_device_relationship(
        self,
        db_session,
        sample_user,
        sample_cat,
        sample_litterbox,
        sample_edge_device,
        sample_usage_data,
    ):
        """Test usage data-edge device relationship."""
        sample_usage_data.litterbox_edge_device = sample_edge_device
        db_session.add(sample_user)
        sample_cat.owner = sample_user
        db_session.add(sample_cat)
        sample_litterbox.cat = sample_cat
        db_session.add(sample_litterbox)
        sample_edge_device.litterbox = sample_litterbox
        db_session.add(sample_edge_device)
        db_session.add(sample_usage_data)
        db_session.commit()

        assert sample_usage_data.litterbox_edge_device == sample_edge_device
        assert sample_usage_data in sample_edge_device.litterbox_usage_data

    def test_usage_data_repr(self, sample_usage_data):
        """Test usage data string representation."""
        repr_str = repr(sample_usage_data)
        assert "LitterboxUsageData" in repr_str
        assert "5.2" in repr_str
        assert "5.0" in repr_str

    def test_usage_data_to_dict(self, sample_usage_data):
        """Test converting usage data to dictionary."""
        usage_dict = sample_usage_data.to_dict()

        assert usage_dict["weight_enter"] == 5.2
        assert usage_dict["weight_exit"] == 5.0
        assert isinstance(usage_dict["litterbox_edge_device_id"], str)
        assert "enter_time" in usage_dict
        assert "exit_time" in usage_dict

    def test_usage_data_from_dict(self):
        """Test creating usage data from dictionary."""
        usage_id = uuid.uuid4()
        device_id = uuid.uuid4()
        enter_time = datetime.now(timezone.utc)
        exit_time = datetime.now(timezone.utc)
        created_at = datetime.now(timezone.utc)

        data = {
            "id": str(usage_id),
            "litterbox_edge_device_id": str(device_id),
            "enter_time": enter_time.isoformat(),
            "exit_time": exit_time.isoformat(),
            "weight_enter": 4.5,
            "weight_exit": 4.3,
            "created_at": created_at.isoformat(),
            "litterbox_edge_device": {},  # Should be filtered out
        }

        usage = LitterboxUsageData.from_dict(data)

        assert usage.id == usage_id
        assert usage.litterbox_edge_device_id == device_id
        assert usage.enter_time == enter_time
        assert usage.exit_time == exit_time
        assert usage.weight_enter == 4.5
        assert usage.weight_exit == 4.3
        assert usage.created_at == created_at


class TestCascadeDeletes:
    """Test cascade delete functionality."""

    def test_user_delete_cascades_to_cats(self, db_session, sample_user, sample_cat):
        """Test that deleting a user deletes their cats."""
        sample_cat.owner = sample_user
        db_session.add(sample_user)
        db_session.add(sample_cat)
        db_session.commit()

        cat_id = sample_cat.id

        db_session.delete(sample_user)
        db_session.commit()

        # Cat should be deleted due to cascade
        deleted_cat = db_session.query(CatInfo).filter_by(id=cat_id).first()
        assert deleted_cat is None

    def test_litterbox_delete_cascades_to_usage_data(
        self,
        db_session,
        sample_user,
        sample_cat,
        sample_litterbox,
        sample_edge_device,
        sample_usage_data,
    ):
        """Test that deleting a litterbox deletes its usage data."""
        # Set up relationships
        sample_cat.owner = sample_user
        sample_litterbox.cat = sample_cat
        sample_edge_device.litterbox = sample_litterbox
        sample_usage_data.litterbox_edge_device = sample_edge_device

        db_session.add_all(
            [
                sample_user,
                sample_cat,
                sample_litterbox,
                sample_edge_device,
                sample_usage_data,
            ]
        )
        db_session.commit()

        usage_id = sample_usage_data.id
        device_id = sample_edge_device.id

        db_session.delete(sample_litterbox)
        db_session.commit()

        # Usage data and edge device should be deleted due to cascade
        deleted_usage = (
            db_session.query(LitterboxUsageData).filter_by(id=usage_id).first()
        )
        deleted_device = (
            db_session.query(LitterboxEdgeDeviceInfo).filter_by(id=device_id).first()
        )

        assert deleted_usage is None
        assert deleted_device is None


class TestDataIntegrity:
    """Test data integrity and validation."""

    def test_required_fields(self, db_session):
        """Test that required fields are enforced."""
        # Test UserInfo with missing username
        with pytest.raises((IntegrityError, TypeError)):
            user = UserInfo(email="test@example.com", password_hash="hash")
            db_session.add(user)
            db_session.commit()

    def test_foreign_key_constraints(self, db_session):
        """Test foreign key constraints."""
        # Try to create a cat with non-existent owner_id
        cat = CatInfo(name="Orphan Cat")

        db_session.add(cat)
        with pytest.raises(IntegrityError):
            db_session.commit()

    # def test_datetime_handling(self, db_session, sample_user):
    #     """Test that datetime fields are handled correctly."""
    #     db_session.add(sample_user)
    #     db_session.commit()
    #     assert sample_user.created_at is not None
    #     assert isinstance(sample_user.created_at, datetime)
    #     assert sample_user.created_at.tzinfo == timezone.utc
