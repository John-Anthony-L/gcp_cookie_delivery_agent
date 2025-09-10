import os
import sys
import logging
import google.cloud.logging
from datetime import datetime, timedelta

# Import callback logging from parent directory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from callback_logging import log_query_to_model, log_model_response # Assuming this is a custom helper
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

try:
    from .dummy_data import DUMMY_ORDER_DATABASE, DUMMY_CALENDAR # our dummy data for testing
except ImportError:
    # Fallback for direct execution
    from dummy_data import DUMMY_ORDER_DATABASE, DUMMY_CALENDAR

# Calendar MCP Integration Setup
calendar_mcp_path = os.path.join(os.path.dirname(__file__), 'mcp-servers', 'calendar')
sys.path.append(calendar_mcp_path)

# Import Calendar MCP Manager
try:
    from calendar_mcp_server import CalendarManager
    calendar_manager = CalendarManager()
    CALENDAR_MCP_AVAILABLE = calendar_manager.service is not None
    logging.info("Calendar MCP: Successfully connected to Google Calendar")
except ImportError as e:
    logging.warning(f"Calendar MCP not available: {e}")
    calendar_manager = None
    CALENDAR_MCP_AVAILABLE = False
except Exception as e:
    logging.warning(f"Calendar MCP authentication failed: {e}")
    calendar_manager = None
    CALENDAR_MCP_AVAILABLE = False

# Import BigQuery tools
try:
    from bigquery_tools import get_latest_order_from_bigquery, update_order_status_in_bigquery
    BIGQUERY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"BigQuery tools not available: {e}")
    BIGQUERY_AVAILABLE = False

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
model_name = os.getenv("MODEL", "gemini-2.5-flash")
use_bigquery = os.getenv("USE_BIGQUERY", "false").lower() == "true"
use_calendar_mcp = os.getenv("USE_CALENDAR_MCP", "false").lower() == "true"
business_calendar_id = os.getenv("BUSINESS_CALENDAR_ID", "primary")

logging.info(f"Using model: {model_name}")
logging.info(f"BigQuery integration: {'enabled' if use_bigquery and BIGQUERY_AVAILABLE else 'disabled (using dummy data)'}")
logging.info(f"Calendar MCP integration: {'enabled' if use_calendar_mcp and CALENDAR_MCP_AVAILABLE else 'disabled (using dummy data)'}")


def get_latest_order(tool_context: ToolContext) -> dict:
    """
    Fetches the most recent order with 'order_placed' status from the database.
    Uses BigQuery if enabled, otherwise uses dummy data.
    """
    logging.info("Tool: get_latest_order called.")
    
    # Use BigQuery if available and enabled
    if use_bigquery and BIGQUERY_AVAILABLE:
        import asyncio
        return asyncio.run(get_latest_order_from_bigquery(tool_context))
    
    # Fallback to dummy data
    logging.info("Using dummy data for order retrieval")
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
    Uses BigQuery if enabled, otherwise uses dummy data.
    """
    logging.info(f"Tool: update_order_status called for {order_number} to set status {new_status}.")
    
    # Use BigQuery if available and enabled
    if use_bigquery and BIGQUERY_AVAILABLE:
        import asyncio
        return asyncio.run(update_order_status_in_bigquery(tool_context, order_number, new_status))
    
    # Fallback to dummy data
    logging.info("Using dummy data for order status update")
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
    
    Uses real Google Calendar MCP server if available, otherwise falls back to dummy data.
    """
    logging.info("Tool: get_delivery_schedule called.")
    
    # Use Calendar MCP if available and enabled
    if use_calendar_mcp and CALENDAR_MCP_AVAILABLE and calendar_manager:
        try:
            # Get events for the next 30 days to see current delivery schedule
            now = datetime.now()
            month_later = now + timedelta(days=30)
            
            time_min = now.isoformat() + "Z"
            time_max = month_later.isoformat() + "Z"
            
            logging.info(f"Calendar MCP: Fetching events from {time_min} to {time_max}")
            
            # Call the real Calendar MCP server
            calendar_result = calendar_manager.get_events(
                time_min=time_min,
                time_max=time_max,
                calendar_id=business_calendar_id
            )
            
            if calendar_result["status"] == "success":
                # Transform the calendar events into the format expected by the agent
                delivery_schedule = {}
                
                for event in calendar_result["events"]:
                    # Extract date from event start time
                    start_datetime = event["start"]
                    if "T" in start_datetime:
                        event_date = start_datetime.split("T")[0]  # Get YYYY-MM-DD format
                    else:
                        event_date = start_datetime
                    
                    # Add event to the schedule grouped by date
                    if event_date not in delivery_schedule:
                        delivery_schedule[event_date] = []
                    
                    delivery_schedule[event_date].append({
                        "id": event["id"],
                        "summary": event["summary"],
                        "description": event["description"],
                        "location": event["location"],
                        "start": {"dateTime": event["start"]},
                        "end": {"dateTime": event["end"]},
                        "status": event["status"]
                    })
                
                logging.info(f"Calendar MCP: Successfully retrieved {calendar_result['count']} events")
                tool_context.state['delivery_schedule'] = delivery_schedule
                tool_context.state['calendar_source'] = 'real_calendar_mcp'
                return {
                    "status": "success",
                    "schedule": delivery_schedule,
                    "total_events": calendar_result['count'],
                    "source": "Google Calendar MCP"
                }
                
            else:
                logging.error(f"Calendar MCP error: {calendar_result.get('message', 'Unknown error')}")
                # Fall back to dummy data
                tool_context.state['delivery_schedule'] = DUMMY_CALENDAR
                tool_context.state['calendar_source'] = 'dummy_fallback'
                return DUMMY_CALENDAR
                
        except Exception as e:
            logging.error(f"Calendar MCP unexpected error: {e}")
            # Fall back to dummy data
            tool_context.state['delivery_schedule'] = DUMMY_CALENDAR
            tool_context.state['calendar_source'] = 'dummy_fallback'
            return DUMMY_CALENDAR
    
    # Fallback to dummy data if MCP not available
    logging.info("Using dummy data for delivery schedule (Calendar MCP not available)")
    tool_context.state['delivery_schedule'] = DUMMY_CALENDAR
    tool_context.state['calendar_source'] = 'dummy_data'
    return DUMMY_CALENDAR

