import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
INDICATOR = 'usdbrl'
BUCKET = os.environ.get('BUCKET', 'dl-economic-indicators-prod')
BRONZE_PREFIX = os.environ.get('BRONZE_PREFIX', 'bronze')
SILVER_PREFIX = os.environ.get('SILVER_PREFIX', 'silver')
QUARANTINE_PREFIX = os.environ.get('QUARANTINE_PREFIX', 'quarantine')

s3_client = boto3.client('s3')

def validate_record(record: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate USD-BRL record with embedded rules"""
    errors = []
    
    # Required fields
    required_fields = ['series_id', 'ref_date', 'value']
    for field in required_fields:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate value type and positivity
    if 'value' in record:
        try:
            value = float(record['value'])
            if value <= 0:
                errors.append("Exchange rate must be positive")
        except (ValueError, TypeError):
            errors.append("Value must be a valid number")
    
    # Validate date format
    if 'ref_date' in record:
        try:
            datetime.strptime(record['ref_date'], '%Y-%m-%d')
        except ValueError:
            errors.append("Date must be in YYYY-MM-DD format")
    
    return len(errors) == 0, errors

def transform_to_silver_format(record: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Bronze record to Silver format"""
    try:
        return {
            'series_id': int(record['series_id']),
            'indicator': INDICATOR,
            'ref_date': record['ref_date'],
            'value': float(record['value']),
            'source': 'bacen_sgs',
            'processed_at': datetime.now().isoformat(),
            'data_quality': 'valid'
        }
    except Exception as e:
        logger.error(f"Error transforming record: {str(e)}")
        raise

def save_to_silver(records: List[Dict[str, Any]]) -> str:
    """Save validated records to Silver layer"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{INDICATOR}_{timestamp}.json"
    s3_key = f"{SILVER_PREFIX}/{INDICATOR}/{filename}"
    
    try:
        json_data = json.dumps(records, indent=2)
        s3_client.put_object(
            Body=json_data,
            Bucket=BUCKET,
            Key=s3_key,
            ContentType='application/json'
        )
        
        logger.info(f"Saved {len(records)} records to Silver: s3://{BUCKET}/{s3_key}")
        return f"s3://{BUCKET}/{s3_key}"
    except Exception as e:
        logger.error(f"Error saving to Silver: {str(e)}")
        raise

def save_to_quarantine(records: List[Dict[str, Any]]) -> Optional[str]:
    """Save invalid records to quarantine"""
    if not records:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{INDICATOR}_quarantine_{timestamp}.json"
    s3_key = f"{QUARANTINE_PREFIX}/{INDICATOR}/{filename}"
    
    try:
        json_data = json.dumps(records, indent=2)
        s3_client.put_object(
            Body=json_data,
            Bucket=BUCKET,
            Key=s3_key,
            ContentType='application/json'
        )
        
        logger.warning(f"Quarantined {len(records)} invalid records: s3://{BUCKET}/{s3_key}")
        return f"s3://{BUCKET}/{s3_key}"
    except Exception as e:
        logger.error(f"Error saving to quarantine: {str(e)}")
        raise

def process_bronze_file(bronze_s3_key: str) -> Dict[str, Any]:
    """Process a Bronze file and apply DQ rules"""
    # Read Bronze file
    response = s3_client.get_object(Bucket=BUCKET, Key=bronze_s3_key)
    bronze_data = json.loads(response['Body'].read().decode('utf-8'))
    
    valid_records = []
    invalid_records = []
    
    # Process each record
    for record in bronze_data:
        is_valid, errors = validate_record(record)
        
        if is_valid:
            # Transform to Silver format
            silver_record = transform_to_silver_format(record)
            valid_records.append(silver_record)
        else:
            # Add to quarantine with error details
            quarantine_record = {
                **record,
                'dq_status': 'invalid',
                'dq_errors': errors,
                'quarantined_at': datetime.now().isoformat(),
                'source_file': bronze_s3_key
            }
            invalid_records.append(quarantine_record)
    
    # Save results
    silver_path = None
    quarantine_path = None
    
    if valid_records:
        silver_path = save_to_silver(valid_records)
    
    if invalid_records:
        quarantine_path = save_to_quarantine(invalid_records)
    
    return {
        'total_records': len(bronze_data),
        'valid_records': len(valid_records),
        'invalid_records': len(invalid_records),
        'silver_path': silver_path,
        'quarantine_path': quarantine_path
    }

def lambda_handler(event, context):
    """Main Lambda handler for Bronze to Silver processing"""
    try:
        # Parse S3 event
        if 'Records' in event:
            # Triggered by S3 event
            s3_event = event['Records'][0]['s3']
            bronze_s3_key = s3_event['object']['key']
        else:
            # Direct invocation
            bronze_s3_key = event.get('s3_key')
            if not bronze_s3_key:
                raise ValueError("Missing s3_key in event")
        
        logger.info(f"Processing Bronze file: {bronze_s3_key}")
        
        # Process the file
        result = process_bronze_file(bronze_s3_key)
        
        logger.info(f"Processing complete: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Bronze to Silver processing completed',
                'indicator': INDICATOR,
                'source_file': bronze_s3_key,
                **result
            })
        }
        
    except Exception as e:
        logger.error(f"Error in bronze2silver processing: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'indicator': INDICATOR
            })
        }