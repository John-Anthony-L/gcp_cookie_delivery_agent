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

# This dictionary simulates a SQL database table for orders.
# In a real application, the tools would make actual SQL/BigQuery calls.
DUMMY_ORDER_DATABASE = {
    "ORD12345": {
        "order_number": "ORD12345",
        "customer_email": "customer@example.com",
        "order_items": ["Chocolate Chip", "Oatmeal Raisin", "Snickerdoodle"],
        "delivery_location": "123 Main St, Anytown, USA",
        "delivery_request_date": "2025-09-10",
        "order_status": "order made"
    }
}

# This dictionary simulates a Google Calendar.
# Keys are dates (YYYY-MM-DD), and values are lists of scheduled events.
DUMMY_CALENDAR = {
    "2025-09-08": [{"summary": "Delivery for ORD12340", "location": "456 Oak Ave"}],
    "2025-09-09": [{"summary": "Delivery for ORD12342", "location": "789 Pine Ln"}]
}

def get_latest_order(tool_context: ToolContext) -> dict:
    """
    Fetches the most recent order with 'order made' status from the database.
    This is a simulation; in a real-world scenario, this would query a SQL
    database or BigQuery.
    """
    logging.info("Tool: get_latest_order called.")
    # Find the first order with status 'order made'
    for order_id, order_details in DUMMY_ORDER_DATABASE.items():
        if order_details["order_status"] == "order made":
            logging.info(f"Found latest order: {order_id}")
            # Save relevant details to the agent's state
            tool_context.state['order_details'] = order_details
            return order_details
    logging.warning("No new orders found.")
    return {"status": "error", "message": "No new orders found."}

def update_order_status(tool_context: ToolContext, order_number: str, new_status: str) -> dict:
    """
    Updates the status of a given order in the database.
    This is a simulation.
    """
    logging.info(f"Tool: update_order_status called for {order_number} to set status {new_status}.")
    if order_number in DUMMY_ORDER_DATABASE:
        DUMMY_ORDER_DATABASE[order_number]["order_status"] = new_status
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
    Fetches the current delivery schedule.
    This simulates fetching events from a Google Calendar API.
    """
    logging.info("Tool: get_delivery_schedule called.")
    tool_context.state['delivery_schedule'] = DUMMY_CALENDAR
    return DUMMY_CALENDAR

def schedule_delivery(tool_context: ToolContext, date: str, order_number: str, location: str) -> dict:
    """
    Adds a new delivery event to the calendar.
    This simulates creating an event using the Google Calendar API.
    """
    logging.info(f"Tool: schedule_delivery called for {order_number} on {date}.")
    event = {"summary": f"Delivery for {order_number}", "location": location}
    if date in DUMMY_CALENDAR:
        DUMMY_CALENDAR[date].append(event)
    else:
        DUMMY_CALENDAR[date] = [event]
    logging.info(f"Delivery for {order_number} scheduled on {date}.")
    # Log the final state for review
    print("--- FINAL CALENDAR STATE ---")
    print(DUMMY_CALENDAR)
    return {"status": "success", "date": date, "event": event}

def send_confirmation_email(tool_context: ToolContext, recipient_email: str, subject: str, body: str) -> dict:
    """
    Sends an email to the customer.
    This is a simulation; it prints the email content instead of sending it.
    """
    logging.info(f"Tool: send_confirmation_email called for {recipient_email}.")
    email_content = f"""
    --- SENDING EMAIL ---
    To: {recipient_email}
    Subject: {subject}
    ---
    {body}
    ---------------------
    """
    # Print the email to the console for verification
    print(email_content)
    logging.info("Email sent successfully (simulated).")
    return {"status": "success", "recipient": recipient_email}

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
# This agent's responsibility is to fetch order data.
store_database_agent = Agent(
    name="store_database_agent",
    model=model_name,
    description="Responsible for getting and updating the SQL database for orders.",
    instruction="""
    You are the order manager. Your first and only job is to fetch the latest order from the database
    that has the status 'order made'. Use the 'get_latest_order' tool to accomplish this.
    The order details will be automatically saved to the state for other agents to use.
    """,
    tools=[get_latest_order],
)
## Calendar Agent
# This agent checks for availability and schedules the delivery.
calendar_agent = Agent(
    name="calendar_agent",
    model=model_name,
    description="Responsible for getting and updating the delivery schedule.",
    instruction="""
    You are the logistics coordinator. Your task is to schedule the new cookie delivery.

    1.  **Fetch Schedule**: Use the `get_delivery_schedule` tool to get the current calendar.
    2.  **Determine Delivery Month**: Use the `save_delivery_month` tool with the requested delivery date ({order_details.delivery_request_date}) to find out the delivery month and save it for the next agent.
    3.  **Check Availability**: Review the schedule. Confirm if the requested delivery date is free.
    4.  **Schedule Delivery**: If the date is available, use the `schedule_delivery` tool to add the delivery to the calendar. Use the order number ({order_details.order_number}) and delivery location ({order_details.delivery_location}) for the event details.
    """,
    tools=[get_delivery_schedule, schedule_delivery, save_delivery_month], # <-- TOOL REPLACED HERE
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
# This agent handles all customer communication, including scheduling and status updates.
email_agent = Agent(
    name="email_agent",
    model=model_name,
    description="Writes and sends emails, and finalizes the order status.",
    instruction="""
    You are the customer communication specialist. Your multi-step task is to confirm the delivery.

    1.  **Generate Haiku**: Delegate to your `haiku_writer_agent` to generate a haiku based on the delivery month ({delivery_month}) and the order items ({order_details.order_items}).

    2.  **Send Email**: Use the `send_confirmation_email` tool. The email should be sent to the customer's email ({order_details.customer_email}).
        The subject should be "Your Cookie Delivery is Scheduled!".
        The body must include a confirmation message with the delivery date and the haiku you generated.

    3.  **Update Status**: After the email is sent, use the `update_order_status` tool to change the order status to 'delivery scheduled'.
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