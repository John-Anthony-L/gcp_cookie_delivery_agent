# Cookie Delivery Agent System - Integration Guide

This document outlines how to integrate the cookie delivery agent system with real-world services: BigQuery for orders, Google Calendar for scheduling, and Gmail for customer communication.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Root Agent    │───►│ Sequential Agent │───►│  Sub-Agents     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Database Agent  │    │  Calendar Agent  │    │   Email Agent   │
│   (BigQuery)    │    │   (MCP Server)   │    │  (MCP Server)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    BigQuery     │    │ Google Calendar  │    │     Gmail       │
│   (Direct)      │    │  (Business Acct) │    │ (Business Acct) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Implementation Strategy

### 1. BigQuery Integration (Direct Connection)

**Why Direct**: Since you're using your own Google Cloud account, direct BigQuery integration is the most efficient approach.

**Setup Requirements**:
```bash
# Install BigQuery client
pip install google-cloud-bigquery

# Set up authentication
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

**Database Schema**:
```sql
CREATE TABLE `cookie_delivery.orders` (
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

**Integration Steps**:
1. Replace dummy functions in `agent.py` with `bigquery_tools.py` functions
2. Update imports to use BigQuery tools
3. Configure environment variables for your project

### 2. Google Calendar MCP Server (Business Account)

**Why MCP**: Separate business email account requires isolated authentication and API access.

**Setup Requirements**:
```bash
# Install Google Calendar API client
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Install MCP server dependencies
pip install mcp

# Set up OAuth2 credentials for business account
```

**MCP Server Features**:
- **get_events**: Fetch delivery schedule
- **create_event**: Schedule new deliveries
- **check_availability**: Verify time slot availability
- **update_event**: Modify existing appointments

**Running the MCP Server**:
```bash
python calendar_mcp_server.py
```

### 3. Gmail MCP Server (Business Account)

**Why MCP**: Business email separation and enhanced security for email operations.

**Setup Requirements**:
```bash
# Same Google API dependencies as Calendar
# Configure OAuth2 for Gmail API access
```

**MCP Server Features**:
- **send_email**: Send confirmation emails
- **get_message_status**: Track email delivery
- **send_html_email**: Rich formatting support

**Running the MCP Server**:
```bash
python gmail_mcp_server.py
```

## Agent Integration Patterns

### Pattern 1: Direct BigQuery Agent
```python
from bigquery_tools import get_latest_order_from_bigquery, update_order_status_in_bigquery
from google.adk.tools.function_tool import FunctionTool

store_database_agent = Agent(
    name="store_database_agent",
    model=model_name,
    description="Responsible for BigQuery order management",
    tools=[
        FunctionTool(get_latest_order_from_bigquery),
        FunctionTool(update_order_status_in_bigquery)
    ]
)
```

### Pattern 2: MCP-Connected Agents
```python
# Calendar agent communicates with MCP server
async def schedule_via_mcp(tool_context: ToolContext, date: str, order_number: str, location: str):
    mcp_response = await mcp_client.call_tool(
        "create_event",
        {
            "summary": f"Cookie Delivery - {order_number}",
            "location": location,
            "start_datetime": f"{date}T09:00:00-07:00",
            "end_datetime": f"{date}T09:30:00-07:00"
        }
    )
    return mcp_response

calendar_agent = Agent(
    name="calendar_agent",
    tools=[FunctionTool(schedule_via_mcp)]
)
```

### Pattern 3: Sub-Agent Delegation
```python
# Email agent delegates to haiku writer, then sends via MCP
email_agent = Agent(
    name="email_agent",
    sub_agents=[haiku_writer_agent],  # Creative sub-agent
    tools=[FunctionTool(send_email_via_mcp)]  # MCP email tool
)
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

## Migration Strategy

### Phase 1: BigQuery Integration
1. Set up BigQuery dataset and tables
2. Replace database agent tools with BigQuery versions
3. Test order fetching and status updates

### Phase 2: Calendar MCP
1. Deploy Calendar MCP server
2. Replace calendar agent tools with MCP calls
3. Test scheduling and availability checks

### Phase 3: Gmail MCP
1. Deploy Gmail MCP server
2. Replace email agent tools with MCP calls
3. Test email sending and tracking

### Phase 4: Production Hardening
1. Add comprehensive error handling
2. Implement monitoring and alerting
3. Set up automated backups
4. Configure load balancing for MCP servers

## Monitoring and Observability

### Logging Strategy
```python
import google.cloud.logging

# Structured logging for agent operations
logging.info("Agent operation", extra={
    "agent_name": "store_database_agent",
    "operation": "get_latest_order",
    "order_id": "ORD12345",
    "status": "success"
})
```

### Metrics to Track
- Order processing time
- Calendar scheduling success rate
- Email delivery rate
- MCP server availability
- BigQuery query performance

## Security Considerations

### Authentication
- Use Google Cloud IAM for BigQuery access
- OAuth2 with minimal scopes for Gmail/Calendar
- Secure credential storage (Google Secret Manager)

### Data Protection
- Encrypt customer data at rest
- Use HTTPS for all API communications
- Implement audit logging for data access

### Access Control
- Principle of least privilege
- Separate service accounts for each component
- Regular credential rotation

## Testing Strategy

### Unit Tests
```python
# Test BigQuery operations with test datasets
async def test_get_latest_order():
    result = await get_latest_order_from_bigquery(mock_context)
    assert result["status"] == "success"
    assert "order_id" in result
```

### Integration Tests
```python
# Test MCP server connectivity
async def test_calendar_mcp():
    events = await mcp_client.call_tool("get_events", {
        "time_min": "2025-09-01T00:00:00Z",
        "time_max": "2025-09-30T23:59:59Z"
    })
    assert events is not None
```

### End-to-End Tests
```python
# Test complete workflow
async def test_full_delivery_workflow():
    # Simulate new order in BigQuery
    # Run agent workflow
    # Verify calendar event created
    # Verify email sent
    # Verify order status updated
```

This architecture provides a robust, scalable solution that separates concerns appropriately while maintaining the agent-based workflow structure.
