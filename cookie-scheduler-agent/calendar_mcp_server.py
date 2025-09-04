"""
MCP Server for Google Calendar integration.
This MCP server exposes Google Calendar operations for the cookie delivery business calendar.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List
from datetime import datetime, timedelta

from dotenv import load_dotenv

# MCP Server Imports
from mcp import types as mcp_types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Google Calendar API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    logging.error("Calendar API dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

load_dotenv()

# Calendar API Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
BUSINESS_CALENDAR_ID = os.getenv('BUSINESS_CALENDAR_ID', 'primary')  # or specific calendar ID

class CalendarManager:
    """Manages Google Calendar API operations for the business calendar."""
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google Calendar API using OAuth2."""
        creds = None
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists('calendar_token.json'):
            creds = Credentials.from_authorized_user_file('calendar_token.json', SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'calendar_credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('calendar_token.json', 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            logging.info("Calendar API authenticated successfully")
        except HttpError as error:
            logging.error(f"Calendar API authentication failed: {error}")
    
    def get_events(self, time_min: str, time_max: str, calendar_id: str = None) -> Dict:
        """Get events from the calendar within a time range."""
        try:
            calendar_id = calendar_id or BUSINESS_CALENDAR_ID
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events for easier processing
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'start': start,
                    'end': end,
                    'status': event.get('status', 'confirmed')
                })
            
            return {
                "status": "success",
                "events": formatted_events,
                "count": len(formatted_events)
            }
            
        except HttpError as error:
            logging.error(f"Calendar API error getting events: {error}")
            return {
                "status": "error",
                "message": f"Failed to get events: {str(error)}"
            }
    
    def create_event(self, summary: str, description: str, location: str, 
                    start_datetime: str, end_datetime: str, calendar_id: str = None) -> Dict:
        """Create a new event in the calendar."""
        try:
            calendar_id = calendar_id or BUSINESS_CALENDAR_ID
            
            event = {
                'summary': summary,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': 'America/Los_Angeles',  # Adjust timezone as needed
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': 'America/Los_Angeles',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 60},       # 1 hour before
                    ],
                },
            }
            
            created_event = self.service.events().insert(
                calendarId=calendar_id, body=event).execute()
            
            logging.info(f"Event created: {created_event['id']}")
            return {
                "status": "success",
                "event_id": created_event['id'],
                "event_link": created_event.get('htmlLink'),
                "summary": summary,
                "start": start_datetime,
                "end": end_datetime
            }
            
        except HttpError as error:
            logging.error(f"Calendar API error creating event: {error}")
            return {
                "status": "error",
                "message": f"Failed to create event: {str(error)}"
            }
    
    def check_availability(self, start_datetime: str, end_datetime: str, 
                          calendar_id: str = None) -> Dict:
        """Check if a time slot is available (no conflicting events)."""
        try:
            calendar_id = calendar_id or BUSINESS_CALENDAR_ID
            
            # Get events in the requested time range
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_datetime,
                timeMax=end_datetime,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            conflicts = []
            
            for event in events:
                # Check if event actually conflicts (not just touches)
                event_start = event['start'].get('dateTime', event['start'].get('date'))
                event_end = event['end'].get('dateTime', event['end'].get('date'))
                
                conflicts.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'Busy'),
                    'start': event_start,
                    'end': event_end
                })
            
            is_available = len(conflicts) == 0
            
            return {
                "status": "success",
                "available": is_available,
                "conflicts": conflicts,
                "requested_start": start_datetime,
                "requested_end": end_datetime
            }
            
        except HttpError as error:
            logging.error(f"Calendar API error checking availability: {error}")
            return {
                "status": "error",
                "message": f"Failed to check availability: {str(error)}"
            }
    
    def update_event(self, event_id: str, updates: Dict, calendar_id: str = None) -> Dict:
        """Update an existing event."""
        try:
            calendar_id = calendar_id or BUSINESS_CALENDAR_ID
            
            # First get the existing event
            event = self.service.events().get(
                calendarId=calendar_id, eventId=event_id).execute()
            
            # Apply updates
            for key, value in updates.items():
                event[key] = value
            
            updated_event = self.service.events().update(
                calendarId=calendar_id, eventId=event_id, body=event).execute()
            
            return {
                "status": "success",
                "event_id": updated_event['id'],
                "updated_fields": list(updates.keys())
            }
            
        except HttpError as error:
            logging.error(f"Calendar API error updating event: {error}")
            return {
                "status": "error",
                "message": f"Failed to update event: {str(error)}"
            }

