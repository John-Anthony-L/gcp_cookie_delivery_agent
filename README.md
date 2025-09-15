# Cookie Delivery Agent System

A sophisticated multi-agent system built with Google ADK that automates cookie delivery order processing, scheduling, and customer communication. The system integrates with BigQuery using Google's first-party ADK toolset for order management, Google Calendar via MCP for delivery scheduling, and Gmail for customer notifications.

## Current Implementation Status

- **BigQuery ADK Integration**: Fully implemented using Google's official first-party ADK BigQuery toolset
- **Calendar MCP Integration**: Fully functional Google Calendar API via MCP server
- **Agent Workflow**: Complete sequential agent system with real BigQuery and calendar integration
- **Async Compatibility**: Resolved async conflicts for ADK web interface compatibility
- **Gmail Integration**: Basic implementation, needs MCP server completion

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Root Agent    │───►│ Sequential Agent │───►│  Sub-Agents     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Database Agent  │    │  Calendar Agent  │    │   Email Agent   │
│ (BigQuery ADK)  │    │    MCP Server    │    │   MCP Server    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    BigQuery     │    │ Google Calendar  │    │     Gmail       │
│  (ADK Toolset)  │    │  (Business Acct) │    │ (Business Acct) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Legend**: Fully Implemented | Partial/Structure Only | In Progress

### Agent Workflow

1. **Database Agent**: Fetches new orders from BigQuery using Google's first-party ADK toolset with status "order_placed"
2. **Calendar Agent**: Checks availability and schedules delivery appointments
3. **Email Agent**: Generates personalized confirmation emails and updates order status in BigQuery

## Quick Start

### Prerequisites

- Python 3.8+
- Google Cloud Project with BigQuery enabled
- Google Workspace account (for business calendar/email)
- Google ADK installed

### Installation

1. **Clone and Install Dependencies**
```bash
cd cookie-scheduler-agent
pip install -r requirements.txt
```

2. **Set up Environment Variables**
```bash
cp .env.example .env
# Edit .env with your configuration (see Environment Setup below)
```

3. **Configure Google Cloud Authentication**
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

4. **Calendar MCP Setup (Implemented)**
```bash
# Navigate to calendar MCP directory
cd mcp-servers/calendar/

# The calendar MCP server is already implemented!
# You just need OAuth2 credentials:
# 1. Go to Google Cloud Console
# 2. Enable Calendar API
# 3. Create OAuth 2.0 Client ID (Desktop Application)
# 4. Download and save as calendar_credentials.json in this directory

# Test the calendar MCP
python test_calendar_functions.py
```

5. **Enable Calendar MCP Integration**
```bash
# Edit .env file and set:
USE_CALENDAR_MCP=true
BUSINESS_CALENDAR_ID=primary  # or your specific calendar ID
```

6. **BigQuery Setup (ADK Toolset Ready)**
```bash
# BigQuery integration now uses Google's first-party ADK toolset
# Authentication is handled via Application Default Credentials

# Set up Google Cloud authentication
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Enable BigQuery Integration
# Edit .env file and set:
USE_BIGQUERY=true

# Optional: Run BigQuery environment setup for sample data
python bigquery-utils/create_bigquery_environment.py
```

7. **Run the Agent System with the WebUI**
```bash
# The system will automatically:
# - Use real Google Calendar if MCP configured
# - Fall back to dummy data for missing services

bash adk web
```

## Environment Setup

Create a `.env` file in the `cookie-scheduler-agent/` directory with the following configuration:

### Required Environment Variables

```bash
# =============================================================================
# GOOGLE CLOUD CONFIGURATION
# =============================================================================
# Your Google Cloud Project ID where BigQuery dataset will be created
GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# Model configuration for Google ADK
MODEL=gemini-2.5-flash

# =============================================================================
# CALENDAR MCP INTEGRATION (IMPLEMENTED)
# =============================================================================
# Set to 'true' to use real Google Calendar via MCP server
USE_CALENDAR_MCP=true

# Google Calendar ID for delivery scheduling
# Use 'primary' for the main calendar or a specific calendar ID
BUSINESS_CALENDAR_ID=primary

# =============================================================================
# BIGQUERY ADK INTEGRATION (FULLY IMPLEMENTED)
# =============================================================================
# Set to 'true' to use Google's first-party ADK BigQuery toolset
# Set to 'false' to use dummy data for development/testing
USE_BIGQUERY=true

# =============================================================================
# BUSINESS ACCOUNT CONFIGURATION
# =============================================================================
# Business email address for sending customer communications
BUSINESS_EMAIL=deliveries@yourbusiness.com

# =============================================================================
# DEVELOPMENT/TESTING
# =============================================================================
# Set to 'development' to use dummy data instead of real services
ENVIRONMENT=production

# Logging level
LOG_LEVEL=INFO
```

### Calendar MCP Server Setup (IMPLEMENTED)

The Calendar MCP server is **fully implemented and functional**! Here's what's ready:

