# 🗓️ MCP Servers - Organized Structure

This directory contains Model Context Protocol (MCP) servers that provide external integrations for the cookie delivery agent.

## 📁 Directory Structure

```
cookie-scheduler-agent/
├── mcp-servers/
│   └── calendar/
│       ├── calendar_mcp_server.py          # Google Calendar MCP Server
│       ├── calendar_credentials.json       # OAuth credentials (not in git)
│       ├── calendar_token.json            # Access tokens (not in git)
│       └── test_calendar_functions.py     # Direct function tests
├── start_calendar_mcp.py                  # Convenience runner script
├── test_organized_structure.py            # Structure validation test
└── agent.py                              # Main agent (will integrate with MCP)
```

## Quick Start

### Start Calendar MCP Server
```bash
# From the main cookie-scheduler-agent directory
python start_calendar_mcp.py
```

### Test Calendar Functions
```bash
# Test from organized structure
cd mcp-servers/calendar
python test_calendar_functions.py
```

## What Changed by Organizing

### Benefits
1. **Clean Separation**: Each MCP server has its own directory
2. **Secure Credentials**: Credentials are isolated per service
3. **Scalable**: Easy to add Gmail, BigQuery, or other MCP servers
4. **Production Ready**: Better for deployment and maintenance
5. **Import Clarity**: Clear import paths for different services

### Path Updates Made
1. **Credentials Loading**: Updated to use relative paths within each MCP directory
2. **Environment Variables**: .env loading adjusted for parent directory
3. **Import Paths**: Future agent.py updates will import from `mcp-servers/calendar/`
4. **Working Directory**: MCP server runs from its own directory

### Security Updates
1. **Updated .gitignore**: New patterns for organized credential files
2. **Isolated Tokens**: Each service's tokens stay in their own directory
3. **Clear Patterns**: Easy to see which credentials belong to which service

## MCP Server Status

| Service | Status | Location | Functionality |
|---------|--------|----------|---------------|
| **Google Calendar** | Working | `mcp-servers/calendar/` | Read/Write events, check availability |
| **Gmail** | Planned | `mcp-servers/gmail/` | Send emails, templates |
| **BigQuery** | Could migrate | `../bigquery_tools.py` | Order data management |

## Next Steps

1. **Agent Integration**: Update `agent.py` to use MCP servers instead of dummy data
2. **Gmail MCP**: Create similar structure for email functionality  
3. **Production Deployment**: Each MCP server can run as separate service
4. **Monitoring**: Add health checks and logging for each MCP server

## Testing

The organized structure maintains all functionality while providing better organization:

-  **Authentication**: Works with Google Calendar API
-  **Event Creation**: Can create calendar events
-  **Event Reading**: Can retrieve calendar events  
-  **Availability Checking**: Can check for scheduling conflicts
-  **Event Updates**: Can modify existing events

## Integration Guide

When updating `agent.py` to use the organized MCP servers:

```python
# Instead of dummy data functions, import from organized structure
import sys
import os

# Add calendar MCP to path
calendar_path = os.path.join(os.path.dirname(__file__), 'mcp-servers', 'calendar')
sys.path.append(calendar_path)

from calendar_mcp_server import CalendarManager

# Use real calendar instead of dummy data
calendar_manager = CalendarManager()
```

This organized structure makes your cookie delivery agent more maintainable and production-ready! 🍪
