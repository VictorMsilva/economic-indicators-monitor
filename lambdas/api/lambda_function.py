import json
import os
import boto3
import logging
from typing import Dict, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'dl-economic-indicators-prod')
GOLD_PREFIX = 'gold'
s3_client = boto3.client('s3')

def cors_response(data, status_code=200):
    """Returns API response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(data)
    }

def get_available_indicators() -> List[str]:
    """Retrieves list of available indicators from S3 Gold layer"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"{GOLD_PREFIX}/",
            Delimiter='/'
        )
        
        indicators = []
        if 'CommonPrefixes' in response:
            for prefix in response['CommonPrefixes']:
                indicator = prefix['Prefix'].split('/')[1]
                indicators.append(indicator)
        
        return sorted(indicators)
    except Exception as e:
        logger.error(f"Error getting indicators: {str(e)}")
        return []

def get_indicator_data(indicator: str, limit: int = 10) -> List[Dict]:
    """Retrieves historical data for a specific indicator from S3 Gold layer"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"{GOLD_PREFIX}/{indicator}/",
            MaxKeys=100
        )
        
        if 'Contents' not in response:
            return []
        
        files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[:limit]
        
        indicator_data = []
        for file_obj in files:
            try:
                file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_obj['Key'])
                data = json.loads(file_response['Body'].read().decode('utf-8'))
                
                data['s3_key'] = file_obj['Key']
                data['last_modified'] = file_obj['LastModified'].isoformat()
                data['size'] = file_obj['Size']
                
                indicator_data.append(data)
            except Exception as e:
                logger.warning(f"Error reading file {file_obj['Key']}: {str(e)}")
                continue
        
        return indicator_data
    except Exception as e:
        logger.error(f"Error getting data for {indicator}: {str(e)}")
        return []

def get_indicator_summary(indicator: str) -> Dict:
    """Returns summary statistics and metadata for a specific indicator"""
    try:
        # Try to get the latest summary from Gold layer first
        summary_response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"{GOLD_PREFIX}/{indicator}/summary/",
            MaxKeys=1
        )
        
        if 'Contents' in summary_response and summary_response['Contents']:
            latest_summary = max(summary_response['Contents'], key=lambda x: x['LastModified'])
            file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=latest_summary['Key'])
            summary_data = json.loads(file_response['Body'].read().decode('utf-8'))
            return summary_data
        
        # Fallback to metadata if summary not available
        metadata_response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"{GOLD_PREFIX}/{indicator}/metadata/",
            MaxKeys=1
        )
        
        if 'Contents' in metadata_response and metadata_response['Contents']:
            latest_metadata = max(metadata_response['Contents'], key=lambda x: x['LastModified'])
            file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=latest_metadata['Key'])
            metadata = json.loads(file_response['Body'].read().decode('utf-8'))
            return metadata
        
        # Final fallback to old format
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"{GOLD_PREFIX}/{indicator}/",
            MaxKeys=1
        )
        
        if 'Contents' not in response or not response['Contents']:
            return {'indicator': indicator, 'status': 'no_data'}
        
        latest_file = max(response['Contents'], key=lambda x: x['LastModified'])
        file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=latest_file['Key'])
        data = json.loads(file_response['Body'].read().decode('utf-8'))
        
        summary = {
            'indicator': indicator,
            'status': 'active',
            'last_updated': latest_file['LastModified'].isoformat(),
            'latest_file': latest_file['Key'],
            'file_size': latest_file['Size'],
            'data_points': len(data.get('data', [])) if isinstance(data.get('data'), list) else 'unknown',
            'processed_at': data.get('processed_at')
        }
        
        if 'data' in data and isinstance(data['data'], list) and data['data']:
            last_record = data['data'][-1]
            summary.update({
                'latest_value': last_record.get('value'),
                'latest_date': last_record.get('ref_date')
            })
        
        return summary
    except Exception as e:
        logger.error(f"Error getting summary for {indicator}: {str(e)}")
        return {'indicator': indicator, 'status': 'error', 'message': str(e)}

def get_indicator_aggregations(indicator: str) -> Dict:
    """Retrieves all aggregations (monthly, yearly, technical, seasonal) for a specific indicator"""
    try:
        aggregations = {}
        
        # Get monthly aggregations
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"{GOLD_PREFIX}/aggregations/{indicator}_monthly.json")
            monthly_data = json.loads(response['Body'].read().decode('utf-8'))
            aggregations['monthly'] = monthly_data
        except Exception:
            aggregations['monthly'] = []
        
        # Get yearly aggregations
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"{GOLD_PREFIX}/aggregations/{indicator}_yearly.json")
            yearly_data = json.loads(response['Body'].read().decode('utf-8'))
            aggregations['yearly'] = yearly_data
        except Exception:
            aggregations['yearly'] = {}
        
        # Get technical indicators
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"{GOLD_PREFIX}/technical/{indicator}_indicators.json")
            technical_data = json.loads(response['Body'].read().decode('utf-8'))
            aggregations['technical_indicators'] = technical_data
        except Exception:
            aggregations['technical_indicators'] = {}
        
        # Get seasonal patterns
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"{GOLD_PREFIX}/seasonal/{indicator}_patterns.json")
            seasonal_data = json.loads(response['Body'].read().decode('utf-8'))
            aggregations['seasonal_patterns'] = seasonal_data
        except Exception:
            aggregations['seasonal_patterns'] = {}
        
        return aggregations
    except Exception as e:
        logger.error(f"Error getting aggregations for {indicator}: {str(e)}")
        return {}

def lambda_handler(event, context):
    """Main Lambda handler - routes API requests to appropriate functions"""
    try:
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters') or {}
        
        if http_method == 'OPTIONS':
            return cors_response({})
        
        if path == '/' or path == '/indicators':
            indicators = get_available_indicators()
            mode = query_params.get('mode', 'list')
            
            if mode == 'summary':
                summaries = []
                for indicator in indicators:
                    summary = get_indicator_summary(indicator)
                    summaries.append(summary)
                return cors_response({'indicators': summaries})
            else:
                return cors_response({'indicators': indicators})
                
        elif path.startswith('/indicators/'):
            indicator = path.split('/')[-1]
            mode = query_params.get('mode', 'data')
            limit = int(query_params.get('limit', 10))
            
            if mode == 'summary':
                summary = get_indicator_summary(indicator)
                return cors_response(summary)
            elif mode == 'aggregations':
                aggregations = get_indicator_aggregations(indicator)
                return cors_response({'indicator': indicator, 'aggregations': aggregations})
            else:
                data = get_indicator_data(indicator, limit)
                return cors_response({'indicator': indicator, 'data': data})
        else:
            return cors_response({"error": "Not found"}, 404)
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return cors_response({"error": "Internal server error"}, 500)