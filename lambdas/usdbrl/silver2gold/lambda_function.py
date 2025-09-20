import json
import os
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
INDICATOR = 'usdbrl'
BUCKET = os.environ.get('BUCKET_NAME', 'dl-economic-indicators-prod')
SILVER_PREFIX = 'silver'
GOLD_PREFIX = 'gold'

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Simplified USD-BRL Silver to Gold processing
    For testing pipeline - just copies silver data to gold layer
    """
    try:
        logger.info(f"Processing Silver to Gold for {INDICATOR}")
        
        # Get the most recent Silver file for USD-BRL
        response = s3_client.list_objects_v2(
            Bucket=BUCKET,
            Prefix=f"{SILVER_PREFIX}/{INDICATOR}/",
            MaxKeys=1000
        )
        
        if 'Contents' not in response:
            logger.warning("No Silver files found for USD-BRL")
            return {
                'statusCode': 200,
                'body': json.dumps('No Silver files found')
            }
        
        # Sort by last modified to get most recent
        silver_files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
        
        if not silver_files:
            logger.warning("No Silver files to process")
            return {
                'statusCode': 200,
                'body': json.dumps('No files to process')
            }
        
        # Process most recent file
        latest_file = silver_files[0]['Key']
        logger.info(f"Processing file: {latest_file}")
        
        # Read silver data
        silver_response = s3_client.get_object(Bucket=BUCKET, Key=latest_file)
        silver_data = json.loads(silver_response['Body'].read().decode('utf-8'))
        
        # Simple transformation: add gold layer metadata
        gold_data = {
            'indicator': INDICATOR,
            'processed_at': datetime.utcnow().isoformat(),
            'source_file': latest_file,
            'data': silver_data,
            'transformations': {
                'layer': 'gold',
                'description': 'Basic copy from silver to gold for pipeline testing'
            }
        }
        
        # Save to Gold layer
        timestamp = datetime.utcnow()
        gold_key = f"{GOLD_PREFIX}/{INDICATOR}/{timestamp.strftime('%Y/%m/%d')}/usdbrl_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        s3_client.put_object(
            Bucket=BUCKET,
            Key=gold_key,
            Body=json.dumps(gold_data, indent=2, ensure_ascii=False),
            ContentType='application/json'
        )
        
        logger.info(f"Successfully saved to Gold layer: {gold_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed Silver to Gold',
                'silver_file': latest_file,
                'gold_file': gold_key,
                'indicator': INDICATOR
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing Silver to Gold: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }