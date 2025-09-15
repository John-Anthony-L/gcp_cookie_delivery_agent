"""
Clean agent definitions using Google ADK with BigQuery toolset integration.
"""

import logging
from pathlib import Path

from google.adk import Agent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import StdioServerParameters
from bigquery_utils.bigquery_tools import get_bigquery_toolset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def store_database_agent():
    """Agent for managing store inventory and customer data in BigQuery."""
    
    # Initialize BigQuery toolset
    bigquery_toolset = get_bigquery_toolset()
    
    if bigquery_toolset is None:
        logger.error("Failed to initialize BigQuery toolset")
        return None
        
    # Build agent with BigQuery capabilities
    agent = Agent(
        name="store_database_agent",
        model="gemini-2.0-flash-exp",
        description="Manages store inventory and customer data using BigQuery ADK toolset",
        instruction="""You are a helpful assistant that manages store inventory and customer data.
        You can query BigQuery databases to help with order management, inventory tracking, and customer service.
        Use the BigQuery tools to access data about cookie orders, customer preferences, and delivery schedules.
        
        Available BigQuery tools:
        - list_dataset_ids: List all available datasets
        - get_dataset_info: Get detailed information about a specific dataset  
        - list_table_ids: List all tables in a dataset
        - get_table_info: Get schema and details for a specific table
        - execute_sql: Execute SQL queries against BigQuery
        - ask_data_insights: Get AI-powered insights about your data
        
        Focus on helping with cookie delivery order management.""",
        tools=[bigquery_toolset]
    )
    
    logger.info("✅ Store database agent initialized successfully")
    return agent

def email_agent():
    """Agent for email management and notifications."""
    
    # Initialize BigQuery toolset for order data access
    bigquery_toolset = get_bigquery_toolset()
    
    if bigquery_toolset is None:
        logger.error("Failed to initialize BigQuery toolset for email agent")
        return None
    
    # Build agent with email and BigQuery capabilities
    agent = Agent(
        name="email_agent", 
        model="gemini-2.0-flash-exp",
        description="Manages email communications with BigQuery data access",
        instruction="""You are a helpful assistant that manages email communications for a cookie delivery service.
        You can access BigQuery data about orders and customers to personalize emails and notifications.
        Help with order confirmations, delivery updates, and customer service communications.
        
        Use BigQuery tools to:
        - Query customer order history
        - Check order statuses
        - Update order records
        - Generate personalized content based on customer data
        
        Focus on providing excellent customer service through data-driven communication.""",
        tools=[bigquery_toolset]
    )
    
    logger.info("✅ Email agent initialized successfully") 
    return agent

def calendar_agent():
    """Agent for calendar and scheduling management."""
    
    # Calendar MCP toolset connection using proper syntax
    server_params = StdioServerParameters(
        command="python",
        args=["calendar_mcp_server.py"],
        env={"PYTHONPATH": str(Path.cwd())}
    )
    
    calendar_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=server_params
        )
    )
    
    # Build agent with calendar capabilities
    agent = Agent(
        name="calendar_agent",
        model="gemini-2.0-flash-exp", 
        description="Manages calendar events and scheduling via MCP server",
        instruction="""You are a helpful assistant that manages calendar events and scheduling for a cookie delivery service.
        You can create, update, and query calendar events for delivery schedules, customer appointments, and team meetings.
        Help coordinate delivery times and manage the scheduling workflow.
        
        Use calendar tools to:
        - Check availability for delivery slots
        - Schedule new delivery appointments
        - Update existing delivery times
        - Manage team schedules and meetings
        
        Focus on optimizing delivery logistics and customer satisfaction.""",
        tools=[calendar_mcp]
    )
    
    logger.info("✅ Calendar agent initialized successfully")
    return agent

def workflow_agent():
    """Agent that orchestrates the entire delivery workflow."""
    
    # Initialize BigQuery toolset for comprehensive data access
    bigquery_toolset = get_bigquery_toolset()
    
    if bigquery_toolset is None:
        logger.error("Failed to initialize BigQuery toolset for workflow agent")
        return None
    
    # Calendar MCP toolset connection using proper syntax
    server_params = StdioServerParameters(
        command="python",
        args=["calendar_mcp_server.py"],
        env={"PYTHONPATH": str(Path.cwd())}
    )
    
    calendar_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=server_params
        )
    )
    
    # Build comprehensive workflow agent
    agent = Agent(
        name="workflow_agent",
        model="gemini-2.0-flash-exp",
        description="Master coordinator for cookie delivery workflow",
        instruction="""You are the master coordinator for a cookie delivery service workflow.
        You have access to both BigQuery for data management and calendar tools for scheduling.
        
        Your workflow process:
        1. Check for new orders in BigQuery
        2. Verify customer and order details
        3. Check delivery schedule availability
        4. Schedule delivery appointments
        5. Update order status in database
        6. Prepare customer communications
        
        You can handle the complete end-to-end process of order fulfillment.
        Always ensure data consistency and customer satisfaction.""",
        tools=[bigquery_toolset, calendar_mcp]
    )
    
    logger.info("✅ Workflow agent initialized successfully")
    return agent

# Main function for testing
if __name__ == "__main__":
    print("Testing ADK agent initialization...")
    
    # Test database agent
    db_agent = store_database_agent()
    if db_agent:
        print("✅ Database agent created successfully")
    else:
        print("❌ Database agent creation failed")
    
    # Test email agent
    email_agent = email_agent()
    if email_agent:
        print("✅ Email agent created successfully") 
    else:
        print("❌ Email agent creation failed")
    
    # Test calendar agent
    cal_agent = calendar_agent()
    if cal_agent:
        print("✅ Calendar agent created successfully")
    else:
        print("❌ Calendar agent creation failed")
    
    # Test workflow agent
    wf_agent = workflow_agent()
    if wf_agent:
        print("✅ Workflow agent created successfully")
    else:
        print("❌ Workflow agent creation failed")
