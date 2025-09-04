# BigQuery Integration Guide

This guide explains how to set up and use BigQuery integration with the Cookie Delivery Agent System.

## Overview

The system can operate in two modes:
- **Dummy Data Mode**: Uses in-memory data structures (default)
- **BigQuery Mode**: Uses real Google BigQuery for order storage and management

## Quick Setup

### 1. Prerequisites

- Google Cloud Project with BigQuery API enabled
- `gcloud` CLI installed and authenticated
- Python dependencies installed (`pip install -r requirements.txt`)

### 2. Automated Setup

```bash
# Navigate to the cookie-scheduler-agent directory
cd cookie-scheduler-agent

# Run the automated setup script
./setup.sh
```

The setup script will:
- Check your Google Cloud authentication
- Enable required APIs
- Create the BigQuery dataset and table
- Populate sample data
- Verify the setup

### 3. Enable BigQuery Integration

Edit your `.env` file:
```bash
USE_BIGQUERY=true
GOOGLE_CLOUD_PROJECT=your-actual-project-id
```

### 4. Test the Integration

```bash
python test_bigquery.py
```

## Manual Setup

If you prefer manual setup or the automated script fails:

### 1. Create Dataset and Table

```python
from bigquery_tools import BigQueryOrderManager

manager = BigQueryOrderManager()
manager.ensure_dataset_exists()
manager.create_orders_table()
```

### 2. Insert Sample Data

```python
from bigquery_tools import setup_bigquery_environment

result = setup_bigquery_environment()
print(result)
```

## Database Schema

### Dataset: `cookie_delivery`
### Table: `orders`

| Field | Type | Mode | Description |
|-------|------|------|-------------|
| order_id | STRING | REQUIRED | Unique order identifier |
| order_number | STRING | REQUIRED | Human-readable order number |
| customer_email | STRING | REQUIRED | Customer email address |
| customer_name | STRING | REQUIRED | Customer full name |
| customer_phone | STRING | NULLABLE | Customer phone number |
| order_items | RECORD | REPEATED | Array of ordered items |
| delivery_address | RECORD | NULLABLE | Structured delivery address |
| delivery_location | STRING | NULLABLE | Formatted delivery address |
| delivery_request_date | DATE | NULLABLE | Requested delivery date |
| delivery_time_preference | STRING | NULLABLE | morning/afternoon/evening |
| order_status | STRING | REQUIRED | Current order status |
| total_amount | FLOAT | NULLABLE | Total order amount |
| order_date | TIMESTAMP | NULLABLE | When order was placed |
| special_instructions | STRING | NULLABLE | Customer delivery notes |
| created_at | TIMESTAMP | NULLABLE | Record creation time |
| updated_at | TIMESTAMP | NULLABLE | Last update time |

### Order Status Values

- `order_placed`: New order, ready for processing
- `confirmed`: Order confirmed, ready for scheduling
- `scheduled`: Delivery scheduled
- `in_delivery`: Out for delivery
- `delivered`: Successfully delivered
- `cancelled`: Order cancelled

## API Functions

### Core Functions

#### `get_latest_order_from_bigquery(tool_context: ToolContext) -> Dict`
Fetches the most recent order with status "order_placed".

#### `update_order_status_in_bigquery(tool_context: ToolContext, order_number: str, new_status: str) -> Dict`
Updates the status of a specific order.

#### `get_order_analytics(tool_context: ToolContext, days: int = 30) -> Dict`
Returns analytics for orders in the specified time period.

### Utility Functions

#### `insert_sample_order(...) -> Dict`
Inserts a single order into BigQuery.

#### `setup_bigquery_environment() -> Dict`
Complete environment setup including sample data.

## Error Handling

The BigQuery integration includes comprehensive error handling:

- **Connection errors**: Graceful fallback to dummy data
- **Authentication errors**: Clear error messages with remediation steps
- **Query errors**: Detailed logging and error reporting
- **Data validation**: Schema validation before insertion

## Monitoring

### Query Performance
```sql
-- Check query history in BigQuery console
SELECT 
  job_id,
  query,
  total_bytes_processed,
  total_slot_ms,
  creation_time
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_USER
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
ORDER BY creation_time DESC;
```

### Data Quality
```sql
-- Check for data quality issues
SELECT 
  order_status,
  COUNT(*) as count,
  COUNT(DISTINCT customer_email) as unique_customers
FROM `your-project.cookie_delivery.orders`
GROUP BY order_status;
```

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Permission Denied**
   - Ensure BigQuery API is enabled
   - Check IAM roles (BigQuery Data Editor, BigQuery Job User)

3. **Table Not Found**
   - Run `setup.sh` again
   - Check project ID in environment variables

4. **Query Timeout**
   - Check BigQuery quotas
   - Optimize queries for large datasets

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python test_bigquery.py
```

### Verify Setup

```bash
# Check dataset exists
bq ls --project_id=YOUR_PROJECT_ID

# Check table schema
bq show your-project:cookie_delivery.orders

# Check sample data
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`your-project.cookie_delivery.orders\`"
```

## Cost Optimization

- Use partitioned tables for large datasets
- Implement table clustering on frequently queried columns
- Monitor query costs in BigQuery console
- Set up billing alerts

## Security

- Use IAM roles with minimal required permissions
- Enable audit logging
- Consider field-level encryption for sensitive data
- Regular access reviews

## Production Considerations

- Set up monitoring and alerting
- Implement backup strategies
- Use separate datasets for different environments
- Configure appropriate retention policies
