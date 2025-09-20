import json
import os
import boto3
import logging
from datetime import datetime
from statistics import mean, stdev, median
from collections import defaultdict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
INDICATOR = 'usdbrl'
BUCKET = os.environ.get('BUCKET_NAME', 'dl-economic-indicators-prod')
SILVER_PREFIX = 'silver'
GOLD_PREFIX = 'gold'

s3_client = boto3.client('s3')

def calculate_statistics(data_points):
    """Calculate basic statistical metrics for indicator data"""
    if not data_points:
        return {}
    
    values = [float(point['value']) for point in data_points if point.get('value')]
    if not values:
        return {}
    
    return {
        'count': len(values),
        'min': min(values),
        'max': max(values),
        'mean': mean(values),
        'std_dev': stdev(values) if len(values) > 1 else 0.0,
        'latest_value': values[-1] if values else None,
        'first_date': data_points[0].get('ref_date') if data_points else None,
        'last_date': data_points[-1].get('ref_date') if data_points else None
    }

def calculate_technical_indicators(data_points):
    """Calculate advanced technical indicators from time series data"""
    if len(data_points) < 7:
        return {}
    
    # Extract values and dates
    values = []
    dates = []
    for point in data_points:
        if point.get('value') and point.get('ref_date'):
            try:
                values.append(float(point['value']))
                dates.append(datetime.strptime(point['ref_date'], '%Y-%m-%d'))
            except (ValueError, TypeError):
                continue
    
    if len(values) < 7:
        return {}
    
    # Calculate various indicators
    indicators = {}
    
    # Moving averages
    if len(values) >= 7:
        indicators['ma_7'] = mean(values[-7:])
    if len(values) >= 30:
        indicators['ma_30'] = mean(values[-30:])
    if len(values) >= 90:
        indicators['ma_90'] = mean(values[-90:])
    
    # Daily returns (percentage change)
    daily_returns = []
    for i in range(1, len(values)):
        return_pct = ((values[i] - values[i-1]) / values[i-1]) * 100
        daily_returns.append(return_pct)
    
    if daily_returns:
        indicators['avg_daily_return'] = mean(daily_returns)
        indicators['daily_volatility'] = stdev(daily_returns) if len(daily_returns) > 1 else 0
        indicators['max_daily_gain'] = max(daily_returns)
        indicators['max_daily_loss'] = min(daily_returns)
    
    # Rolling volatility (30-day if available)
    if len(daily_returns) >= 30:
        recent_returns = daily_returns[-30:]
        indicators['rolling_volatility_30d'] = stdev(recent_returns)
        indicators['annualized_volatility'] = stdev(recent_returns) * (252 ** 0.5)  # 252 trading days
    
    # Momentum indicators
    if len(values) >= 7:
        momentum_7d = ((values[-1] - values[-7]) / values[-7]) * 100
        indicators['momentum_7d'] = momentum_7d
    
    if len(values) >= 30:
        momentum_30d = ((values[-1] - values[-30]) / values[-30]) * 100
        indicators['momentum_30d'] = momentum_30d
    
    # Drawdown calculation (maximum drop from peak)
    peak = values[0]
    max_drawdown = 0
    for value in values:
        if value > peak:
            peak = value
        drawdown = ((peak - value) / peak) * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    indicators['max_drawdown_pct'] = max_drawdown
    
    # Support and resistance levels (psychological levels)
    indicators['resistance_level'] = max(values[-30:]) if len(values) >= 30 else max(values)
    indicators['support_level'] = min(values[-30:]) if len(values) >= 30 else min(values)
    
    # Trend analysis (simple linear regression slope)
    if len(values) >= 10:
        x_values = list(range(len(values)))
        n = len(values)
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        indicators['trend_slope'] = slope
        indicators['trend_direction'] = 'bullish' if slope > 0 else 'bearish' if slope < 0 else 'sideways'
    
    return indicators

def calculate_seasonal_patterns(data_points):
    """Calculate seasonal patterns and day-of-week effects"""
    if len(data_points) < 30:
        return {}
    
    # Group by weekday and month
    weekday_values = defaultdict(list)
    monthly_values = defaultdict(list)
    
    for point in data_points:
        if not point.get('value') or not point.get('ref_date'):
            continue
        
        try:
            value = float(point['value'])
            date_obj = datetime.strptime(point['ref_date'], '%Y-%m-%d')
            
            weekday = date_obj.strftime('%A')  # Monday, Tuesday, etc.
            month = date_obj.strftime('%B')    # January, February, etc.
            
            weekday_values[weekday].append(value)
            monthly_values[month].append(value)
            
        except (ValueError, TypeError):
            continue
    
    seasonal_patterns = {}
    
    # Calculate weekday averages
    weekday_avg = {}
    for day, values in weekday_values.items():
        if values:
            weekday_avg[day] = {
                'average': mean(values),
                'count': len(values),
                'volatility': stdev(values) if len(values) > 1 else 0
            }
    
    seasonal_patterns['weekday_patterns'] = weekday_avg
    
    # Calculate monthly averages
    monthly_avg = {}
    for month, values in monthly_values.items():
        if values:
            monthly_avg[month] = {
                'average': mean(values),
                'count': len(values),
                'volatility': stdev(values) if len(values) > 1 else 0
            }
    
    seasonal_patterns['monthly_patterns'] = monthly_avg
    
    return seasonal_patterns

