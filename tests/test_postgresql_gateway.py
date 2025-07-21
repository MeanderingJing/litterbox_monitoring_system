"""Tests for PostgreSQL database gateway using pytest."""

import uuid
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from database.postgresql_gateway import PostgreSQLGateway
from models.litterbox_usage_data import LitterboxUsageData


# Test fixtures
@pytest.fixture
def db_url():
    """Test database URL."""
    return "postgresql://example_user:example_password@localhost:5435/example_db"


@pytest.fixture
def gateway(db_url):
    """Create a PostgreSQLGateway instance for testing."""
    return PostgreSQLGateway(db_url)


@pytest.fixture
def sample_usage_data():
    """Sample litterbox usage data for testing."""
    return [
        {
            "id": uuid.uuid4(),
            "cat_id": 1,
            "litterbox_id": 1,
            "enter_time": datetime(2024, 1, 15, 10, 30, 0),
            "exit_time": datetime(2024, 1, 15, 10, 35, 0),
            "weight_enter": 4.5,
            "weight_exit": 4.3,
            "timestamp": datetime(2024, 1, 15, 10, 35, 30),
        },
        {
            "id": uuid.uuid4(),
            "cat_id": 2,
            "litterbox_id": 2,
            "enter_time": datetime(2024, 2, 15, 10, 30, 0),
            "exit_time": datetime(2024, 2, 15, 10, 35, 0),
            "weight_enter": 9.5,
            "weight_exit": 9.3,
            "timestamp": datetime(2024, 2, 15, 10, 35, 30),
        }
    ]


@pytest.fixture
def mock_litterbox_record():
    """Mock LitterboxUsageData record."""
    record = Mock(spec=LitterboxUsageData)
    record.id = uuid.uuid4()
    record.cat_id = 1
    record.litterbox_id = 1
    record.enter_time = datetime(2024, 1, 1, 10, 0, 0)
    record.exit_time = datetime(2024, 1, 1, 10, 5, 0)
    record.weight_enter = 5.0
    record.weight_exit = 4.8    
    record.timestamp = datetime(2024, 1, 1, 10, 5, 0)
   
    record.__dict__ = {
        "id": str(record.id),
        "cat_id": record.cat_id,
        "litterbox_id": record.litterbox_id,
        "enter_time": record.enter_time.isoformat(),
        "exit_time": record.exit_time.isoformat(),
        "weight_enter": record.weight_enter,
        "weight_exit": record.weight_exit,
        "timestamp": record.timestamp.isoformat(),
    }
    return record


class TestPostgreSQLGatewayInit:
    """Test initialization of PostgreSQLGateway."""
    
    def test_init_sets_properties(self, db_url):
        """Test that initialization sets the correct properties."""
        gateway = PostgreSQLGateway(db_url)
        
        assert gateway.db_url == db_url
        assert gateway.engine is None
        assert gateway.session is None
        assert gateway.logger is not None


class TestPostgreSQLGatewayConnect:
    """Test database connection functionality."""
    
    # @patch('database.postgresql_gateway.create_engine')
    # @patch('database.postgresql_gateway.Session')
    # def test_connect_success(self, mock_session_class, mock_create_engine, gateway):
    #     """Test successful database connection."""
    #     # Arrange
    #     mock_engine = Mock()
    #     mock_connection = Mock()
    #     mock_engine.connect.return_value.__enter__.return_value = mock_connection
    #     mock_engine.connect.return_value.__exit__.return_value = None
    #     mock_create_engine.return_value = mock_engine
        
    #     mock_session = Mock()
    #     mock_session_class.return_value = mock_session
        
    #     # Act
    #     gateway.connect()
        
    #     # Assert
    #     mock_create_engine.assert_called_once_with(gateway.db_url)
    #     mock_session_class.assert_called_once_with(mock_engine)
    #     mock_connection.execute.assert_called_once()
    #     assert gateway.engine == mock_engine
    #     assert gateway.session == mock_session
    
    # @patch('database.postgresql_gateway.create_engine')
    # def test_connect_failure(self, mock_create_engine, gateway):
    #     """Test database connection failure."""
    #     # Arrange
    #     mock_create_engine.side_effect = OperationalError("Connection failed", None, None)
        
    #     # Act & Assert
    #     with pytest.raises(OperationalError):
    #         gateway.connect()
        
    #     assert gateway.engine is None
    #     assert gateway.session is None


