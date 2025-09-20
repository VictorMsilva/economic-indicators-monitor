import json
import os
import boto3
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
INDICATOR = 'usdbrl'
BUCKET = os.environ.get('BUCKET', 'dl-economic-indicators-prod')
SILVER_PREFIX = os.environ.get('SILVER_PREFIX', 'silver')
GOLD_PREFIX = os.environ.get('GOLD_PREFIX', 'gold')

s3_client = boto3.client('s3')

def get_silver_data(days_back: int = 400) -> pd.DataFrame:
    """
    Retrieve USD-BRL data from Silver layer in S3
    Gets data from last N days to ensure we have enough for calculations
    """
    try:
        # List Silver files for USD-BRL
        response = s3_client.list_objects_v2(
            Bucket=BUCKET,
            Prefix=f"{SILVER_PREFIX}/{INDICATOR}/",
            MaxKeys=1000
        )
        
        if 'Contents' not in response:
            logger.warning("No Silver files found for USD-BRL")
            return pd.DataFrame()
        
        # Get recent files (last N files sorted by modification date)
        files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
        recent_files = files[:50]  # Get last 50 files to ensure coverage
        
        all_records = []
        
        for file_obj in recent_files:
            try:
                # Read JSON file from S3
                obj_response = s3_client.get_object(Bucket=BUCKET, Key=file_obj['Key'])
                data = json.loads(obj_response['Body'].read().decode('utf-8'))
                
                if isinstance(data, list):
                    all_records.extend(data)
                else:
                    all_records.append(data)
                    
            except Exception as e:
                logger.error(f"Error reading file {file_obj['Key']}: {str(e)}")
                continue
        
        if not all_records:
            logger.warning("No data found in Silver files")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_records)
        
        # Ensure required columns exist
        required_cols = ['ref_date', 'value']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        # Data cleaning and conversion
        df['ref_date'] = pd.to_datetime(df['ref_date']).dt.date
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # Remove duplicates and invalid data
        df = df.drop_duplicates(subset=['ref_date']).dropna(subset=['value'])
        
        # Sort by date and filter recent data
        df = df.sort_values('ref_date')
        cutoff_date = datetime.now().date() - timedelta(days=days_back)
        df = df[df['ref_date'] >= cutoff_date]
        
        logger.info(f"Retrieved {len(df)} records from Silver layer")
        return df
        
    except Exception as e:
        logger.error(f"Error retrieving Silver data: {str(e)}")
        raise

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Gold layer indicators for USD-BRL"""
    try:
        if df.empty:
            return pd.DataFrame()
        
        # Sort by date to ensure proper calculations
        df = df.sort_values('ref_date').reset_index(drop=True)
        
        # Base columns
        result_df = pd.DataFrame({
            'ref_date': df['ref_date'],
            'usd_brl': df['value'].round(4)
        })
        
        # 1. Daily variation percentage
        result_df['var_dia_pct'] = df['value'].pct_change() * 100
        result_df['var_dia_pct'] = result_df['var_dia_pct'].round(2)
        
        # 2. Monthly variation percentage (accumulated in month)
        df_temp = df.copy()
        df_temp['year_month'] = pd.to_datetime(df_temp['ref_date']).dt.to_period('M')
        df_temp['month_first_value'] = df_temp.groupby('year_month')['value'].transform('first')
        result_df['var_mes_pct'] = ((df_temp['value'] - df_temp['month_first_value']) / df_temp['month_first_value'] * 100).round(2)
        
        # 3. Moving averages
        result_df['mm7'] = df['value'].rolling(window=7, min_periods=1).mean().round(4)
        result_df['mm30'] = df['value'].rolling(window=30, min_periods=1).mean().round(4)
        
        # 4. 7-day volatility (standard deviation)
        result_df['vol_7d'] = df['value'].rolling(window=7, min_periods=1).std().round(4)
        
        # 5. Monthly max and min
        df_temp = df.copy()
        df_temp['year_month'] = pd.to_datetime(df_temp['ref_date']).dt.to_period('M')
        monthly_stats = df_temp.groupby('year_month')['value'].agg(['max', 'min']).reset_index()
        monthly_stats.columns = ['year_month', 'max_mes', 'min_mes']
        
        # Merge monthly stats back to main dataframe
        df_temp = df_temp.merge(monthly_stats, on='year_month', how='left')
        result_df['max_mes'] = df_temp['max_mes'].round(4)
        result_df['min_mes'] = df_temp['min_mes'].round(4)
        
        # Add metadata columns
        result_df['processed_at'] = datetime.now().isoformat()
        result_df['source'] = 'silver_layer'
        result_df['indicator'] = INDICATOR
        
        # Filter to recent data only (last 90 days for Gold layer)
        cutoff_date = datetime.now().date() - timedelta(days=90)
        result_df = result_df[result_df['ref_date'] >= cutoff_date]
        
        logger.info(f"Calculated indicators for {len(result_df)} records")
        return result_df
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        raise

def save_to_gold(df: pd.DataFrame) -> str:
    """Save Gold layer data as Parquet to S3"""
    try:
        if df.empty:
            raise ValueError("No data to save to Gold layer")
        
        # Convert date column to string for Parquet compatibility
        df_save = df.copy()
        df_save['ref_date'] = df_save['ref_date'].astype(str)
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{INDICATOR}_gold_{timestamp}.parquet"
        s3_key = f"{GOLD_PREFIX}/{INDICATOR}/{filename}"
        
        # Convert to Parquet
        table = pa.Table.from_pandas(df_save)
        parquet_buffer = BytesIO()
        pq.write_table(table, parquet_buffer)
        
        # Upload to S3
        s3_client.put_object(
            Body=parquet_buffer.getvalue(),
            Bucket=BUCKET,
            Key=s3_key,
            ContentType='application/octet-stream'
        )
        
        s3_path = f"s3://{BUCKET}/{s3_key}"
        logger.info(f"Saved {len(df)} Gold records to: {s3_path}")
        return s3_path
        
    except Exception as e:
        logger.error(f"Error saving to Gold layer: {str(e)}")
        raise

def lambda_handler(event, context):
    """Main Lambda handler for Silver to Gold processing"""
    try:
        logger.info(f"Starting Silver to Gold processing for {INDICATOR}")
        
        # Get Silver data
        silver_df = get_silver_data()
        
        if silver_df.empty:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No Silver data found for processing',
                    'indicator': INDICATOR,
                    'records_processed': 0
                })
            }
        
        # Calculate Gold indicators
        gold_df = calculate_indicators(silver_df)
        
        if gold_df.empty:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No Gold data generated',
                    'indicator': INDICATOR,
                    'silver_records': len(silver_df),
                    'gold_records': 0
                })
            }
        
        # Save to Gold layer
        gold_path = save_to_gold(gold_df)
        
        # Calculate summary statistics
        latest_record = gold_df.iloc[-1]
        summary_stats = {
            'latest_date': str(latest_record['ref_date']),
            'latest_value': float(latest_record['usd_brl']),
            'daily_variation': float(latest_record['var_dia_pct']) if pd.notna(latest_record['var_dia_pct']) else None,
            'monthly_variation': float(latest_record['var_mes_pct']) if pd.notna(latest_record['var_mes_pct']) else None,
            'ma7': float(latest_record['mm7']),
            'ma30': float(latest_record['mm30']),
            'volatility_7d': float(latest_record['vol_7d']) if pd.notna(latest_record['vol_7d']) else None
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Silver to Gold processing completed successfully',
                'indicator': INDICATOR,
                'silver_records': len(silver_df),
                'gold_records': len(gold_df),
                'gold_path': gold_path,
                'summary_stats': summary_stats,
                'processed_at': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in Silver to Gold processing: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'indicator': INDICATOR,
                'processed_at': datetime.now().isoformat()
            })
        }