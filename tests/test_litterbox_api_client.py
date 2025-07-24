"""Tests for the Litterbox API client using pytest."""

import pytest
import requests

from data_collector.litterbox_api_client import (LITTERBOX_API_URL,
                                                 get_litterbox_usage_data)


# Pytest fixtures for common test data
@pytest.fixture
def sample_api_response():
    """Sample API response data."""
    return [
        {"id": 1, "timestamp": "2024-01-01T10:00:00", "cat_id": "whiskers"},
        {"id": 2, "timestamp": "2024-01-01T15:30:00", "cat_id": "mittens"},
    ]


@pytest.fixture
def mock_successful_response(mocker, sample_api_response):
    """Mock a successful API response."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = sample_api_response
    mock_response.raise_for_status.return_value = None
    return mock_response


class TestGetLitterboxUsageData:
    """Test cases for get_litterbox_usage_data function."""

    def test_successful_request_no_params(
        self, mocker, mock_successful_response, sample_api_response
    ):
        """Test successful API call without parameters."""
        # Arrange
        mock_get = mocker.patch(
            "data_collector.litterbox_api_client.requests.get",
            return_value=mock_successful_response,
        )

        # Act
        result = get_litterbox_usage_data()

        # Assert
        assert len(result) == 2
        assert result[0]["cat_id"] == "whiskers"
        assert result == sample_api_response
        mock_get.assert_called_once_with(
            f"{LITTERBOX_API_URL}litterbox_usage_data", params={}
        )

    def test_successful_request_with_date_params(self, mocker):
        """Test successful API call with date parameters."""
        # Arrange
        expected_response = [{"id": 1, "cat_id": "fluffy"}]
        mock_response = mocker.Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status.return_value = None
        mock_get = mocker.patch(
            "data_collector.litterbox_api_client.requests.get",
            return_value=mock_response,
        )

        # Act
        result = get_litterbox_usage_data(
            start_date="2024-01-01", end_date="2024-01-31"
        )

        # Assert
        assert result == expected_response
        mock_get.assert_called_once_with(
            f"{LITTERBOX_API_URL}litterbox_usage_data",
            params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        )


# Integration tests
@pytest.mark.integration
class TestLitterboxClientIntegration:
    """Integration tests that require a running API."""

    def test_real_api_call_success(self):
        """Test against the real API (requires localhost:5000 to be running)."""
        try:
            result = get_litterbox_usage_data()
            assert isinstance(result, list)
            # Add more specific assertions based on your API's actual response
            for item in result:
                assert isinstance(item, dict)
                # Add assertions for expected fields if known
        except requests.RequestException as e:
            pytest.skip(f"API not available for integration test: {e}")

    def test_real_api_call_with_params(self):
        """Test real API call with date parameters."""
        try:
            result = get_litterbox_usage_data(
                start_date="2024-01-01", end_date="2024-12-31"
            )
            assert isinstance(result, list)
        except requests.RequestException as e:
            pytest.skip(f"API not available for integration test: {e}")