# class TestPostgreSQLGatewayDisconnect:
#     """Test database disconnection functionality."""
    
#     def test_disconnect_with_active_connection(self, gateway):
#         """Test disconnecting when connection is active."""
#         # Arrange
#         mock_session = Mock()
#         mock_engine = Mock()
#         gateway.session = mock_session
#         gateway.engine = mock_engine
        
#         # Act
#         gateway.disconnect()
        
#         # Assert
#         mock_session.close.assert_called_once()
#         mock_engine.dispose.assert_called_once()
#         assert gateway.session is None
#         assert gateway.engine is None
    
#     def test_disconnect_with_no_connection(self, gateway):
#         """Test disconnecting when no connection exists."""
#         # Arrange
#         gateway.session = None
#         gateway.engine = None
        
#         # Act
#         gateway.disconnect()
        
#         # Assert - Should not raise any errors
#         assert gateway.session is None
#         assert gateway.engine is None


# class TestPostgreSQLGatewayCreateTables:
#     """Test table creation functionality."""
    
#     @patch('postgresql_gateway.Base')
#     def test_create_tables_success(self, mock_base, gateway):
#         """Test successful table creation."""
#         # Arrange
#         mock_engine = Mock()
#         gateway.engine = mock_engine
        
#         # Act
#         gateway.create_tables()
        
#         # Assert
#         mock_base.metadata.create_all.assert_called_once_with(mock_engine)
    
#     @patch('postgresql_gateway.Base')
#     def test_create_tables_failure(self, mock_base, gateway):
#         """Test table creation failure."""
#         # Arrange
#         mock_engine = Mock()
#         gateway.engine = mock_engine
#         mock_base.metadata.create_all.side_effect = SQLAlchemyError("Table creation failed")
        
#         # Act & Assert
#         with pytest.raises(SQLAlchemyError):
#             gateway.create_tables()


# class TestPostgreSQLGatewayInsertData:
#     """Test data insertion functionality."""
    
#     @patch('postgresql_gateway.LitterboxUsageData')
#     def test_insert_litterbox_usage_data_success(self, mock_model, gateway, sample_usage_data):
#         """Test successful data insertion."""
#         # Arrange
#         mock_session = Mock()
#         gateway.session = mock_session
        
#         # Mock the query to return None (no existing records)
#         mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
#         # Mock the model creation
#         mock_records = [Mock(), Mock()]
#         mock_model.from_dict.side_effect = mock_records
        
#         # Act
#         gateway.insert_litterbox_usage_data(sample_usage_data)
        
#         # Assert
#         assert mock_model.from_dict.call_count == len(sample_usage_data)
#         assert mock_session.add.call_count == len(sample_usage_data)
#         mock_session.commit.assert_called_once()
        
#         # Check that from_dict was called with correct data
#         expected_calls = [call(record) for record in sample_usage_data]
#         mock_model.from_dict.assert_has_calls(expected_calls)
    
#     def test_insert_litterbox_usage_data_duplicate_id(self, gateway, sample_usage_data):
#         """Test insertion failure due to duplicate ID."""
#         # Arrange
#         mock_session = Mock()
#         gateway.session = mock_session
        
#         # Mock the query to return an existing record
#         existing_record = Mock()
#         existing_record.id = sample_usage_data[0]["id"]
#         mock_session.query.return_value.filter_by.return_value.first.return_value = existing_record
        
