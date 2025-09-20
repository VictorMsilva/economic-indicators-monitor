"""
Orchestration module for USD-BRL Pipeline
Handles EventBridge Rules, SQS Queues, and scheduling
"""
from aws_cdk import (
    Duration,
    aws_events as events,
    aws_events_targets as targets,
    aws_sqs as sqs,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_events,
    aws_iam as iam,
    aws_scheduler as scheduler,
)
from constructs import Construct


class USDBRLOrchestration:
    """Creates orchestration resources for USD-BRL pipeline"""

    @staticmethod
    def create_orchestration(stack: Construct, lambda_functions: dict, data_lake_bucket):
        """Create all orchestration resources"""
        
        # SQS Queue for Silver to Gold processing
        silver2gold_queue = sqs.Queue(
            stack, "USDBRLSilver2GoldQueue",
            queue_name="sqs-usdbrl-silver2gold",
            visibility_timeout=Duration.minutes(5),  # Longer than Lambda timeout
            retention_period=Duration.days(14),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=sqs.Queue(
                    stack, "USDBRLSilver2GoldDLQ",
                    queue_name="sqs-usdbrl-silver2gold-dlq"
                )
            )
        )
        
        # Grant Lambda permission to consume from SQS
        silver2gold_queue.grant_consume_messages(lambda_functions['silver2gold'])
        
        # Configure SQS trigger for Silver2Gold Lambda
        lambda_functions['silver2gold'].add_event_source(
            lambda_events.SqsEventSource(silver2gold_queue, batch_size=1)
        )
        
        # EventBridge Rule: S3 Bronze → Lambda Bronze2Silver
        bronze_rule = events.Rule(
            stack, "USDBRLBronzeRule",
            rule_name="usdbrl-bronze-to-silver",
            description="Triggers Bronze2Silver when new Bronze data arrives",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {"name": [data_lake_bucket.bucket_name]},
                    "object": {"key": [{"prefix": "bronze/usdbrl/"}]}
                }
            )
        )
        
        # Add Lambda target to Bronze rule
        bronze_rule.add_target(
            targets.LambdaFunction(lambda_functions['bronze2silver'])
        )
        
        # EventBridge Rule: S3 Silver → SQS
        silver_rule = events.Rule(
            stack, "USDBRLSilverRule", 
            rule_name="usdbrl-silver-to-gold",
            description="Sends message to SQS when new Silver data arrives",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {"name": [data_lake_bucket.bucket_name]},
                    "object": {"key": [{"prefix": "silver/usdbrl/"}]}
                }
            )
        )
        
        # Add SQS target to Silver rule
        silver_rule.add_target(
            targets.SqsQueue(silver2gold_queue)
        )
        
        # EventBridge Scheduler: Daily Monitor trigger
        # Note: Using EventBridge Rule with schedule instead of Scheduler for simplicity
        monitor_schedule = events.Rule(
            stack, "USDBRLMonitorSchedule",
            rule_name="usdbrl-monitor-daily",
            description="Triggers USD-BRL monitor daily at 9 AM",
            schedule=events.Schedule.cron(
                minute="0",
                hour="9", 
                day="*",
                month="*",
                year="*"
            )
        )
        
        # Add Lambda target to schedule
        monitor_schedule.add_target(
            targets.LambdaFunction(lambda_functions['monitor'])
        )
        
        # Grant EventBridge permission to invoke Lambdas
        lambda_functions['monitor'].add_permission(
            "AllowEventBridgeMonitor",
            principal=iam.ServicePrincipal("events.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=monitor_schedule.rule_arn
        )
        
        lambda_functions['bronze2silver'].add_permission(
            "AllowEventBridgeBronze2Silver", 
            principal=iam.ServicePrincipal("events.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=bronze_rule.rule_arn
        )
        
        return {
            'silver2gold_queue': silver2gold_queue,
            'bronze_rule': bronze_rule,
            'silver_rule': silver_rule,
            'monitor_schedule': monitor_schedule
        }