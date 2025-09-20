from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct
from usdbrl_lambdas import USDBRLLambdas
from usdbrl_orchestration import USDBRLOrchestration
from s3_events import S3Events


class EconomicIndicatorsStack(Stack):
    """Main stack for Economic Indicators infrastructure"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Data Lake S3 Bucket
        self.data_lake_bucket = s3.Bucket(
            self, "DataLakeBucket",
            bucket_name="dl-economic-indicators-prod",
            versioned=False,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            intelligent_tiering_configurations=[
                s3.IntelligentTieringConfiguration(
                    name="EntireBucket",
                    archive_access_tier_time=Duration.days(90),
                    deep_archive_access_tier_time=Duration.days(180)
                )
            ],
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # DynamoDB Table for Lambda state
        self.dynamodb_table = dynamodb.Table(
            self, "SGSIndicatorsState",
            table_name="sgs-indicators-state",
            partition_key=dynamodb.Attribute(
                name="indicator", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # IAM Role for Lambda functions
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "S3DynamoDBPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject", 
                                "s3:DeleteObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                self.data_lake_bucket.bucket_arn,
                                f"{self.data_lake_bucket.bucket_arn}/*"
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:Query",
                                "dynamodb:Scan"
                            ],
                            resources=[self.dynamodb_table.table_arn]
                        )
                    ]
                )
            }
        )

        # Environment variables for Lambda functions
        lambda_env = {
            "BUCKET_NAME": self.data_lake_bucket.bucket_name,
            "DYNAMODB_TABLE": self.dynamodb_table.table_name,
            "REGION": self.region
        }

        # Create Lambda Functions using separate module
        lambda_functions = USDBRLLambdas.create_all_functions(
            stack=self,
            lambda_role=lambda_role, 
            env_vars=lambda_env
        )
        
        # Setup S3 Event Notifications to EventBridge for USD-BRL
        s3_events = S3Events.setup_usdbrl_events(self.data_lake_bucket)
        
        # Create Orchestration (EventBridge Rules, SQS, Scheduler)
        orchestration = USDBRLOrchestration.create_orchestration(
            stack=self,
            lambda_functions=lambda_functions,
            data_lake_bucket=self.data_lake_bucket
        )
        
        # Store references for potential cross-stack usage
        self.monitor_function = lambda_functions['monitor']
        self.bronze2silver_function = lambda_functions['bronze2silver'] 
        self.silver2gold_function = lambda_functions['silver2gold']
        
        # Store orchestration references
        self.silver2gold_queue = orchestration['silver2gold_queue']
        self.bronze_rule = orchestration['bronze_rule']
        self.silver_rule = orchestration['silver_rule'] 
        self.monitor_schedule = orchestration['monitor_schedule']