def schedule_delivery(tool_context: ToolContext, date: str, order_number: str, location: str, time_preference: str = "morning") -> dict:
    """
    Adds a new delivery event to the Google Calendar.
    
    Uses real Google Calendar MCP server if available, otherwise falls back to dummy data.
    """
    logging.info(f"Tool: schedule_delivery called for {order_number} on {date} ({time_preference}).")
    
    # Get order details for the event
    order_details = tool_context.state.get('order_details', {})
    customer_name = order_details.get('customer_name', 'Customer')
    customer_email = order_details.get('customer_email', '')
    order_items = order_details.get('order_items', [])
    
    # Map time preferences to actual times (using RFC3339 format for Google Calendar)
    time_slots = {
        "morning": {"start": "09:00:00", "end": "09:30:00"},
        "afternoon": {"start": "14:00:00", "end": "14:30:00"},
        "evening": {"start": "18:00:00", "end": "18:30:00"}
    }
    slot = time_slots.get(time_preference, time_slots["morning"])
    
    # Create RFC3339 formatted datetime strings for Google Calendar
    start_datetime = f"{date}T{slot['start']}Z"
    end_datetime = f"{date}T{slot['end']}Z"
    
    # Use Calendar MCP if available and enabled
    if use_calendar_mcp and CALENDAR_MCP_AVAILABLE and calendar_manager:
        try:
            # First check availability for the requested time slot
            logging.info(f"Calendar MCP: Checking availability for {start_datetime} to {end_datetime}")
            
            availability_result = calendar_manager.check_availability(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                calendar_id=business_calendar_id
            )
            
            if availability_result["status"] == "success":
                if not availability_result["available"]:
                    # Handle conflicts by suggesting alternative or noting the conflict
                    conflicts = availability_result.get("conflicts", [])
                    logging.warning(f"Calendar MCP: Time slot has {len(conflicts)} conflicts")
                    
                    # For now, we'll still create the event but note the conflicts
                    # In production, you might want to suggest alternative times
                
                # Create the event description with order details
                event_description = f"""🍪 Cookie Delivery for {customer_name}

Order Number: {order_number}
Customer Email: {customer_email}
Items: {', '.join([item.get('name', 'Cookie') for item in order_items]) if order_items else 'Delicious Cookies'}

Delivery Instructions: Please ring doorbell and confirm delivery.

This event was created automatically by the Cookie Delivery Agent.
"""
                
                # Create the event using Calendar MCP
                logging.info(f"Calendar MCP: Creating event for {order_number}")
                
                create_result = calendar_manager.create_event(
                    summary=f"🍪 Cookie Delivery - {order_number}",
                    description=event_description,
                    location=location,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    calendar_id=business_calendar_id
                )
                
                if create_result["status"] == "success":
                    logging.info(f"Calendar MCP: Successfully created event {create_result['event_id']}")
                    
                    # Update the delivery schedule in state if it exists
                    delivery_schedule = tool_context.state.get('delivery_schedule', {})
                    event_data = {
                        "id": create_result["event_id"],
                        "summary": f"🍪 Cookie Delivery - {order_number}",
                        "description": event_description,
                        "location": location,
                        "start": {"dateTime": start_datetime},
                        "end": {"dateTime": end_datetime},
                        "status": "confirmed"
                    }
                    
                    if date in delivery_schedule:
                        delivery_schedule[date].append(event_data)
                    else:
                        delivery_schedule[date] = [event_data]
                    
                    tool_context.state['delivery_schedule'] = delivery_schedule
                    
                    return {
                        "status": "success",
                        "date": date,
                        "event_id": create_result["event_id"],
                        "event_link": create_result.get("event_link"),
                        "summary": f"🍪 Cookie Delivery - {order_number}",
                        "start_time": start_datetime,
                        "end_time": end_datetime,
                        "location": location,
                        "source": "Google Calendar MCP",
                        "conflicts": availability_result.get("conflicts", [])
                    }
                else:
                    logging.error(f"Calendar MCP: Failed to create event: {create_result.get('message', 'Unknown error')}")
                    # Fall back to dummy data behavior
            else:
                logging.error(f"Calendar MCP: Failed to check availability: {availability_result.get('message', 'Unknown error')}")
                # Fall back to dummy data behavior
                
        except Exception as e:
            logging.error(f"Calendar MCP unexpected error during scheduling: {e}")
            # Fall back to dummy data behavior
    
    # Fallback to dummy data behavior (original implementation)
    logging.info("Using dummy data for delivery scheduling (Calendar MCP not available)")
    
    event = {
        "id": f"evt_{order_number}",
        "summary": f"Cookie Delivery - {order_number}",
        "description": f"Delivery for {customer_name} - Order {order_number}",
        "location": location,
        "start": {"dateTime": f"{date}T{slot['start']}-07:00"},
        "end": {"dateTime": f"{date}T{slot['end']}-07:00"},
        "status": "confirmed"
    }
    
    if date in DUMMY_CALENDAR:
        DUMMY_CALENDAR[date].append(event)
    else:
        DUMMY_CALENDAR[date] = [event]
    
    logging.info(f"Delivery for {order_number} scheduled on {date} at {time_preference} (using dummy data).")
    # Log the final state for review
    print("--- FINAL CALENDAR STATE (DUMMY DATA) ---")
    print(DUMMY_CALENDAR)
    return {"status": "success", "date": date, "event": event, "event_id": event["id"], "source": "dummy_data"}

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

