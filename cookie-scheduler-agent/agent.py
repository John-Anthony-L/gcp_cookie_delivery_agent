import os
import logging
import google.cloud.logging
from datetime import datetime

from callback_logging import log_query_to_model, log_model_response # Assuming this is a custom helper
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

# --- Setup and Configuration ---

# Set up cloud logging
try:
    cloud_logging_client = google.cloud.logging.Client()
    cloud_logging_client.setup_logging()
    logging.info("Google Cloud Logging initialized.")
except Exception as e:
    logging.warning(f"Could not initialize Google Cloud Logging: {e}. Using basic logging.")
    logging.basicConfig(level=logging.INFO)


# Load environment variables from a .env file
load_dotenv()
model_name = os.getenv("MODEL", "gemini-1.5-flash-001") # Default to a known model
logging.info(f"Using model: {model_name}")


# --- Dummy Data and Simulation Tools ---
# NOTE: In production, these will be replaced with:
# - BigQuery integration for orders (direct connection)
# - Google Calendar MCP server for scheduling (business account)
# - Gmail MCP server for email sending (business account)

# This dictionary simulates a BigQuery table structure for orders.
# Table: `cookie_delivery.orders`
DUMMY_ORDER_DATABASE = {
    "ORD12345": {
        "order_id": "ORD12345",
        "order_number": "ORD12345",
        "customer_email": "customer@example.com",
        "customer_name": "John Doe",
        "customer_phone": "+1-555-0123",
        "order_items": [
            {"item_name": "Chocolate Chip", "quantity": 12, "unit_price": 2.50},
            {"item_name": "Oatmeal Raisin", "quantity": 6, "unit_price": 2.75},
            {"item_name": "Snickerdoodle", "quantity": 12, "unit_price": 2.60}
        ],
        "delivery_address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "USA"
        },
        "delivery_location": "123 Main St, Anytown, CA 12345, USA",
        "delivery_request_date": "2025-09-10",
        "delivery_time_preference": "morning", # morning, afternoon, evening
        "order_status": "order_placed", # order_placed, confirmed, scheduled, in_delivery, delivered, cancelled
        "total_amount": 63.50,
        "order_date": "2025-09-04T10:30:00Z",
        "special_instructions": "Please ring doorbell twice",
        "created_at": "2025-09-04T10:30:00Z",
        "updated_at": "2025-09-04T10:30:00Z"
    }
}

# This dictionary simulates Google Calendar API responses.
# In production, this would come from business calendar via MCP server
DUMMY_CALENDAR = {
    "2025-09-08": [
        {
            "id": "evt_001",
            "summary": "Cookie Delivery - ORD12340",
            "description": "Delivery for John Smith - 2 dozen assorted cookies",
            "location": "456 Oak Ave, Springfield, CA",
            "start": {"dateTime": "2025-09-08T10:00:00-07:00"},
            "end": {"dateTime": "2025-09-08T10:30:00-07:00"},
            "status": "confirmed"
        }
    ],
    "2025-09-09": [
        {
            "id": "evt_002", 
            "summary": "Cookie Delivery - ORD12342",
            "description": "Delivery for Jane Doe - 1 dozen chocolate chip",
            "location": "789 Pine Ln, Springfield, CA",
            "start": {"dateTime": "2025-09-09T14:00:00-07:00"},
            "end": {"dateTime": "2025-09-09T14:30:00-07:00"},
            "status": "confirmed"
        }
    ]
}

def get_latest_order(tool_context: ToolContext) -> dict:
    """
    Fetches the most recent order with 'order_placed' status from the database.
    
    In production, this would:
    1. Connect to BigQuery using google-cloud-bigquery
    2. Query: SELECT * FROM `cookie_delivery.orders` 
             WHERE order_status = 'order_placed' 
             ORDER BY created_at DESC LIMIT 1
    3. Handle authentication and connection errors
    """
    logging.info("Tool: get_latest_order called.")
    
    # TODO: Replace with BigQuery integration
    # from google.cloud import bigquery
    # client = bigquery.Client()
    # query = """
    #     SELECT * FROM `cookie_delivery.orders` 
    #     WHERE order_status = 'order_placed' 
    #     ORDER BY created_at DESC LIMIT 1
    # """
    # result = client.query(query).to_dataframe()
    
    # Find the first order with status 'order_placed'
    for order_id, order_details in DUMMY_ORDER_DATABASE.items():
        if order_details["order_status"] == "order_placed":
            logging.info(f"Found latest order: {order_id}")
            # Save relevant details to the agent's state
            tool_context.state['order_details'] = order_details
            return order_details
    
    logging.warning("No new orders found with status 'order_placed'.")
    return {"status": "error", "message": "No new orders found with status 'order_placed'."}