#### What's Working:
- Google Calendar API authentication via OAuth2
- Event creation, reading, and availability checking
- RFC3339 datetime formatting for Google Calendar
- Automatic fallback to dummy data if unavailable
- Comprehensive error handling and logging

#### Setup Steps:
1. **Enable Calendar API** in Google Cloud Console
2. **Create OAuth2 Credentials** (Desktop Application)
3. **Save credentials** as `mcp-servers/calendar/calendar_credentials.json`
4. **Test the integration**: `python mcp-servers/calendar/test_calendar_functions.py`

#### File Structure:
```
mcp-servers/calendar/
├── calendar_mcp_server.py       # Main MCP server (CalendarManager class)
├── calendar_credentials.json    # Your OAuth2 credentials
├── calendar_token.json          # Auto-generated tokens
└── test_calendar_functions.py   # Test script
```

## BigQuery Schema

The system creates the following BigQuery structure:

### Dataset: `cookie_delivery`
### Table: `orders`

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
  delivery_time_preference STRING,  -- 'morning', 'afternoon', 'evening'
  order_status STRING NOT NULL,     -- 'order_placed', 'confirmed', 'scheduled', 'delivered'
  total_amount FLOAT64,
  order_date TIMESTAMP,
  special_instructions STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Sample Data Insert

```sql
INSERT INTO `{PROJECT_ID}.cookie_delivery.orders` VALUES (
  'ORD12345',
  'ORD12345',
  'customer@example.com',
  'John Doe',
  '+1-555-0123',
  [
    STRUCT('Chocolate Chip', 12, 2.50),
    STRUCT('Oatmeal Raisin', 6, 2.75)
  ],
  STRUCT('123 Main St', 'Anytown', 'CA', '12345', 'USA'),
  '123 Main St, Anytown, CA 12345, USA',
  '2025-09-10',
  'morning',
  'order_placed',
  63.50,
  '2025-09-04T10:30:00Z',
  'Please ring doorbell twice',
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);
```

## MCP Server Setup

The system uses Model Context Protocol (MCP) servers for Gmail and Calendar integration with your business accounts.

### Running MCP Servers

**Calendar MCP Server:**
```bash
python calendar_mcp_server.py
```

**Gmail MCP Server:**
```bash
python gmail_mcp_server.py
```

### MCP Server Features

#### Calendar MCP Server
- `get_events`: Fetch delivery schedule
- `create_event`: Schedule new deliveries  
- `check_availability`: Verify time slot availability
- `update_event`: Modify existing appointments

#### Gmail MCP Server
- `send_email`: Send customer confirmation emails
- `get_message_status`: Track email delivery status

## Current Implementation: What's Working

### BigQuery ADK Integration (Production Ready)
- **Google's First-Party ADK Toolset**: Uses official BigQuery ADK integration
- **Application Default Credentials**: Secure authentication via ADC
- **WriteMode Configuration**: Proper data access control (BLOCKED, ALLOWED, PROTECTED)
- **Async Compatibility**: Resolved async conflicts for ADK web interface usage
- **Available Tools**: list_dataset_ids, get_dataset_info, list_table_ids, get_table_info, execute_sql, ask_data_insights

### Calendar Agent with Real Google Calendar
- **Real Google Calendar Integration**: Creates actual calendar events via MCP server
- **Smart Fallback**: Uses dummy data when Calendar MCP unavailable
- **Business Calendar Support**: Configurable calendar ID for business account
- **RFC3339 Datetime**: Proper timezone handling for Google Calendar API

### Agent Workflow (Sequential Processing)
1. **Database Agent**: Fetches orders using BigQuery ADK toolset with production-ready data access
2. **Calendar Agent**: Real Google Calendar scheduling via MCP server
3. **Email Agent**: Customer communication with BigQuery integration for order updates
4. **Haiku Writer Sub-Agent**: Generates creative seasonal content

### Error Handling & Resilience
- **Graceful Degradation**: Falls back to dummy data when services unavailable
- **Comprehensive Logging**: Detailed operation tracking and error reporting
- **Authentication Recovery**: Handles OAuth2 token refresh automatically

### Next Implementation Steps
1. **Complete Gmail MCP Server**: Similar to calendar implementation
2. **Production Hardening**: Add monitoring and alerting
3. **Extended BigQuery Analytics**: Leverage ask_data_insights for business intelligence

## Workflow Process

1. **Order Detection**: Database agent fetches latest order with "order_placed" status
2. **Schedule Analysis**: Calendar agent checks availability for requested delivery date
3. **Appointment Creation**: Calendar agent schedules delivery appointment
4. **Haiku Generation**: Email agent delegates to haiku writer for personalized content
5. **Customer Notification**: Email agent sends confirmation with delivery details and haiku
6. **Status Update**: Order status updated to "scheduled" in BigQuery

## Testing & Validation

### Calendar MCP Testing (Working)
```bash
# Test real Google Calendar integration
cd mcp-servers/calendar/
python test_calendar_functions.py

# Expected output:
# Calendar MCP: Successfully connected to Google Calendar
# Calendar events retrieved successfully
# Event creation and availability checking working
```