def check_delivery_availability(tool_context: ToolContext, date: str, time_preference: str = "morning") -> dict:
    """
    Checks if a specific date and time preference is available for delivery.
    
    Uses real Google Calendar MCP server if available, otherwise uses dummy data logic.
    """
    logging.info(f"Tool: check_delivery_availability called for {date} ({time_preference}).")
    
    # Map time preferences to time slots
    time_slots = {
        "morning": {"start": "09:00:00", "end": "09:30:00"},
        "afternoon": {"start": "14:00:00", "end": "14:30:00"},
        "evening": {"start": "18:00:00", "end": "18:30:00"}
    }
    slot = time_slots.get(time_preference, time_slots["morning"])
    
    # Create RFC3339 formatted datetime strings
    start_datetime = f"{date}T{slot['start']}Z"
    end_datetime = f"{date}T{slot['end']}Z"
    
    # Use Calendar MCP if available and enabled
    if use_calendar_mcp and CALENDAR_MCP_AVAILABLE and calendar_manager:
        try:
            logging.info(f"Calendar MCP: Checking availability for {start_datetime} to {end_datetime}")
            
            availability_result = calendar_manager.check_availability(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                calendar_id=business_calendar_id
            )
            
            if availability_result["status"] == "success":
                return {
                    "status": "success",
                    "available": availability_result["available"],
                    "conflicts": availability_result.get("conflicts", []),
                    "requested_date": date,
                    "requested_time": time_preference,
                    "time_slot": f"{slot['start']} - {slot['end']}",
                    "source": "Google Calendar MCP"
                }
            else:
                logging.error(f"Calendar MCP availability check failed: {availability_result.get('message')}")
                
        except Exception as e:
            logging.error(f"Calendar MCP availability check error: {e}")
    
    # Fallback to dummy data logic
    logging.info("Using dummy data for availability check")
    delivery_schedule = tool_context.state.get('delivery_schedule', DUMMY_CALENDAR)
    
    # Check if the date has any conflicts in dummy data
    date_events = delivery_schedule.get(date, [])
    conflicts = []
    
    for event in date_events:
        # Simple conflict detection based on summary content
        if "delivery" in event.get("summary", "").lower():
            conflicts.append({
                "summary": event.get("summary", "Existing Event"),
                "start": event.get("start", {}).get("dateTime", ""),
                "end": event.get("end", {}).get("dateTime", "")
            })
    
    is_available = len(conflicts) == 0
    
    return {
        "status": "success",
        "available": is_available,
        "conflicts": conflicts,
        "requested_date": date,
        "requested_time": time_preference,
        "time_slot": f"{slot['start']} - {slot['end']}",
        "source": "dummy_data"
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
    instruction=f"""
    You are the logistics coordinator with access to the business Google Calendar {'via MCP server' if use_calendar_mcp and CALENDAR_MCP_AVAILABLE else '(using dummy data)'}.
    Your task is to schedule the new cookie delivery.

    **Calendar Integration Status**: {'✅ Real Google Calendar MCP Connected' if use_calendar_mcp and CALENDAR_MCP_AVAILABLE else '⚠️ Using Dummy Data (MCP not available)'}

    1.  **Fetch Schedule**: Use the `get_delivery_schedule` tool to get the current calendar from the business account.
    2.  **Determine Delivery Month**: Use the `save_delivery_month` tool with the requested delivery date from the order details in state to find out the delivery month and save it for the next agent.
    3.  **Check Availability**: Use the `check_delivery_availability` tool to verify if the requested delivery date and time preference are available.
    4.  **Schedule Delivery**: If the date/time is available, use the `schedule_delivery` tool to add the delivery to the calendar. 
        - Use the order number from the order details in state
        - Use the delivery location from the order details in state  
        - Use the time preference from the order details in state
        
    **Important**: If using real Google Calendar MCP, the events will be created in the actual Google Calendar. 
    Handle any calendar conflicts by noting them in your response and still proceeding with scheduling if requested.
    
    **Note**: All order information will be available in the agent state from the previous database agent step.
    """,
    tools=[get_delivery_schedule, check_delivery_availability, schedule_delivery, save_delivery_month],
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

    Use the order_details and delivery_month from the agent state to create your haiku.
    Focus on the seasonal feeling of the delivery month and the joy of cookie delivery.
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

    1.  **Generate Haiku**: Delegate to your `haiku_writer_agent` to generate a haiku based on the delivery month and the order items from the state.

    2.  **Update Status**: use the `update_order_status` tool to change the order status to 'scheduled' in BigQuery.
        Use the order number from the state.

    3.  **Send Email**: Use the `send_confirmation_email` tool to send via the business Gmail account (deliveries@cookiebusiness.com). 
        - Send to the customer email from the state
        - Subject: "Your Cookie Delivery is Scheduled!"
        - Body: Include a personalized confirmation message with:
          * Customer name from the state
          * Delivery date and time from the scheduling results
          * Order details from the state
          * The generated haiku
          * Business contact information

    **Note**: All necessary information (order_details, delivery_month) will be available in the agent state from previous steps.
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
    
    WORKFLOW:
    1. First, greet the user and ask if they would like to kick off the cookie service for the week.
    2. If they say yes, start the process by transferring control to the 'delivery_workflow_agent'.
    3. Once the delivery workflow is complete, thank the user and summarize what was accomplished.
    4. DO NOT ask to restart the process unless the user explicitly requests it.
    5. If the user asks to process another order, then you can restart the workflow.
    
    Remember: Only run the workflow ONCE per user request, then wait for further instructions.
    """,
    sub_agents=[delivery_workflow_agent],
)