def update_order_status(tool_context: ToolContext, order_number: str, new_status: str) -> dict:
    """
    Updates the status of a given order in the database.
    
    In production, this would:
    1. Connect to BigQuery
    2. Execute: UPDATE `cookie_delivery.orders` 
                SET order_status = @new_status, updated_at = CURRENT_TIMESTAMP()
                WHERE order_number = @order_number
    3. Return success/failure with affected rows count
    """
    logging.info(f"Tool: update_order_status called for {order_number} to set status {new_status}.")
    
    # TODO: Replace with BigQuery update
    # from google.cloud import bigquery
    # client = bigquery.Client()
    # query = """
    #     UPDATE `cookie_delivery.orders` 
    #     SET order_status = @new_status, updated_at = CURRENT_TIMESTAMP()
    #     WHERE order_number = @order_number
    # """
    # job_config = bigquery.QueryJobConfig(
    #     query_parameters=[
    #         bigquery.ScalarQueryParameter("new_status", "STRING", new_status),
    #         bigquery.ScalarQueryParameter("order_number", "STRING", order_number),
    #     ]
    # )
    # result = client.query(query, job_config=job_config)
    
    if order_number in DUMMY_ORDER_DATABASE:
        DUMMY_ORDER_DATABASE[order_number]["order_status"] = new_status
        DUMMY_ORDER_DATABASE[order_number]["updated_at"] = datetime.now().isoformat() + "Z"
        logging.info(f"Order {order_number} status updated to '{new_status}'.")
        # Log the final state for review
        print("--- FINAL DATABASE STATE ---")
        print(DUMMY_ORDER_DATABASE)
        return {"status": "success", "order_number": order_number, "new_status": new_status}
    else:
        logging.error(f"Order {order_number} not found in database.")
        return {"status": "error", "message": f"Order {order_number} not found."}

def get_delivery_schedule(tool_context: ToolContext) -> dict:
    """
    Fetches the current delivery schedule from Google Calendar.
    
    In production, this would:
    1. Connect to Google Calendar via MCP server (business account)
    2. Call calendar.events.list() for the delivery calendar
    3. Parse and return events for scheduling analysis
    """
    logging.info("Tool: get_delivery_schedule called.")
    
    # TODO: Replace with MCP server call to Google Calendar
    # This would be something like:
    # mcp_response = await mcp_client.call_tool(
    #     "calendar_get_events", 
    #     {
    #         "calendar_id": "deliveries@cookiebusiness.com",
    #         "time_min": "2025-09-01T00:00:00Z",
    #         "time_max": "2025-09-30T23:59:59Z"
    #     }
    # )
    
    tool_context.state['delivery_schedule'] = DUMMY_CALENDAR
    return DUMMY_CALENDAR

