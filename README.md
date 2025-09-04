# Cookie Delivery Agent System

A sophisticated multi-agent system built with Google ADK that automates cookie delivery order processing, scheduling, and customer communication. The system integrates with BigQuery for order management, Google Calendar for delivery scheduling, and Gmail for customer notifications.

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

### Agent Workflow

1. **Database Agent**: Fetches new orders from BigQuery with status "order_placed"
2. **Calendar Agent**: Checks availability and schedules delivery appointments
3. **Email Agent**: Generates personalized confirmation emails with haikus and updates order status

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

4. **Initialize BigQuery Database**
```python
from bigquery_tools import BigQueryOrderManager

manager = BigQueryOrderManager()
manager.ensure_dataset_exists()
manager.create_orders_table()
```

5. **Run the Agent System**
```bash
python agent.py
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
MODEL=gemini-1.5-flash-001

# =============================================================================
# BUSINESS ACCOUNT CONFIGURATION (for MCP servers)
# =============================================================================
# Business email address for sending customer communications
BUSINESS_EMAIL=deliveries@yourbusiness.com

# Google Calendar ID for delivery scheduling
# Use 'primary' for the main calendar or a specific calendar ID
BUSINESS_CALENDAR_ID=primary

# =============================================================================
# MCP SERVER CONFIGURATION (Optional - for remote servers)
# =============================================================================
# If running MCP servers remotely, specify their endpoints
# Leave as 'stdio' if running locally
CALENDAR_MCP_URL=stdio
GMAIL_MCP_URL=stdio

# =============================================================================
# DEVELOPMENT/TESTING (Optional)
# =============================================================================
# Set to 'development' to use dummy data instead of real services
ENVIRONMENT=production

# Logging level
LOG_LEVEL=INFO
```

### OAuth2 Credentials Setup

For the MCP servers to access Google Calendar and Gmail APIs, you'll need OAuth2 credentials:

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Enable APIs**: Calendar API and Gmail API
3. **Create Credentials**: OAuth 2.0 Client ID (Desktop Application)
4. **Download JSON**: Save as `calendar_credentials.json` and `gmail_credentials.json`
5. **Place in Directory**: Put credential files in `cookie-scheduler-agent/`

```
cookie-scheduler-agent/
├── .env
├── calendar_credentials.json  # OAuth2 for Calendar MCP
├── gmail_credentials.json     # OAuth2 for Gmail MCP
└── ...
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

## Agent Components

### 1. Database Agent (`store_database_agent`)
- **Purpose**: Manages order data in BigQuery
- **Tools**: `get_latest_order`, `update_order_status`
- **Integration**: Direct BigQuery connection

### 2. Calendar Agent (`calendar_agent`)
- **Purpose**: Handles delivery scheduling
- **Tools**: `get_delivery_schedule`, `schedule_delivery`, `save_delivery_month`
- **Integration**: Google Calendar via MCP server

### 3. Email Agent (`email_agent`)
- **Purpose**: Customer communication and order finalization
- **Tools**: `send_confirmation_email`, `update_order_status`
- **Sub-Agents**: `haiku_writer_agent` (generates personalized haikus)
- **Integration**: Gmail via MCP server

### 4. Haiku Writer Sub-Agent (`haiku_writer_agent`)
- **Purpose**: Creative content generation
- **Capability**: Generates seasonal haikus based on delivery month and cookie types

## Workflow Process

1. **Order Detection**: Database agent fetches latest order with "order_placed" status
2. **Schedule Analysis**: Calendar agent checks availability for requested delivery date
3. **Appointment Creation**: Calendar agent schedules delivery appointment
4. **Haiku Generation**: Email agent delegates to haiku writer for personalized content
5. **Customer Notification**: Email agent sends confirmation with delivery details and haiku
6. **Status Update**: Order status updated to "scheduled" in BigQuery

## Testing

### Development Mode

Set `ENVIRONMENT=development` in `.env` to use dummy data instead of real services:

```bash
# In .env file
ENVIRONMENT=development
```

### Test Commands

```bash
# Test BigQuery connection
python -c "from bigquery_tools import BigQueryOrderManager; mgr = BigQueryOrderManager(); print('BigQuery connected!')"

# Test MCP servers
python calendar_mcp_server.py &
python gmail_mcp_server.py &

# Run agent workflow
python agent.py
```

## 📁 File Structure

```
cookie-scheduler-agent/
├── agent.py                    # Main agent definitions and workflow
├── bigquery_tools.py          # BigQuery integration functions
├── calendar_mcp_server.py     # Google Calendar MCP server
├── gmail_mcp_server.py        # Gmail MCP server
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── INTEGRATION_GUIDE.md       # Detailed implementation guide
├── .env.example              # Example environment configuration
├── .env                      # Your environment configuration (create this)
├── calendar_credentials.json # OAuth2 credentials for Calendar (you create)
├── gmail_credentials.json    # OAuth2 credentials for Gmail (you create)
├── calendar_token.json       # Auto-generated OAuth2 tokens
└── gmail_token.json          # Auto-generated OAuth2 tokens
```

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

### Common Issues

1. **BigQuery Permission Denied**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **OAuth2 Authentication Failed**
   - Ensure credential JSON files are in the correct directory
   - Check that Calendar and Gmail APIs are enabled in Google Cloud Console
   - Verify business account has proper permissions

3. **MCP Server Connection Issues**
   - Check that MCP servers are running
   - Verify `stdio` configuration in environment variables
   - Check firewall settings if using remote MCP servers

4. **Agent Execution Errors**
   - Check `.env` file configuration
   - Verify all dependencies are installed
   - Check Google Cloud authentication status

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

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the detailed [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
3. Create an issue in the repository

---

**Note**: This system is designed for production use with real business accounts. Always test thoroughly in a development environment before deploying to production.
