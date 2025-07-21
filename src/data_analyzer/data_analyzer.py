"""
This module takes care of data analysis tasks for the Litterbox data collector.
It includes functions to analyze litterbox usage data.
"""

from typing import List, Dict, Any
from database.gateway import DatabaseGateway
from database.postgresql_gateway import PostgreSQLGateway
from config.logging import get_logger

logger = get_logger(__name__)
DATABASE_URL = "postgresql://example_user:example_password@localhost:5435/example_db"

def analyze_litterbox_usage_data(db_gateway: PostgreSQLGateway) -> Dict[str, Any]:
    """
    Analyze litterbox usage data from the database.

    Args:
        db_gateway (DatabaseGateway): The database gateway instance to interact with the database.

    Returns:
        Dict[str, Any]: A dictionary containing analysis results such as total usage, average usage, etc.
    """
    try:
        # Fetch litterbox usage data from the database
        db_gateway.connect()
        logger.info("Fetching litterbox usage data from the database...")
        usage_data = db_gateway.get_litterbox_usage_data()
        
        if not usage_data:
            logger.warning("No litterbox usage data found.")
            return {}

        logger.info(f"Fetched {len(usage_data)} records of litterbox usage data.")
        analyzed_data = []

        # Perform analysis on the fetched data
        for record in usage_data:
            duration = record['exit_time'] - record['enter_time']
            cat_weight = record['weight_enter'] - record['weight_exit']
            analyzed_record = {
                "cat_id": record["cat_id"],
                "duration": duration.total_seconds(),
                "cat_weight": cat_weight,
                "timestamp": record["timestamp"],
                
            }
            analyzed_data.append(analyzed_record)
        
        # Calculate the average duration and weight 
        total_duration = sum(item['duration'] for item in analyzed_data)
        total_weight = sum(item['cat_weight'] for item in analyzed_data)    
        average_duration = total_duration / len(analyzed_data)
        average_weight = total_weight / len(analyzed_data)

        # Calculate total usage per day
        usage_count_per_day = {}
        for record in usage_data:
            date = record['exit_time'].date()
            if date not in usage_count_per_day:
                usage_count_per_day[date] = 0
            usage_count_per_day[date] += 1
        logger.info("Litterbox usage data analysis completed successfully.")

        return {
            "total_usage": len(analyzed_data),
            "average_duration": average_duration,
            "average_weight": average_weight,
            "usage_count_per_day": usage_count_per_day,
        }
        
    except Exception as e:
        logger.error(f"Error analyzing litterbox usage data: {e}")
        raise

db_gateway = PostgreSQLGateway(DATABASE_URL)  # Replace with actual gateway implementatio
print(analyze_litterbox_usage_data(db_gateway))