def schedule_delivery(tool_context: ToolContext, date: str, order_number: str, location: str, time_preference: str = "morning") -> dict:
    """
    Adds a new delivery event to the Google Calendar.
    
    In production, this would:
    1. Connect to Google Calendar via MCP server (business account)
    2. Create event with proper time slots based on preference
    3. Handle conflicts and availability checking
    4. Return calendar event ID for tracking
    """
    logging.info(f"Tool: schedule_delivery called for {order_number} on {date} ({time_preference}).")
    
    # TODO: Replace with MCP server call to Google Calendar
    # This would be something like:
    # time_slots = {
    #     "morning": {"start": "09:00:00", "end": "09:30:00"},
    #     "afternoon": {"start": "14:00:00", "end": "14:30:00"},
    #     "evening": {"start": "18:00:00", "end": "18:30:00"}
    # }
    # slot = time_slots.get(time_preference, time_slots["morning"])
    # 
    # mcp_response = await mcp_client.call_tool(
    #     "calendar_create_event",
    #     {
    #         "calendar_id": "deliveries@cookiebusiness.com",
    #         "summary": f"Cookie Delivery - {order_number}",
    #         "location": location,
    #         "start": f"{date}T{slot['start']}-07:00",
    #         "end": f"{date}T{slot['end']}-07:00",
    #         "description": f"Delivery for order {order_number}"
    #     }
    # )
    
    # Get order details for the event
    order_details = tool_context.state.get('order_details', {})
    customer_name = order_details.get('customer_name', 'Customer')
    
    # Map time preferences to actual times
    time_slots = {
        "morning": {"start": "09:00:00-07:00", "end": "09:30:00-07:00"},
        "afternoon": {"start": "14:00:00-07:00", "end": "14:30:00-07:00"},
        "evening": {"start": "18:00:00-07:00", "end": "18:30:00-07:00"}
    }
    slot = time_slots.get(time_preference, time_slots["morning"])
    
    event = {
        "id": f"evt_{order_number}",
        "summary": f"Cookie Delivery - {order_number}",
        "description": f"Delivery for {customer_name} - Order {order_number}",
        "location": location,
        "start": {"dateTime": f"{date}T{slot['start']}"},
        "end": {"dateTime": f"{date}T{slot['end']}"},
        "status": "confirmed"
    }
    
    if date in DUMMY_CALENDAR:
        DUMMY_CALENDAR[date].append(event)
    else:
        DUMMY_CALENDAR[date] = [event]
    
    logging.info(f"Delivery for {order_number} scheduled on {date} at {time_preference}.")
    # Log the final state for review
    print("--- FINAL CALENDAR STATE ---")
    print(DUMMY_CALENDAR)
    return {"status": "success", "date": date, "event": event, "event_id": event["id"]}

def send_confirmation_email(tool_context: ToolContext, recipient_email: str, subject: str, body: str) -> dict:
    """
    Sends an email to the customer via Gmail.
    
    In production, this would:
    1. Connect to Gmail via MCP server (business account: deliveries@cookiebusiness.com)
    2. Compose and send email with proper formatting
    3. Handle authentication and delivery status
    4. Return message ID for tracking
    """
    logging.info(f"Tool: send_confirmation_email called for {recipient_email}.")
    
    # TODO: Replace with MCP server call to Gmail
    # This would be something like:
    # mcp_response = await mcp_client.call_tool(
    #     "gmail_send_email",
    #     {
    #         "to": recipient_email,
    #         "from": "deliveries@cookiebusiness.com",
    #         "subject": subject,
    #         "body": body,
    #         "body_type": "html"  # or "plain"
    #     }
    # )
    
    email_content = f"""
    --- SENDING EMAIL VIA GMAIL MCP SERVER ---
    From: deliveries@cookiebusiness.com
    To: {recipient_email}
    Subject: {subject}
    ---
    {body}
    ---------------------
    """
    # Print the email to the console for verification
    print(email_content)
    logging.info("Email sent successfully via Gmail MCP server (simulated).")
    return {
        "status": "success", 
        "recipient": recipient_email,
        "message_id": f"msg_{recipient_email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

def save_delivery_month(tool_context: ToolContext, date_string: str) -> dict:
    """
    Calculates the month name from a date string (YYYY-MM-DD)
    and saves it to the state.
    """
    logging.info(f"Tool: save_delivery_month called for {date_string}.")
    try:
        # Parse the date string and get the full name of the month
        month_name = datetime.strptime(date_string, "%Y-%m-%d").strftime('%B')
        tool_context.state['delivery_month'] = month_name
        logging.info(f"Saved 'delivery_month' to state: {month_name}")
        return {"status": "success", "delivery_month": month_name}
    except ValueError as e:
        logging.error(f"Error parsing date string: {e}")
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}
    
# --- AGENT DEFINITIONS ---

