#!/usr/bin/env python3
"""
Convenience script to test the organized MCP structure.
Run this from the main cookie-scheduler-agent directory.
"""

import sys
import os

# Add the calendar MCP server directory to Python path
calendar_mcp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mcp-servers', 'calendar')
sys.path.append(calendar_mcp_path)

# Import and run the test
from test_calendar_functions import test_calendar_functions

if __name__ == "__main__":
    test_calendar_functions()
