"""
S3 Events module for Economic Indicators Pipeline
Configures S3 bucket notifications to EventBridge for all indicators
"""
from aws_cdk import (
    aws_s3 as s3,
)
from constructs import Construct


class S3Events:
    """Configures S3 event notifications for the data lake"""

    @staticmethod
    def setup_indicator_events(data_lake_bucket: s3.Bucket, indicator: str):
        """Configure S3 bucket to send events to EventBridge for a specific indicator"""
        
        # Enable EventBridge notifications for the bucket
        # This is done at bucket level - no need for specific destinations
        data_lake_bucket.enable_event_bridge_notification()
        
        print(f"✅ S3 EventBridge notifications configured for indicator: {indicator}")
        
        return {
            'bronze_notification': f"bronze/{indicator}/ → EventBridge",
            'silver_notification': f"silver/{indicator}/ → EventBridge",
            'eventbridge_enabled': True
        }
    
    @staticmethod
    def setup_usdbrl_events(data_lake_bucket: s3.Bucket):
        """Setup S3 events specifically for USD-BRL indicator"""
        return S3Events.setup_indicator_events(data_lake_bucket, "usdbrl")