## Database Agent
# This agent's responsibility is to fetch order data from BigQuery.
store_database_agent = Agent(
    name="store_database_agent",
    model=model_name,
    description="Responsible for getting and updating the BigQuery database for orders.",
    instruction="""
    You are the order manager with access to the BigQuery orders database. 
    Your primary job is to fetch the latest order from the database that has the status 'order_placed'. 
    Use the 'get_latest_order' tool to accomplish this.
    
    The order details will be automatically saved to the state for other agents to use.
    Make sure to handle any database connection errors gracefully.
    """,
    tools=[get_latest_order],
)
## Calendar Agent
# This agent checks for availability and schedules the delivery via Google Calendar MCP.
calendar_agent = Agent(
    name="calendar_agent",
    model=model_name,
    description="Responsible for getting and updating the delivery schedule via Google Calendar MCP server.",
    instruction="""
    You are the logistics coordinator with access to the business Google Calendar via MCP server.
    Your task is to schedule the new cookie delivery.

    1.  **Fetch Schedule**: Use the `get_delivery_schedule` tool to get the current calendar from the business account.
    2.  **Determine Delivery Month**: Use the `save_delivery_month` tool with the requested delivery date ({order_details.delivery_request_date}) to find out the delivery month and save it for the next agent.
    3.  **Check Availability**: Review the schedule. Confirm if the requested delivery date is free for the customer's time preference ({order_details.delivery_time_preference}).
    4.  **Schedule Delivery**: If the date/time is available, use the `schedule_delivery` tool to add the delivery to the calendar. 
        - Use the order number ({order_details.order_number})
        - Use the delivery location ({order_details.delivery_location})
        - Use the time preference ({order_details.delivery_time_preference})
        
    Handle any calendar conflicts by suggesting alternative times if needed.
    """,
    tools=[get_delivery_schedule, schedule_delivery, save_delivery_month],
)

## Haiku Writer Sub-Agent
# A specialized agent for creative writing, used as a sub-agent by the emailer.
haiku_writer_agent = Agent(
    name="haiku_writer_agent",
    model=model_name,
    description="A creative agent that writes haikus.",
    instruction="""
    You are a poet. You will be given a delivery month and a list of cookie types from the order items.
    Write a beautiful and creative 5-7-5 syllable haiku that captures the feeling of that month and the cookies being delivered.
    Return only the haiku text.

    ORDER ITEMS: {order_details.order_items}
    DELIVERY MONTH: {delivery_month}
    """,
    output_key="haiku_text"
)

## Email Agent
# This agent handles all customer communication via Gmail MCP server and finalizes the order status.
email_agent = Agent(
    name="email_agent",
    model=model_name,
    description="Writes and sends emails via Gmail MCP server, and finalizes the order status in BigQuery.",
    instruction="""
    You are the customer communication specialist with access to the business Gmail account via MCP server. 
    Your multi-step task is to confirm the delivery and update the order status.

    1.  **Generate Haiku**: Delegate to your `haiku_writer_agent` to generate a haiku based on the delivery month ({delivery_month}) and the order items ({order_details.order_items}).

    2.  **Send Email**: Use the `send_confirmation_email` tool to send via the business Gmail account (deliveries@cookiebusiness.com). 
        - Send to: {order_details.customer_email}
        - Subject: "Your Cookie Delivery is Scheduled!"
        - Body: Include a personalized confirmation message with:
          * Customer name ({order_details.customer_name})
          * Delivery date and time
          * Order details
          * The generated haiku
          * Business contact information

    3.  **Update Status**: After the email is sent successfully, use the `update_order_status` tool to change the order status to 'scheduled' in BigQuery.
        Use the order number: {order_details.order_number}.
    """,
    sub_agents=[haiku_writer_agent],
    tools=[send_confirmation_email, update_order_status],
)


# --- SEQUENTIAL WORKFLOW AGENT ---
# This agent orchestrates the sub-agents in a specific order.
delivery_workflow_agent = SequentialAgent(
    name="delivery_workflow_agent",
    description="Manages the entire cookie delivery process from order to confirmation.",
    sub_agents=[
        store_database_agent,
        calendar_agent,
        email_agent
    ],
)

# --- ROOT AGENT ---
# The main entry point for the entire workflow.
root_agent = Agent(
    name="root_agent",
    model=model_name,
    description="The main agent that kicks off the cookie delivery workflow.",
    instruction="""
    You are the manager of a delightful cookie delivery service.
    Your goal is to process the latest incoming order.
    - Ask the user if they would like to kick off the cookie service for the week.
    - if they do, Start the process by transferring control to the 'delivery_workflow_agent'.
    """,
    sub_agents=[delivery_workflow_agent],
)