"""
USD-BRL Lambda Functions Module
Simple module to organize Lambda functions separately from main stack
"""
import os
from aws_cdk import (
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class USDBRLLambdas:
    """Creates Lambda functions for USD-BRL data processing pipeline"""

    @staticmethod
    def create_all_functions(stack: Construct, lambda_role: iam.Role, env_vars: dict):
        """Create all USD-BRL Lambda functions and return them"""
        
        # Get project root path (parent of infra-aws-cdk/)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Monitor Function
        monitor_function = lambda_.Function(
            stack, "USDBRLMonitor",
            function_name="usdbrl-monitor",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(project_root, "lambdas/usdbrl/monitor")),
            role=lambda_role,
            timeout=Duration.seconds(60),
            memory_size=256,
            environment=env_vars,
            description="USD-BRL Monitor - Coleta dados SGS API",
            log_retention=logs.RetentionDays.TWO_WEEKS
        )

        # Bronze to Silver Function
        bronze2silver_function = lambda_.Function(
            stack, "USDBRLBronze2Silver", 
            function_name="usdbrl-bronze2silver",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(project_root, "lambdas/usdbrl/bronze2silver")),
            role=lambda_role,
            timeout=Duration.seconds(60),
            memory_size=512,
            environment=env_vars,
            description="USD-BRL Bronze to Silver - Data Quality",
            log_retention=logs.RetentionDays.TWO_WEEKS
        )

        # Silver to Gold Function  
        silver2gold_function = lambda_.Function(
            stack, "USDBRLSilver2Gold",
            function_name="usdbrl-silver2gold", 
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(project_root, "lambdas/usdbrl/silver2gold")),
            role=lambda_role,
            timeout=Duration.seconds(120),
            memory_size=512,
            environment=env_vars,
            description="USD-BRL Silver to Gold - Financial Indicators",
            log_retention=logs.RetentionDays.TWO_WEEKS
        )
        
        return {
            'monitor': monitor_function,
            'bronze2silver': bronze2silver_function,
            'silver2gold': silver2gold_function
        }