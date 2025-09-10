# BigQuery Setup Directory

This directory contains setup scripts and tools for configuring the BigQuery environment for the Cookie Delivery System.

## Files

- `create_bigquery_environment.py` - Main setup script that creates the BigQuery dataset, table, and populates sample data
- `test_bigquery.py` - Test script to validate BigQuery integration
- `requirements.txt` - Python dependencies for BigQuery setup
- `setup_dataset.sql` (if needed) - SQL scripts for manual setup

## Usage

### Automated Setup

The main setup script is called from the root `setup.sh` file, but can also be run independently:

```bash
# From the bigquery-setup directory
python create_bigquery_environment.py
```

### Prerequisites

1. Google Cloud Project with BigQuery API enabled
2. Authentication configured (via gcloud CLI or service account)
3. Environment variable `GOOGLE_CLOUD_PROJECT` set

### What Gets Created

1. **Dataset**: `cookie_delivery`
2. **Table**: `orders` with complete schema for order management
3. **Sample Data**: 3 sample orders for testing

The script will:
- Create the dataset if it doesn't exist
- Create the orders table with proper schema
- Insert sample data if the table is empty
- Verify the setup was successful

### Testing

Run the test script to validate the BigQuery integration:

```bash
python test_bigquery.py
```

This will test all CRUD operations and ensure the integration is working correctly.