#         # Act & Assert
#         with pytest.raises(ValueError, match=f"Record with ID {sample_usage_data[0]['id']} already exists"):
#             gateway.insert_litterbox_usage_data(sample_usage_data)
        
#         # Verify no commit was attempted
#         mock_session.commit.assert_not_called()
    
#     @patch('postgresql_gateway.LitterboxUsageData')
#     def test_insert_litterbox_usage_data_database_error(self, mock_model, gateway, sample_usage_data):
#         """Test insertion failure due to database error."""
#         # Arrange
#         mock_session = Mock()
#         gateway.session = mock_session
        
#         # Mock the query to return None (no existing records)
#         mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
#         # Mock commit to raise an exception
#         mock_session.commit.side_effect = SQLAlchemyError("Database error")
        
#         # Act & Assert
#         with pytest.raises(SQLAlchemyError):
#             gateway.insert_litterbox_usage_data(sample_usage_data)


# class TestPostgreSQLGatewayRetrieveData:
#     """Test data retrieval functionality."""
    
#     def test_get_litterbox_usage_data_success(self, gateway, mock_litterbox_record):
#         """Test successful data retrieval."""
#         # Arrange
#         mock_session = Mock()
#         gateway.session = mock_session
        
#         mock_query_result = [mock_litterbox_record]
#         mock_session.query.return_value.all.return_value = mock_query_result
        
#         # Act
#         result = gateway.get_litterbox_usage_data()
        
#         # Assert
#         assert len(result) == 1
#         assert result[0] == mock_litterbox_record.__dict__
#         mock_session.query.assert_called_once_with(LitterboxUsageData)
    
#     def test_get_litterbox_usage_data_empty_result(self, gateway):
#         """Test data retrieval with empty result."""
#         # Arrange
#         mock_session = Mock()
#         gateway.session = mock_session
#         mock_session.query.return_value.all.return_value = []
        
#         # Act
#         result = gateway.get_litterbox_usage_data()
        
#         # Assert
#         assert result == []


# class TestPostgreSQLGatewayLatestTimestamp:
#     """Test latest timestamp retrieval functionality."""
    
#     def test_get_latest_litterbox_usage_timestamp_success(self, gateway, mock_litterbox_record):
#         """Test successful retrieval of latest timestamp."""
#         # Arrange
#         mock_session = Mock()
#         gateway.session = mock_session
        
#         mock_session.query.return_value.order_by.return_value.first.return_value = mock_litterbox_record
        
#         # Act
#         result = gateway.get_latest_litterbox_usage_timestamp()
        
#         # Assert
#         expected_timestamp = mock_litterbox_record.timestamp.isoformat()
#         assert result == expected_timestamp
        
#         # Verify the query was constructed correctly
#         mock_session.query.assert_called_once_with(LitterboxUsageData)
#         mock_session.query.return_value.order_by.assert_called_once()
#         mock_session.query.return_value.order_by.return_value.first.assert_called_once()
    
#     def test_get_latest_litterbox_usage_timestamp_no_data(self, gateway):
#         """Test retrieval of latest timestamp when no data exists."""
#         # Arrange
#         mock_session = Mock()
#         gateway.session = mock_session
#         mock_session.query.return_value.order_by.return_value.first.return_value = None
        
#         # Act
#         result = gateway.get_latest_litterbox_usage_timestamp()
        
#         # Assert
#         assert result is None
    
#     def test_get_latest_litterbox_usage_timestamp_database_error(self, gateway):
#         """Test retrieval of latest timestamp with database error."""
#         # Arrange
#         mock_session = Mock()
#         gateway.session = mock_session
#         mock_session.query.side_effect = SQLAlchemyError("Database query failed")
        
#         # Act
#         result = gateway.get_latest_litterbox_usage_timestamp()
        
#         # Assert
#         assert result is None


# # Integration tests (require actual database)
# @pytest.mark.integration
# class TestPostgreSQLGatewayIntegration:
#     """Integration tests for PostgreSQLGateway."""
    
