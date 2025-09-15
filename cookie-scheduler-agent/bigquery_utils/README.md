# BigQuery ADK Integration Directory

This directory contains the BigQuery ADK toolset integration for the Cookie Delivery System using Google's first-party ADK tools.

## Files

- `bigquery_tools.py` - ADK BigQuery toolset implementation with Application Default Credentials
- `create_bigquery_environment.py` - Legacy setup script for BigQuery dataset and table creation  
- `test_bigquery.py` - Legacy test script (use `../test_bigquery_integration.py` for ADK testing)
- `BIGQUERY_SETUP.md` - Comprehensive setup guide for ADK integration
- `requirements.txt` - Python dependencies for BigQuery setup

## ADK Integration Overview

The new implementation uses Google's official ADK BigQuery toolset:

```python
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode

def get_bigquery_toolset() -> BigQueryToolset:
    """Create and configure the ADK BigQuery toolset."""
    # Uses Application Default Credentials for authentication
    # WriteMode.ALLOWED for full read/write access
    # Synchronous operation compatible with ADK web interface
```

## Quick Start

### 1. Install Dependencies
```bash
pip install google-adk[bigquery]
```

### 2. Authentication
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 3. Test ADK Integration
```bash
# Use the comprehensive ADK test suite
cd ..
python test_bigquery_integration.py
```

## Key Features

- **ADK Toolset Integration**: Uses Google's first-party BigQuery tools
- **Application Default Credentials**: Secure authentication via ADC
- **Async Compatibility**: Resolved async conflicts for ADK web interface
- **WriteMode Configuration**: Proper data access control
- **Tool Availability**: list_dataset_ids, get_dataset_info, list_table_ids, get_table_info, execute_sql, ask_data_insights

## Migration from Legacy

The legacy implementation had async compatibility issues with the ADK web interface. The new ADK toolset approach is:

- **Synchronous**: No async/await conflicts
- **Official**: Uses Google's first-party tools  
- **Production Ready**: Proper authentication and configuration
- **Feature Rich**: Includes AI-powered data insights

## Testing

### ADK Integration Tests (Recommended)
```bash
cd ..
python test_bigquery_integration.py
```

### Legacy Tests (For Reference)
```bash
python test_bigquery.py
```

The legacy test may show import errors for old functions - this is expected with the new ADK implementation.

## Environment Setup

Set these environment variables:
```bash
export USE_BIGQUERY=true
export GOOGLE_CLOUD_PROJECT=your-project-id
```

For detailed setup instructions, see `BIGQUERY_SETUP.md`.