def create_monthly_aggregations(data_points):
    """Create monthly aggregations from daily data"""
    monthly_data = defaultdict(list)
    
    for point in data_points:
        if not point.get('ref_date') or not point.get('value'):
            continue
            
        # Extract year-month from date
        date_str = point['ref_date']
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
            monthly_data[month_key].append(float(point['value']))
        except (ValueError, TypeError):
            continue
    
    # Calculate monthly statistics
    monthly_aggregations = []
    for month, values in monthly_data.items():
        if values:
            monthly_aggregations.append({
                'period': month,
                'period_type': 'monthly',
                'count': len(values),
                'avg_value': mean(values),
                'min_value': min(values),
                'max_value': max(values),
                'volatility': stdev(values) if len(values) > 1 else 0.0,
                'first_value': values[0],
                'last_value': values[-1]
            })
    
    return sorted(monthly_aggregations, key=lambda x: x['period'])

def create_yearly_aggregations(data_points):
    """Create yearly aggregations from daily data"""
    yearly_data = defaultdict(list)
    
    for point in data_points:
        if not point.get('ref_date') or not point.get('value'):
            continue
            
        try:
            ref_date = datetime.strptime(point['ref_date'], '%Y-%m-%d')
            year = ref_date.year
            value = float(point['value'])
            yearly_data[year].append(value)
        except (ValueError, TypeError):
            continue
    
    yearly_result = {}
    for year in sorted(yearly_data.keys()):
        values = yearly_data[year]
        if values:
            yearly_result[str(year)] = {
                'year': year,
                'open': values[0],
                'high': max(values),
                'low': min(values),
                'close': values[-1],
                'average': mean(values),
                'median': median(values),
                'count': len(values),
                'volatility': stdev(values) if len(values) > 1 else 0,
                'yearly_return': ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
            }
    
    return yearly_result

