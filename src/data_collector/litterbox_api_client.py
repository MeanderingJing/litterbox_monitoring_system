"""API client for interacting with the Litterbox API."""

import requests
from typing import Any, Dict, List, Optional
from config.logging import get_logger

logger = get_logger(__name__)
LITTERBOX_API_URL = "https://fake-litterbox-usage-api-1bf46a2bc363.herokuapp.com/"
# LITTERBOX_API_URL = "http://localhost:5000/"
LITTERBOX_USAGE_DATA_ENDPOINT = "litterbox_usage_data"


def get_litterbox_usage_data(
    endpoint: str = LITTERBOX_USAGE_DATA_ENDPOINT,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch litterbox usage data from the Litterbox API.

    Params:
        url (str): The API endpoint to fetch data from.
        start_data (str): Optional start date filter (ISO format).
        end_date (str): Optional end date filter (ISO format).
    """
    # Ensure the endpoint is properly formatted
    base_url = LITTERBOX_API_URL.rstrip("/")
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    url = f"{base_url}{endpoint}"
    logger.info(f"Fetching data from Litterbox API at {url}")

    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching data from Litterbox API: {e}")
        raise
