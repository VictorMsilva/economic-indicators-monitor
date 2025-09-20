"""
USD-BRL Exchange Rate Monitor Lambda

This script checks the Banco Central do Brasil SGS API for updates to the USD-BRL exchange rate
and stores new data in the Bronze layer when changes are detected.
"""

import json
import os
import requests
import logging
from datetime import datetime, timedelta
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
INDICATOR = 'usdbrl'
BRONZE_BUCKET = os.environ.get('BUCKET_NAME', 'dl-economic-indicators-prod')
BRONZE_PREFIX = os.environ.get('BRONZE_PREFIX', 'bronze')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'sgs-indicators-state')

# USD-BRL Indicator Configuration
USDBRL_CONFIG = {
    "series_id": 1, 
    "name": "USD-BRL Exchange Rate",
    "description": "Daily exchange rate between US Dollar and Brazilian Real",
    "frequency": "daily",
    "check_interval_minutes": 60,
    "source": {
        "api_endpoint": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados?formato=json",
        "parameters": {
            "inicio": "01/01/2020", 
            "fim": "" 
        }
    }
}

def load_config(indicator_name):
    """
    Load configuration for a specific indicator
    """
    try:
        if indicator_name == 'usdbrl':
            return USDBRL_CONFIG
        else:
            raise ValueError(f"Indicator {indicator_name} not supported")
        
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise

def fetch_from_sgs_api(config):
    """
    Fetch data from SGS API in 10-year windows using dataInicial/dataFinal parameters.
    """
    series_id = config['series_id']
    api_url = config['source']['api_endpoint'].replace('{series_id}', str(series_id))


    # Get date range from config or use defaults
    params = config['source']['parameters']
    # Use default if missing or empty
    start_str = params.get('dataInicial') or params.get('inicio') or '01/01/2015'
    end_str = params.get('dataFinal') or params.get('fim') or datetime.now().strftime('%d/%m/%Y')

    # Parse dates
    try:
        start_date = datetime.strptime(start_str, '%d/%m/%Y')
    except Exception:
        logger.warning(f"Invalid or missing start date, using default 01/01/2015")
        start_date = datetime.strptime('01/01/2015', '%d/%m/%Y')
    try:
        end_date = datetime.strptime(end_str, '%d/%m/%Y')
    except Exception:
        logger.warning(f"Invalid or missing end date, using today")
        end_date = datetime.now()

    all_data = []
    window_years = 10
    current_start = start_date

    # Loop over the date range in 10-year windows
    while current_start <= end_date:
        # Calculate window end (max 10 years ahead, or end_date)
        window_end = min(current_start.replace(year=current_start.year + window_years), end_date)
        # Prepare request parameters
        req_params = {
            'formato': 'json',
            'dataInicial': current_start.strftime('%d/%m/%Y'),
            'dataFinal': window_end.strftime('%d/%m/%Y')
        }
        headers = {"Accept": "application/json"}
        try:
            response = requests.get(api_url, params=req_params, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Fetched {len(data)} records from SGS API for {req_params['dataInicial']} to {req_params['dataFinal']}")
            all_data.extend(data)
        except Exception as e:
            logger.error(f"Error fetching data from SGS API for {req_params['dataInicial']} to {req_params['dataFinal']}: {str(e)}")
            raise
        # Move to next window
        current_start = window_end + timedelta(days=1)

    return all_data

def transform_to_bronze_format(raw_data, config):
    """
    Transform SGS API response to Bronze layer format
    """
    transformed = []
    for item in raw_data:
        # SGS API returns dates as "dd/mm/yyyy" and values as strings
        try:
            # Parse date from "dd/mm/yyyy" to ISO format "yyyy-mm-dd"
            date_parts = item.get('data', '').split('/')
            if len(date_parts) == 3:
                iso_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
            else:
                iso_date = None
                
            # Convert value to float
            value = float(item.get('valor', '').replace(',', '.'))
            
            transformed.append({
                'series_id': config['series_id'],
                'ref_date': iso_date,
                'value': value,
                'raw_payload': item,
                'ingest_ts': datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"Error transforming record {item}: {str(e)}")
    
    return transformed

def has_new_data(transformed_data, last_known_state):
    """
    Check if there's new data compared to the last known state
    """
    if not last_known_state or not last_known_state.get('latest_value'):
        return True
    
    # Get latest date in the new data
    latest_record = max(transformed_data, key=lambda x: x['ref_date'])
    
    # Check if we have a newer date or different value for the same date
    if latest_record['ref_date'] > last_known_state.get('latest_date', ''):
        return True
    
    if (latest_record['ref_date'] == last_known_state.get('latest_date') and 
        abs(latest_record['value'] - last_known_state.get('latest_value', 0)) > 0.0001):
        return True
    
    return False

def save_to_bronze(transformed_data, config):
    """
    Save data to Bronze layer (S3)
    """
    # Generate filename with timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{INDICATOR}_{timestamp}.json"
    s3_key = f"{BRONZE_PREFIX}/{INDICATOR}/{filename}"
    
    try:
        # Convert data to JSON string
        json_data = json.dumps(transformed_data)
        
        # Create S3 client and upload data
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Body=json_data,
            Bucket=BRONZE_BUCKET,
            Key=s3_key,
            ContentType='application/json'
        )
        
        logger.info(f"Saved {len(transformed_data)} records to s3://{BRONZE_BUCKET}/{s3_key}")
        return f"s3://{BRONZE_BUCKET}/{s3_key}"
    except Exception as e:
        logger.error(f"Error saving to S3: {str(e)}")
        raise

def update_state(transformed_data):
    """
    Update the state in DynamoDB with the latest processed data
    """
    try:
        # Get latest record
        latest_record = max(transformed_data, key=lambda x: x['ref_date'])
        
        # Prepare DynamoDB item
        item = {
            'indicator': INDICATOR,
            'latest_date': latest_record['ref_date'],
            'latest_value': latest_record['value'],
            'last_updated': datetime.now().isoformat()
        }
        
        # Create DynamoDB client and update item
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        response = table.put_item(Item=item)
        
        logger.info(f"State updated in DynamoDB: latest_date={latest_record['ref_date']}, latest_value={latest_record['value']}")
        return True
    except Exception as e:
        logger.error(f"Error updating state in DynamoDB: {str(e)}")
        # Don't raise exception here, as this is a non-critical operation
        return False

def lambda_handler(event, context):
    """
    Main Lambda handler
    """
    try:
        # Load configuration for USD-BRL
        config = load_config(INDICATOR)
        
        # Fetch data from SGS API
        raw_data = fetch_from_sgs_api(config)
        
        # Transform data to Bronze format
        transformed_data = transform_to_bronze_format(raw_data, config)
        
        # In real implementation, get the last known state from DynamoDB
        last_known_state = None  # Mock empty state
        
        # Check if there's new data
        if has_new_data(transformed_data, last_known_state):
            # Save to Bronze layer
            filepath = save_to_bronze(transformed_data, config)
            
            # Update state
            update_state(transformed_data)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'New data detected and saved to Bronze layer',
                    'records': len(transformed_data),
                    'filepath': filepath
                })
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No new data detected',
                    'records': len(transformed_data)
                })
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

# No local testing code for AWS deployment
