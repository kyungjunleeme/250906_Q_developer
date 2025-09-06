from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_ssm as ssm,
    CfnOutput,
    Duration
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, auth_stack, data_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        stage = self.node.try_get_context("stage") or "dev"
        
        # Lambda Function
        self.api_lambda = _lambda.Function(
            self, "ApiLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="main.handler",
            code=_lambda.Code.from_asset("services/api"),
            timeout=Duration.seconds(30),
            environment={
                "TENANTS_TABLE": data_stack.tenants_table.table_name,
                "USERS_TABLE": data_stack.users_table.table_name,
                "ITEMS_TABLE": data_stack.items_table.table_name,
                "USER_POOL_ID": auth_stack.user_pool.user_pool_id,
                "USER_POOL_CLIENT_ID": auth_stack.user_pool_client.user_pool_client_id
            }
        )
        
        # Grant DynamoDB permissions
        data_stack.tenants_table.grant_read_write_data(self.api_lambda)
        data_stack.users_table.grant_read_write_data(self.api_lambda)
        data_stack.items_table.grant_read_write_data(self.api_lambda)
        
        # API Gateway
        self.api = apigateway.LambdaRestApi(
            self, "Api",
            handler=self.api_lambda,
            rest_api_name=f"saas-api-{stage}",
            proxy=True,
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )
        
        # SSM Parameters
        ssm.StringParameter(
            self, "ApiUrlParam",
            parameter_name=f"/saas/{stage}/api/url",
            string_value=self.api.url
        )
        
        ssm.StringParameter(
            self, "ApiLambdaArnParam",
            parameter_name=f"/saas/{stage}/api/lambda-arn",
            string_value=self.api_lambda.function_arn
        )
        
        # Outputs
        CfnOutput(self, "ApiUrl", value=self.api.url)
        CfnOutput(self, "ApiLambdaArn", value=self.api_lambda.function_arn)