# Initialize Calendar manager
calendar_manager = CalendarManager()

# MCP Server Setup
app = Server("calendar-mcp-server")

@app.list_tools()
async def list_tools() -> List[mcp_types.Tool]:
    """List available Calendar tools."""
    return [
        mcp_types.Tool(
            name="get_events",
            description="Get events from the business calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "description": "Start time in RFC3339 format (e.g., '2025-09-01T00:00:00Z')"
                    },
                    "time_max": {
                        "type": "string",
                        "description": "End time in RFC3339 format (e.g., '2025-09-30T23:59:59Z')"
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (optional, uses business calendar by default)"
                    }
                },
                "required": ["time_min", "time_max"]
            }
        ),
        mcp_types.Tool(
            name="create_event",
            description="Create a new event in the business calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title/summary"
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description"
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location"
                    },
                    "start_datetime": {
                        "type": "string",
                        "description": "Start time in RFC3339 format"
                    },
                    "end_datetime": {
                        "type": "string",
                        "description": "End time in RFC3339 format"
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (optional)"
                    }
                },
                "required": ["summary", "start_datetime", "end_datetime"]
            }
        ),
        mcp_types.Tool(
            name="check_availability",
            description="Check if a time slot is available",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_datetime": {
                        "type": "string",
                        "description": "Start time in RFC3339 format"
                    },
                    "end_datetime": {
                        "type": "string",
                        "description": "End time in RFC3339 format"
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID (optional)"
                    }
                },
                "required": ["start_datetime", "end_datetime"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[mcp_types.Content]:
    """Execute Calendar tools."""
    logging.info(f"Calendar MCP: Executing tool '{name}' with args: {arguments}")
    
    try:
        if name == "get_events":
            result = calendar_manager.get_events(
                time_min=arguments["time_min"],
                time_max=arguments["time_max"],
                calendar_id=arguments.get("calendar_id")
            )
            
        elif name == "create_event":
            result = calendar_manager.create_event(
                summary=arguments["summary"],
                description=arguments.get("description", ""),
                location=arguments.get("location", ""),
                start_datetime=arguments["start_datetime"],
                end_datetime=arguments["end_datetime"],
                calendar_id=arguments.get("calendar_id")
            )
            
        elif name == "check_availability":
            result = calendar_manager.check_availability(
                start_datetime=arguments["start_datetime"],
                end_datetime=arguments["end_datetime"],
                calendar_id=arguments.get("calendar_id")
            )
            
        else:
            result = {"status": "error", "message": f"Unknown tool: {name}"}
        
        response_text = json.dumps(result, indent=2)
        return [mcp_types.TextContent(type="text", text=response_text)]
        
    except Exception as e:
        logging.error(f"Calendar MCP tool error: {e}")
        error_response = {"status": "error", "message": str(e)}
        return [mcp_types.TextContent(type="text", text=json.dumps(error_response))]

async def run_calendar_mcp_server():
    """Run the Calendar MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logging.info("Calendar MCP Server: Starting...")
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="calendar-mcp-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Calendar MCP Server...")
    
    try:
        asyncio.run(run_calendar_mcp_server())
    except KeyboardInterrupt:
        logging.info("Calendar MCP Server stopped by user")
    except Exception as e:
        logging.error(f"Calendar MCP Server error: {e}")
