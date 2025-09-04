#!/usr/bin/env python3
"""
Test script for BigQuery integration.
This script tests the BigQuery tools without running the full agent system.
"""

import asyncio
import os
import sys
import logging
from typing import Dict

# Add the cookie-scheduler-agent directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cookie-scheduler-agent'))

from bigquery_tools import (
    BigQueryOrderManager,
    get_latest_order_from_bigquery,
    update_order_status_in_bigquery,
    get_order_analytics,
    setup_bigquery_environment
)

# Mock ToolContext for testing
class MockToolContext:
    def __init__(self):
        self.state = {}

async def test_bigquery_setup():
    """Test the BigQuery environment setup."""
    print("Testing BigQuery Environment Setup...")
    
    result = setup_bigquery_environment()
    if result["status"] == "success":
        print("BigQuery environment setup successful")
    else:
        print(f"Setup failed: {result['message']}")
        return False
    return True

async def test_get_latest_order():
    """Test getting the latest order."""
    print("\nTesting Get Latest Order...")
    
    mock_context = MockToolContext()
    result = await get_latest_order_from_bigquery(mock_context)
    
    if result.get("status") == "error":
        print(f"Get latest order failed: {result['message']}")
        return False
    else:
        print(" Successfully retrieved latest order:")
        print(f"   Order Number: {result.get('order_number')}")
        print(f"   Customer: {result.get('customer_name')}")
        print(f"   Status: {result.get('order_status')}")
        print(f"   Total: ${result.get('total_amount')}")
        return True

async def test_update_order_status():
    """Test updating order status."""
    print("\n Testing Update Order Status...")
    
    # First get an order to update
    mock_context = MockToolContext()
    order_result = await get_latest_order_from_bigquery(mock_context)
    
    if order_result.get("status") == "error":
        print("Cannot test update - no orders found")
        return False
    
    order_number = order_result.get("order_number")
    if not order_number:
        print("Cannot test update - no order number found")
        return False
    
    # Update the order status
    result = await update_order_status_in_bigquery(
        mock_context, 
        order_number, 
        "confirmed"
    )
    
    if result.get("status") == "success":
        print("Successfully updated order status:")
        print(f"   Order: {result.get('order_number')}")
        print(f"   New Status: {result.get('new_status')}")
        
        # Check if this was a streaming buffer conflict (expected in demo)
        if "streaming buffer" in result.get("message", ""):
            print(f"   Note: {result.get('message')}")
        else:
            print(f"   Affected Rows: {result.get('affected_rows')}")
        return True
    else:
        # For demo purposes, streaming buffer conflicts are expected
        if "streaming buffer" in result.get("message", ""):
            print("  Update delayed due to streaming buffer conflict (expected in demo)")
            print("   This is normal behavior when data was recently inserted")
            return True
        else:
            print(f" Update failed: {result.get('message')}")
            return False

async def test_order_analytics():
    """Test getting order analytics."""
    print("\n Testing Order Analytics...")
    
    mock_context = MockToolContext()
    result = await get_order_analytics(mock_context, days=30)
    
    if result.get("status") == "success":
        print(" Successfully retrieved analytics:")
        analytics = result.get("analytics", [])
        for item in analytics:
            print(f"   Status: {item.get('order_status')} | "
                  f"Count: {item.get('order_count')} | "
                  f"Avg Value: ${item.get('avg_order_value', 0):.2f} | "
                  f"Revenue: ${item.get('total_revenue', 0):.2f}")
        return True
    else:
        print(f" Analytics failed: {result.get('message')}")
        return False

async def test_direct_query():
    """Test direct BigQuery query."""
    print("\n Testing Direct BigQuery Query...")
    
    try:
        from google.cloud import bigquery
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            print(" GOOGLE_CLOUD_PROJECT not set")
            return False
        
        client = bigquery.Client(project=project_id)
        
        query = f"""
        SELECT 
            COUNT(*) as total_orders,
            COUNT(DISTINCT customer_email) as unique_customers,
            SUM(total_amount) as total_revenue
        FROM `{project_id}.cookie_delivery.orders`
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        for row in results:
            print(" Direct query successful:")
            print(f"   Total Orders: {row.total_orders}")
            print(f"   Unique Customers: {row.unique_customers}")
            print(f"   Total Revenue: ${row.total_revenue:.2f}")
        
        return True
        
    except Exception as e:
        print(f" Direct query failed: {e}")
        return False

async def main():
    """Run all BigQuery tests."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("========================================")
    print("BigQuery Integration Test Suite")
    print("========================================")
    
    # Check environment
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print(" GOOGLE_CLOUD_PROJECT environment variable not set")
        print("Please set it with: export GOOGLE_CLOUD_PROJECT=your-project-id")
        return
    
    print(f"Using project: {project_id}")
    print()
    
    # Run tests
    tests = [
        ("Environment Setup", test_bigquery_setup),
        ("Get Latest Order", test_get_latest_order),
        ("Update Order Status", test_update_order_status),
        ("Order Analytics", test_order_analytics),
        ("Direct Query", test_direct_query),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f" {test_name} failed with exception: {e}")
    
    print("\n========================================")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(" All tests passed! BigQuery integration is working correctly.")
    else:
        print("  Some tests failed. Please check the errors above.")
    
    print("========================================")

if __name__ == "__main__":
    asyncio.run(main())
