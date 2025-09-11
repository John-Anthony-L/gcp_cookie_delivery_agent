# Cookie Delivery Agent System - Technical Integration Guide

This document provides **deep technical implementation details** for integrating the cookie delivery agent system with real-world services. For quick start instructions, see [README.md](README.md).

## Current Implementation Status

### Completed Integrations
- **Calendar MCP Server**: Full Google Calendar API integration with OAuth2 authentication
- **Agent Sequential Workflow**: Complete multi-agent orchestration with state management
- **Error Handling & Fallbacks**: Graceful degradation to dummy data when services unavailable
- **Environment Configuration**: Comprehensive .env management with feature flags

### Partial Implementations
- **BigQuery Integration**: Database schema and tools ready, needs activation
- **Gmail MCP Server**: Basic structure exists, needs completion like calendar implementation

### Next Development Priorities
1. Complete Gmail MCP server following calendar pattern
2. Enable and test BigQuery integration
3. Production hardening and monitoring

## Calendar MCP Implementation Deep Dive

### Architecture Pattern: Direct Google API + MCP Wrapper

The calendar integration follows this pattern:
```python
# mcp-servers/calendar/calendar_mcp_server.py
class CalendarManager:
    def __init__(self):
        self.service = self._authenticate()  # Direct Google Calendar API
    
    def get_events(self, time_min, time_max, calendar_id="primary"):
        """Direct Google Calendar API call with error handling"""
        
    def create_event(self, summary, description, location, start_datetime, end_datetime, calendar_id="primary"):
        """Create calendar events with RFC3339 formatting"""
        
    def check_availability(self, start_datetime, end_datetime, calendar_id="primary"):
        """Check for scheduling conflicts"""
```

### Authentication Flow
```python
# OAuth2 Flow Implementation
def _authenticate(self):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    
    # Load existing token
    if os.path.exists('calendar_token.json'):
        creds = Credentials.from_authorized_user_file('calendar_token.json', SCOPES)
    
    # Refresh or create new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('calendar_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token for future use
        with open('calendar_token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)
```

### Agent Integration Pattern
```python
# cookie-scheduler-agent/agent.py
# Dynamic import with fallback
try:
    from .mcp_servers.calendar.calendar_mcp_server import CalendarManager
    calendar_manager = CalendarManager()
    CALENDAR_MCP_AVAILABLE = calendar_manager.service is not None
except ImportError as e:
    calendar_manager = None
    CALENDAR_MCP_AVAILABLE = False

# Tool function with real API + fallback
def schedule_delivery(tool_context: ToolContext, date: str, order_number: str, location: str, time_preference: str = "morning"):
    if use_calendar_mcp and CALENDAR_MCP_AVAILABLE and calendar_manager:
        # Use real Google Calendar API
        create_result = calendar_manager.create_event(
            summary=f"🍪 Cookie Delivery - {order_number}",
            description=event_description,
            location=location,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            calendar_id=business_calendar_id
        )
        return create_result
    else:
        # Fallback to dummy data
        return dummy_schedule_delivery(date, order_number, location, time_preference)
```

## BigQuery Integration Architecture

### Current State: Structure Ready, Needs Activation

The BigQuery integration is **structurally complete** but not yet activated. Here's the implementation:

```python
# bigquery-utils/bigquery_tools.py (implemented)
async def get_latest_order_from_bigquery(tool_context: ToolContext) -> dict:
    """Fetches most recent order with 'order_placed' status"""
    
async def update_order_status_in_bigquery(tool_context: ToolContext, order_number: str, new_status: str) -> dict:
    """Updates order status to 'scheduled', 'delivered', etc."""

# Agent integration pattern (ready)
def get_latest_order(tool_context: ToolContext) -> dict:
    if use_bigquery and BIGQUERY_AVAILABLE:
        return asyncio.run(get_latest_order_from_bigquery(tool_context))
    else:
        # Fallback to dummy data (currently active)
        return get_dummy_order_data()
```