#     @pytest.fixture
#     def test_db_url(self):
#         """Test database URL for integration tests."""
#         return "postgresql://test_user:test_password@localhost:5432/test_litterbox_db"
    
#     @pytest.fixture
#     def integration_gateway(self, test_db_url):
#         """Gateway instance for integration tests."""
#         gateway = PostgreSQLGateway(test_db_url)
#         try:
#             gateway.connect()
#             gateway.create_tables()
#             yield gateway
#         finally:
#             gateway.disconnect()
    
#     def test_full_workflow_integration(self, integration_gateway, sample_usage_data):
#         """Test the complete workflow: insert, retrieve, get latest timestamp."""
#         try:
#             # Insert data
#             integration_gateway.insert_litterbox_usage_data(sample_usage_data)
            
#             # Retrieve data
#             retrieved_data = integration_gateway.get_litterbox_usage_data()
#             assert len(retrieved_data) >= len(sample_usage_data)
            
#             # Get latest timestamp
#             latest_timestamp = integration_gateway.get_latest_litterbox_usage_timestamp()
#             assert latest_timestamp is not None
            
#         except Exception as e:
#             pytest.skip(f"Integration test skipped - database not available: {e}")


# # Parametrized tests for edge cases
# class TestPostgreSQLGatewayEdgeCases:
#     """Test edge cases and boundary conditions."""
    
#     @pytest.mark.parametrize("data_input", [
#         [],  # Empty list
#         [{"id": 1, "timestamp": "2024-01-01T10:00:00", "cat_id": "test"}],  # Single record
#         # Add more edge cases as needed
#     ])
#     @patch('postgresql_gateway.LitterboxUsageData')
#     def test_insert_with_various_data_sizes(self, mock_model, gateway, data_input):
#         """Test insertion with various data sizes."""
#         # Arrange
#         mock_session = Mock()
#         gateway.session = mock_session
#         mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
#         # Act
#         if data_input:
#             gateway.insert_litterbox_usage_data(data_input)
#             # Assert
#             assert mock_model.from_dict.call_count == len(data_input)
#         else:
#             # Empty data should still work
#             gateway.insert_litterbox_usage_data(data_input)
#             mock_model.from_dict.assert_not_called()


# # Test context manager usage (if your gateway needs to support it)
# class TestPostgreSQLGatewayContextManager:
#     """Test context manager functionality if implemented."""
    
#     def test_context_manager_usage(self, gateway):
#         """Test that gateway can be used as context manager if implemented."""
#         # This would test __enter__ and __exit__ methods if you implement them
#         # For now, we'll test manual connect/disconnect
        
#         with patch.object(gateway, 'connect') as mock_connect, \
#              patch.object(gateway, 'disconnect') as mock_disconnect:
            
#             # Manual context management
#             gateway.connect()
#             try:
#                 # Do some work
#                 pass
#             finally:
#                 gateway.disconnect()
            
#             mock_connect.assert_called_once()
#             mock_disconnect.assert_called_once()


# # Performance tests (can be marked as slow)
# @pytest.mark.slow
# class TestPostgreSQLGatewayPerformance:
#     """Performance-related tests."""
    
#     @patch('postgresql_gateway.LitterboxUsageData')
#     def test_insert_large_dataset_performance(self, mock_model, gateway):
#         """Test insertion performance with large dataset."""
#         # Arrange
#         large_dataset = [
#             {"id": i, "timestamp": f"2024-01-01T10:00:0{i%10}", "cat_id": f"cat_{i}"}
#             for i in range(1000)
#         ]
        
#         mock_session = Mock()
#         gateway.session = mock_session
#         mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
#         # Act
#         gateway.insert_litterbox_usage_data(large_dataset)
        
#         # Assert
#         assert mock_model.from_dict.call_count == len(large_dataset)
#         assert mock_session.add.call_count == len(large_dataset)
#         mock_session.commit.assert_called_once()