### Agent Integration Testing (Working)
```bash
# Test agent with real calendar integration
python agent.py

# The agent will:
# 1. Import CalendarManager successfully
# 2. Use real Google Calendar if configured
# 3. Fall back to dummy data gracefully
# 4. Process sequential workflow
```

### BigQuery ADK Testing (Production Ready)
```bash
# Test BigQuery ADK toolset integration
cd cookie-scheduler-agent/
python test_bigquery_integration.py

# Expected output:
# BigQuery ADK Integration Test Suite
# All tests passed: toolset initialization, agent creation, async compatibility
```

## File Structure

```
cookie-scheduler-agent/
├── agent.py                    # Legacy agent definitions (see agents.py for modern implementation)
├── agents.py                   # Modern ADK agent definitions with BigQuery toolset
├── dummy_data.py              # Fallback data for testing
├── gmail_mcp_server.py        # Gmail MCP server (basic implementation)
├── test_bigquery_integration.py # BigQuery ADK toolset integration tests
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment configuration
├── .env                      # Your environment configuration (create this)
│
├── bigquery_utils/           # BigQuery ADK toolset integration
│   ├── bigquery_tools.py     # ADK BigQuery toolset implementation
│   └── test_bigquery.py      # Legacy test script
│
├── mcp-servers/              # MCP Server implementations
│   ├── calendar/             # FULLY IMPLEMENTED Calendar MCP
│   │   ├── calendar_mcp_server.py      # Complete CalendarManager class
│   │   ├── calendar_credentials.json   # OAuth2 credentials (you create)
│   │   ├── calendar_token.json         # Auto-generated tokens
│   │   └── test_calendar_functions.py  # Test script for validation
│   ├── start_calendar_mcp.py           # MCP server startup script
│   └── setup_calendar_credentials.md   # Setup instructions
│
└── tests/                    # Test files and validation scripts
    └── test_bigquery_adk_integration.py  # Comprehensive ADK integration tests
```

**Legend**: Fully Implemented | Structure Ready | In Progress | You Create | Documentation

## Security Notes

### Credential Management
- Never commit `.env`, `*_credentials.json`, or `*_token.json` files to version control
- Use Google Secret Manager for production deployments
- Implement credential rotation policies

### API Permissions
- Use minimal required scopes for OAuth2
- Implement proper IAM roles for BigQuery access
- Monitor API usage and set quotas

### Data Protection
- All customer data is encrypted at rest in BigQuery
- Use HTTPS for all API communications
- Implement audit logging for data access

## Troubleshooting

### Calendar MCP Issues (Most Common)

1. **Import Error: "calendar_mcp_server could not be resolved"**
   ```bash
   # Solution: This is an IDE issue, the code works at runtime
   # The agent uses try/catch for graceful fallback
   # Verify it works: python mcp-servers/calendar/test_calendar_functions.py
   ```

2. **OAuth2 Authentication Failed**
   ```bash
   # 1. Ensure Calendar API is enabled in Google Cloud Console
   # 2. Create OAuth 2.0 Client ID (Desktop Application)  
   # 3. Download and save as mcp-servers/calendar/calendar_credentials.json
   # 4. Delete calendar_token.json to force re-authentication
   ```

3. **Calendar Events Not Appearing**
   ```bash
   # Check your calendar ID in .env:
   BUSINESS_CALENDAR_ID=primary  # or specific calendar ID
   # Verify permissions on the target calendar
   ```

4. **Permissions Error**
   ```bash
   # 1. Ensure Calendar API is enabled in Google Cloud Console
   # 2. Navigate to: "APIs & Services" → "OAuth consent screen"
   # 3. User Type: Make sure you selected "External" (not Internal)
   # 4. Test users: Add your personal Gmail account as a test user
   ```


### BigQuery ADK Issues

1. **BigQuery ADK Toolset Import Error**
   ```bash
   # Ensure google-adk package is installed with BigQuery support
   pip install google-adk[bigquery]
   
   # Verify authentication
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **BigQuery Permission Denied**
   ```bash
   # Ensure your account has BigQuery permissions
   # Required roles: BigQuery Data Editor, BigQuery Job User
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="user:your-email@domain.com" \
     --role="roles/bigquery.dataEditor"
   ```

3. **Async Compatibility Issues**
   ```bash
   # This should be resolved with the ADK toolset integration
   # If you encounter async errors, run the integration test:
   python test_bigquery_integration.py
   ```

### Debug Mode

Enable detailed logging:

```bash
# In .env file
LOG_LEVEL=DEBUG
```

## Monitoring and Analytics

The system includes built-in analytics via the `get_order_analytics` function:

```python
# Get business insights
analytics = await get_order_analytics(tool_context, days=30)
print(analytics)
# Returns: order counts, average order value, total revenue by status
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the Apache-2.0 license - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the detailed [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
3. Create an issue in the repository

---

**Note**: This system is designed for production use with real business accounts. Always test thoroughly in a development environment before deploying to production.