### Database Schema (Implemented)
```sql
CREATE TABLE `{PROJECT_ID}.cookie_delivery.orders` (
  order_id STRING NOT NULL,
  order_number STRING NOT NULL,
  customer_email STRING NOT NULL,
  customer_name STRING NOT NULL,
  customer_phone STRING,
  order_items ARRAY<STRUCT<
    item_name STRING,
    quantity INT64,
    unit_price FLOAT64
  >>,
  delivery_address STRUCT<
    street STRING,
    city STRING,
    state STRING,
    zip_code STRING,
    country STRING
  >,
  delivery_location STRING,
  delivery_request_date DATE,
  delivery_time_preference STRING,
  order_status STRING NOT NULL,
  total_amount FLOAT64,
  order_date TIMESTAMP,
  special_instructions STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Activation Steps
1. **Set Environment Variables**: `USE_BIGQUERY=true` in `.env`
2. **Run Setup Script**: `./setup.sh` to create dataset and tables
3. **Test Connection**: `python bigquery-utils/test_bigquery.py`
4. **Add Sample Data**: Insert test orders for validation

## Gmail MCP Implementation Roadmap

### Current State: Basic Structure, Needs Calendar-Style Implementation

The Gmail MCP server exists but needs completion following the successful calendar pattern:

```python
# gmail_mcp_server.py (needs completion)
class GmailManager:
    def __init__(self):
        self.service = self._authenticate()  # Implement like CalendarManager
    
    def send_email(self, to_email, subject, body, from_email=None):
        """Send HTML email via Gmail API"""
        
    def get_message_status(self, message_id):
        """Track email delivery status"""
```

### Implementation Pattern (Following Calendar Success)
1. **OAuth2 Setup**: Similar to calendar - `gmail_credentials.json` + `gmail_token.json`
2. **API Scopes**: `['https://www.googleapis.com/auth/gmail.send']`
3. **Error Handling**: Same graceful fallback pattern as calendar
4. **Agent Integration**: Update email agent tools to use real Gmail API

### Required OAuth2 Scopes
```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'  # for status tracking
]
```

### Agent Integration Target
```python
# Target implementation in agent.py
def send_confirmation_email(tool_context: ToolContext, recipient_email: str, subject: str, body: str):
    if use_gmail_mcp and GMAIL_MCP_AVAILABLE and gmail_manager:
        # Use real Gmail API
        result = gmail_manager.send_email(
            to_email=recipient_email,
            subject=subject,
            body=body,
            from_email=business_email
        )
        return result
    else:
        # Fallback to dummy response
        return dummy_send_email(recipient_email, subject, body)
```

## Agent Workflow Implementation Details

### Sequential Agent Pattern (Implemented)
```python
# Successful pattern now working
delivery_workflow_agent = SequentialAgent(
    name="delivery_workflow_agent",
    description="Manages the entire cookie delivery process from order to confirmation.",
    sub_agents=[
        store_database_agent,    # BigQuery operations (structure ready)
        calendar_agent,          # ✅ Real Google Calendar integration
        email_agent             # Basic implementation (needs Gmail MCP)
    ],
)

# Root agent with proper termination (fixed infinite loop issue)
root_agent = Agent(
    name="root_agent",
    instruction="""
    1. Greet user and ask to start cookie service
    2. Transfer to delivery_workflow_agent
    3. Summarize results and wait for next request
    4. DO NOT restart unless explicitly requested
    """,
    sub_agents=[delivery_workflow_agent],
)
```

### State Management Pattern (Working)
```python
# State flows through sequential agents
def get_latest_order(tool_context: ToolContext) -> dict:
    # Save to state for next agent
    tool_context.state['order_details'] = order_details
    
def schedule_delivery(tool_context: ToolContext, ...):
    # Read from state, update calendar, save results
    order_details = tool_context.state.get('order_details', {})
    # ... create calendar event ...
    tool_context.state['delivery_schedule'] = delivery_info
    
def send_confirmation_email(tool_context: ToolContext, ...):
    # Read all previous state for email content
    order_details = tool_context.state.get('order_details', {})
    delivery_schedule = tool_context.state.get('delivery_schedule', {})
