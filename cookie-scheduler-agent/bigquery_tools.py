"""
BigQuery integration tools for the cookie delivery system.
This file shows how to implement real BigQuery connectivity.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.adk.tools.tool_context import ToolContext

# BigQuery Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
DATASET_ID = "cookie_delivery"
ORDERS_TABLE = "orders"

class BigQueryOrderManager:
    """Manages BigQuery operations for cookie orders."""
    
    def __init__(self):
        """Initialize BigQuery client."""
        self.client = bigquery.Client(project=PROJECT_ID)
        self.table_id = f"{PROJECT_ID}.{DATASET_ID}.{ORDERS_TABLE}"
        
    def ensure_dataset_exists(self):
        """Create dataset if it doesn't exist."""
        dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
        try:
            self.client.get_dataset(dataset_id)
            logging.info(f"Dataset {dataset_id} already exists.")
        except NotFound:
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = "US"
            dataset = self.client.create_dataset(dataset)
            logging.info(f"Created dataset {dataset.dataset_id}")
    
    def create_orders_table(self):
        """Create the orders table with proper schema."""
        schema = [
            bigquery.SchemaField("order_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("order_number", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("customer_email", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("customer_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("customer_phone", "STRING"),
            bigquery.SchemaField("order_items", "RECORD", mode="REPEATED", fields=[
                bigquery.SchemaField("item_name", "STRING"),
                bigquery.SchemaField("quantity", "INTEGER"),
                bigquery.SchemaField("unit_price", "FLOAT"),
            ]),
            bigquery.SchemaField("delivery_address", "RECORD", fields=[
                bigquery.SchemaField("street", "STRING"),
                bigquery.SchemaField("city", "STRING"),
                bigquery.SchemaField("state", "STRING"),
                bigquery.SchemaField("zip_code", "STRING"),
                bigquery.SchemaField("country", "STRING"),
            ]),
            bigquery.SchemaField("delivery_location", "STRING"),
            bigquery.SchemaField("delivery_request_date", "DATE"),
            bigquery.SchemaField("delivery_time_preference", "STRING"),
            bigquery.SchemaField("order_status", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("total_amount", "FLOAT"),
            bigquery.SchemaField("order_date", "TIMESTAMP"),
            bigquery.SchemaField("special_instructions", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
        ]
        
        table = bigquery.Table(self.table_id, schema=schema)
        try:
            table = self.client.create_table(table)
            logging.info(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
        except Exception as e:
            logging.error(f"Error creating table: {e}")

# ADK Tool Functions that use BigQuery

async def get_latest_order_from_bigquery(tool_context: ToolContext) -> Dict:
    """
    Fetch the latest order with 'order_placed' status from BigQuery.
    """
    logging.info("Fetching latest order from BigQuery...")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.{ORDERS_TABLE}`
        WHERE order_status = 'order_placed'
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        for row in results:
            order_data = dict(row)
            # Save to agent state
            tool_context.state['order_details'] = order_data
            logging.info(f"Found order: {order_data['order_number']}")
            return order_data
        
        logging.warning("No orders with status 'order_placed' found.")
        return {"status": "error", "message": "No new orders found."}
        
    except Exception as e:
        logging.error(f"BigQuery error: {e}")
        return {"status": "error", "message": f"Database error: {str(e)}"}

async def update_order_status_in_bigquery(
    tool_context: ToolContext, 
    order_number: str, 
    new_status: str
) -> Dict:
    """
    Update order status in BigQuery.
    """
    logging.info(f"Updating order {order_number} status to {new_status} in BigQuery...")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.{ORDERS_TABLE}`
        SET order_status = @new_status, 
            updated_at = CURRENT_TIMESTAMP()
        WHERE order_number = @order_number
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("new_status", "STRING", new_status),
                bigquery.ScalarQueryParameter("order_number", "STRING", order_number),
            ]
        )
        
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the job to complete
        
        if query_job.num_dml_affected_rows > 0:
            logging.info(f"Updated {query_job.num_dml_affected_rows} rows")
            return {
                "status": "success", 
                "order_number": order_number, 
                "new_status": new_status,
                "affected_rows": query_job.num_dml_affected_rows
            }
        else:
            logging.warning(f"No rows updated for order {order_number}")
            return {"status": "error", "message": f"Order {order_number} not found"}
            
    except Exception as e:
        logging.error(f"BigQuery update error: {e}")
        return {"status": "error", "message": f"Database error: {str(e)}"}

async def get_order_analytics(tool_context: ToolContext, days: int = 30) -> Dict:
    """
    Get order analytics from BigQuery for business insights.
    """
    logging.info(f"Fetching order analytics for last {days} days...")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        query = f"""
        SELECT 
            order_status,
            COUNT(*) as order_count,
            AVG(total_amount) as avg_order_value,
            SUM(total_amount) as total_revenue
        FROM `{PROJECT_ID}.{DATASET_ID}.{ORDERS_TABLE}`
        WHERE DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY)
        GROUP BY order_status
        ORDER BY order_count DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("days", "INT64", days),
            ]
        )
        
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        analytics = []
        for row in results:
            analytics.append(dict(row))
        
        return {"status": "success", "analytics": analytics}
        
    except Exception as e:
        logging.error(f"BigQuery analytics error: {e}")
        return {"status": "error", "message": f"Analytics error: {str(e)}"}

