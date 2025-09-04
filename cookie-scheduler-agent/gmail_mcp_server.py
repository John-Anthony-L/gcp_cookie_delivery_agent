"""
MCP Server for Gmail integration.
This MCP server exposes Gmail operations for the cookie delivery business email.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List
from datetime import datetime

from dotenv import load_dotenv

# MCP Server Imports
from mcp import types as mcp_types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Gmail API imports (you'll need to install these)
# pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import base64
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    logging.error("Gmail API dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

load_dotenv()

# Gmail API Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
BUSINESS_EMAIL = os.getenv('BUSINESS_EMAIL', 'deliveries@cookiebusiness.com')

class GmailManager:
    """Manages Gmail API operations for the business account."""
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists('gmail_token.json'):
            creds = Credentials.from_authorized_user_file('gmail_token.json', SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'gmail_credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('gmail_token.json', 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logging.info("Gmail API authenticated successfully")
        except HttpError as error:
            logging.error(f"Gmail API authentication failed: {error}")
    
    def send_email(self, to: str, subject: str, body: str, body_type: str = "html") -> Dict:
        """Send an email via Gmail API."""
        try:
            if body_type == "html":
                message = MimeMultipart('alternative')
                message['to'] = to
                message['from'] = BUSINESS_EMAIL
                message['subject'] = subject
                
                html_part = MimeText(body, 'html')
                message.attach(html_part)
            else:
                message = MimeText(body)
                message['to'] = to
                message['from'] = BUSINESS_EMAIL
                message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw_message}
            
            result = self.service.users().messages().send(
                userId='me', body=send_message).execute()
            
            logging.info(f"Email sent successfully. Message ID: {result['id']}")
            return {
                "status": "success",
                "message_id": result['id'],
                "recipient": to,
                "timestamp": datetime.now().isoformat()
            }
            
        except HttpError as error:
            logging.error(f"Gmail API error: {error}")
            return {
                "status": "error",
                "message": f"Failed to send email: {str(error)}"
            }
    
    def get_message_status(self, message_id: str) -> Dict:
        """Get the status of a sent message."""
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id).execute()
            
            return {
                "status": "success",
                "message_id": message_id,
                "thread_id": message['threadId'],
                "labels": message.get('labelIds', [])
            }
            
        except HttpError as error:
            logging.error(f"Gmail API error getting message status: {error}")
            return {
                "status": "error",
                "message": f"Failed to get message status: {str(error)}"
            }

# Initialize Gmail manager
gmail_manager = GmailManager()

# MCP Server Setup
app = Server("gmail-mcp-server")

@app.list_tools()
async def list_tools() -> List[mcp_types.Tool]:
    """List available Gmail tools."""
    return [
        mcp_types.Tool(
            name="send_email",
            description="Send an email via the business Gmail account",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    },
                    "body_type": {
                        "type": "string",
                        "enum": ["html", "plain"],
                        "description": "Email body format",
                        "default": "html"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        ),
        mcp_types.Tool(
            name="get_message_status",
            description="Get the status of a sent email message",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "Gmail message ID to check"
                    }
                },
                "required": ["message_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[mcp_types.Content]:
    """Execute Gmail tools."""
    logging.info(f"Gmail MCP: Executing tool '{name}' with args: {arguments}")
    
    try:
        if name == "send_email":
            result = gmail_manager.send_email(
                to=arguments["to"],
                subject=arguments["subject"],
                body=arguments["body"],
                body_type=arguments.get("body_type", "html")
            )
            
        elif name == "get_message_status":
            result = gmail_manager.get_message_status(
                message_id=arguments["message_id"]
            )
            
        else:
            result = {"status": "error", "message": f"Unknown tool: {name}"}
        
        response_text = json.dumps(result, indent=2)
        return [mcp_types.TextContent(type="text", text=response_text)]
        
    except Exception as e:
        logging.error(f"Gmail MCP tool error: {e}")
        error_response = {"status": "error", "message": str(e)}
        return [mcp_types.TextContent(type="text", text=json.dumps(error_response))]

async def run_gmail_mcp_server():
    """Run the Gmail MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logging.info("Gmail MCP Server: Starting...")
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gmail-mcp-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Gmail MCP Server...")
    
    try:
        asyncio.run(run_gmail_mcp_server())
    except KeyboardInterrupt:
        logging.info("Gmail MCP Server stopped by user")
    except Exception as e:
        logging.error(f"Gmail MCP Server error: {e}")