```

### Error Handling Pattern (Implemented)
```python
# Graceful degradation at each level
def calendar_operation():
    if use_calendar_mcp and CALENDAR_MCP_AVAILABLE and calendar_manager:
        try:
            return real_calendar_api_call()
        except Exception as e:
            logging.error(f"Calendar API error: {e}")
            return fallback_to_dummy_data()
    else:
        logging.info("Using dummy data (Calendar MCP not available)")
        return dummy_calendar_data()
```

## Configuration and Environment

### Environment Variables
```bash
# BigQuery
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Business Email/Calendar
export BUSINESS_EMAIL="deliveries@cookiebusiness.com"
export BUSINESS_CALENDAR_ID="primary"

# MCP Server Endpoints (if running remotely)
export CALENDAR_MCP_URL="stdio"  # or "tcp://localhost:8001"
export GMAIL_MCP_URL="stdio"     # or "tcp://localhost:8002"
```

### OAuth2 Setup
1. **Google Cloud Console**: Create project and enable APIs
2. **Credentials**: Download OAuth2 credentials JSON
3. **Business Account**: Authenticate with business Google Workspace account
4. **Scopes**: Configure appropriate API scopes

## Error Handling and Resilience

### BigQuery Error Handling
```python
async def robust_bigquery_operation(query: str, parameters: List):
    try:
        result = await execute_bigquery(query, parameters)
        return {"status": "success", "data": result}
    except Exception as e:
        logging.error(f"BigQuery error: {e}")
        # Implement retry logic
        # Fall back to dummy data if needed
        return {"status": "error", "message": str(e)}
```

### MCP Server Health Checks
```python
async def check_mcp_health(server_name: str):
    try:
        response = await mcp_client.ping()
        return response.status == "healthy"
    except Exception:
        logging.warning(f"MCP server {server_name} unavailable")
        return False
```

## Production Implementation Roadmap

### Phase 1: Complete Current Implementations (Mostly Done)
- **Calendar MCP**: Fully functional Google Calendar integration
- **Agent Workflow**: Sequential processing with state management
- **Error Handling**: Graceful fallbacks and comprehensive logging
- **BigQuery**: Enable `USE_BIGQUERY=true` and test
- **Gmail MCP**: Complete following calendar pattern

### Phase 2: Production Hardening
```python
# Monitoring and observability
def log_agent_operation(agent_name: str, operation: str, status: str, **kwargs):
    logging.info("Agent operation", extra={
        "agent_name": agent_name,
        "operation": operation,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    })

# Health checks for services
async def health_check():
    status = {
        "bigquery": test_bigquery_connection(),
        "calendar_mcp": CALENDAR_MCP_AVAILABLE,
        "gmail_mcp": GMAIL_MCP_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }
    return status
```

### Phase 3: Advanced Features
- **Analytics Dashboard**: Order processing metrics
- **Webhook Integration**: Real-time order updates
- **Load Balancing**: Multiple agent instances
- **Automated Testing**: CI/CD pipeline with integration tests

## Metrics and Monitoring

### Key Performance Indicators
- **Order Processing Time**: Database → Calendar → Email workflow
- **Calendar Integration Success Rate**: % of successful event creations
- **Email Delivery Rate**: % of successful customer notifications
- **Fallback Usage**: % of operations using dummy data vs real APIs

### Logging Strategy
```python
# Structured logging for each component
logging.info("Calendar operation", extra={
    "operation": "create_event",
    "order_id": "ORD12345",
    "calendar_id": "primary",
    "status": "success",
    "event_id": "abc123xyz",
    "processing_time_ms": 1250
})
```

## Security Implementation

### Authentication Management
```python
# Credential rotation strategy
def refresh_oauth_tokens():
    for service in ['calendar', 'gmail']:
        if token_needs_refresh(service):
            refresh_token(service)
            log_security_event("token_refreshed", service=service)

# Secure credential storage
def load_credentials(service_name: str):
    # Production: Use Google Secret Manager
    # Development: Use local JSON files with .gitignore
    if ENVIRONMENT == "production":
        return load_from_secret_manager(f"{service_name}_credentials")
    else:
        return load_from_file(f"{service_name}_credentials.json")
```

This architecture provides a robust foundation that's already **working for calendar integration** and ready for expansion to BigQuery and Gmail services.
