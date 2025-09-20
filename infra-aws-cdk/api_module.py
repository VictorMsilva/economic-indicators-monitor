import os
from aws_cdk import (
    Duration,
    BundlingOptions,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class EconomicIndicatorsAPI:

    @staticmethod
    def create_api(stack: Construct, lambda_role: iam.Role, data_lake_bucket, env_vars: dict):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        api_lambda = lambda_.Function(
            stack, "EconomicIndicatorsAPI",
            function_name="economic-indicators-api",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambdas/api"),
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment=env_vars,
            description="Economic Indicators API",
            log_retention=logs.RetentionDays.TWO_WEEKS
        )
        
        data_lake_bucket.grant_read(api_lambda)
        
        api_gateway = apigw.RestApi(
            stack, "EconomicIndicatorsRestAPI",
            rest_api_name="economic-indicators-api",
            description="API for querying economic indicators",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=['Content-Type', 'Authorization']
            ),
            endpoint_configuration=apigw.EndpointConfiguration(
                types=[apigw.EndpointType.REGIONAL]
            )
        )
        
        api_integration = apigw.LambdaIntegration(api_lambda, proxy=True)
        
        api_gateway.root.add_method("GET", api_integration)
        
        indicators_resource = api_gateway.root.add_resource("indicators")
        indicators_resource.add_method("GET", api_integration)
        
        indicator_resource = indicators_resource.add_resource("{indicator}")
        indicator_resource.add_method("GET", api_integration)
        
        return {
            'api_lambda': api_lambda,
            'api_gateway': api_gateway,
            'api_url': api_gateway.url
        }