def lambda_handler(event, context):
    """Process Silver layer data to Gold layer with business aggregations"""
    try:
        logger.info("Starting Silver to Gold processing")
        
        # Find the most recent silver file
        silver_files = s3_client.list_objects_v2(
            Bucket=BUCKET,
            Prefix=f"{SILVER_PREFIX}/{INDICATOR}/",
            Delimiter='/'
        )
        
        if 'Contents' not in silver_files or not silver_files['Contents']:
            logger.warning("No silver files found")
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'No silver data found'})
            }
        
        # Get latest file
        latest_file = max(silver_files['Contents'], key=lambda x: x['LastModified'])['Key']
        logger.info(f"Processing latest silver file: {latest_file}")
        
        # Read silver data
        response = s3_client.get_object(Bucket=BUCKET, Key=latest_file)
        silver_data = json.loads(response['Body'].read())
        
        # Silver data is a list of records, not a dict with 'data' key
        if isinstance(silver_data, list):
            data_points = silver_data
        else:
            data_points = silver_data.get('data', [])
            
        if not data_points:
            logger.warning("No data points found in silver file")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'No data points in silver file'})
            }
        
        # Calculate business intelligence metrics
        stats = calculate_statistics(data_points)
        technical_indicators = calculate_technical_indicators(data_points)
        seasonal_patterns = calculate_seasonal_patterns(data_points)
        
        logger.info(f"Calculated analytics for {stats.get('count', 0)} data points")
        
        timestamp = datetime.utcnow()
        
        # Create enhanced summary with business intelligence
        latest_summary = {
            'indicator': INDICATOR,
            'last_updated': timestamp.isoformat(),
            'latest_value': stats.get('latest_value'),
            'latest_date': stats.get('last_date'),
            'trend': technical_indicators.get('trend_direction', 'unknown'),
            'momentum_7d': technical_indicators.get('momentum_7d', 0),
            'volatility': technical_indicators.get('daily_volatility', 0),
            'support_level': technical_indicators.get('support_level'),
            'resistance_level': technical_indicators.get('resistance_level'),
            'data_quality_score': 1.0,
            'statistics': stats,
            'risk_metrics': {
                'max_drawdown': technical_indicators.get('max_drawdown_pct', 0),
                'volatility_30d': technical_indicators.get('rolling_volatility_30d', 0)
            }
        }
        
        # Store enhanced Gold layer artifacts
        
        # 1. Metadata with comprehensive statistics
        metadata_key = f"{GOLD_PREFIX}/metadata/{INDICATOR}.json"
        metadata = {
            'indicator': INDICATOR,
            'name': 'USD-BRL Exchange Rate',
            'source': 'Banco Central do Brasil',
            'last_updated': timestamp.isoformat(),
            'data_range': {
                'start_date': stats.get('first_date'),
                'end_date': stats.get('last_date'),
                'total_records': stats.get('count', 0)
            },
            'quality_metrics': {
                'completeness': 1.0,
                'consistency': 1.0,
                'timeliness': 1.0
            },
            'update_frequency': 'daily',
            'schema_version': '1.0'
        }
        
        s3_client.put_object(
            Bucket=BUCKET,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2, ensure_ascii=False, default=str),
            ContentType='application/json'
        )
        
        # 2. Aggregations for different time periods
        aggregations_key = f"{GOLD_PREFIX}/aggregations/{INDICATOR}_monthly.json"
        monthly_agg = create_monthly_aggregations(data_points)
        s3_client.put_object(
            Bucket=BUCKET,
            Key=aggregations_key,
            Body=json.dumps(monthly_agg, indent=2, ensure_ascii=False, default=str),
            ContentType='application/json'
        )
        
        yearly_agg_key = f"{GOLD_PREFIX}/aggregations/{INDICATOR}_yearly.json"
        yearly_agg = create_yearly_aggregations(data_points)
        s3_client.put_object(
            Bucket=BUCKET,
            Key=yearly_agg_key,
            Body=json.dumps(yearly_agg, indent=2, ensure_ascii=False, default=str),
            ContentType='application/json'
        )
        
        # 3. Technical analysis
        technical_key = f"{GOLD_PREFIX}/technical/{INDICATOR}_indicators.json"
        s3_client.put_object(
            Bucket=BUCKET,
            Key=technical_key,
            Body=json.dumps(technical_indicators, indent=2, ensure_ascii=False, default=str),
            ContentType='application/json'
        )
        
        # 4. Seasonal patterns
        seasonal_key = f"{GOLD_PREFIX}/seasonal/{INDICATOR}_patterns.json"
        s3_client.put_object(
            Bucket=BUCKET,
            Key=seasonal_key,
            Body=json.dumps(seasonal_patterns, indent=2, ensure_ascii=False, default=str),
            ContentType='application/json'
        )
        
        # 5. Latest summary for API consumption
        summary_key = f"{GOLD_PREFIX}/{INDICATOR}/summary/latest_summary.json"
        
        s3_client.put_object(
            Bucket=BUCKET,
            Key=summary_key,
            Body=json.dumps(latest_summary, indent=2, ensure_ascii=False, default=str),
            ContentType='application/json'
        )
        
        # Store Gold layer summary (legacy compatibility)
        gold_key = f"{GOLD_PREFIX}/{INDICATOR}/summary.json"
        gold_summary = {
            'indicator': INDICATOR,
            'name': 'USD-BRL Exchange Rate',
            'last_updated': timestamp.isoformat(),
            'statistics': stats,
            'data_quality': 'valid',
            'total_records': len(data_points)
        }
        s3_client.put_object(
            Bucket=BUCKET,
            Key=gold_key,
            Body=json.dumps(gold_summary, indent=2, ensure_ascii=False, default=str),
            ContentType='application/json'
        )
        
        logger.info(f"Successfully created Gold layer artifacts:")
        logger.info(f"  - Metadata: {metadata_key}")
        logger.info(f"  - Monthly Aggregations: {aggregations_key}")
        logger.info(f"  - Yearly Aggregations: {yearly_agg_key}")
        logger.info(f"  - Technical Indicators: {technical_key}")
        logger.info(f"  - Seasonal Patterns: {seasonal_key}")
        logger.info(f"  - Summary: {summary_key}")
        logger.info(f"  - Legacy Summary: {gold_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed Silver to Gold with business intelligence artifacts',
                'silver_file': latest_file,
                'gold_artifacts': {
                    'metadata': metadata_key,
                    'monthly_aggregations': aggregations_key,
                    'yearly_aggregations': yearly_agg_key,
                    'technical_indicators': technical_key,
                    'seasonal_patterns': seasonal_key,
                    'summary': summary_key,
                    'legacy_summary': gold_key
                },
                'indicator': INDICATOR,
                'statistics': stats,
                'technical_summary': {
                    'trend': technical_indicators.get('trend_direction'),
                    'volatility': technical_indicators.get('daily_volatility'),
                    'momentum_7d': technical_indicators.get('momentum_7d')
                }
            }, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error processing Silver to Gold: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Error processing data: {str(e)}'})
        }