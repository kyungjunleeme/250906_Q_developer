from aws_cdk import (
    Stack, Duration, CfnOutput,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigw,
    aws_iam as iam,
    aws_logs as logs,
    aws_ssm as ssm
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, auth_stack, data_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda Layer for Powertools
        powertools_layer = _lambda.LayerVersion(
            self, "PowertoolsLayer",
            code=_lambda.Code.from_asset("layers/powertools"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="AWS Lambda Powertools"
        )

        # Common Lambda environment
        common_env = {
            "POWERTOOLS_SERVICE_NAME": "sync-hub",
            "POWERTOOLS_METRICS_NAMESPACE": "SyncHub",
            "LOG_LEVEL": "INFO",
            "USER_POOL_ID": auth_stack.user_pool.user_pool_id,
            "SETTINGS_TABLE": data_stack.settings_table.table_name,
            "BOOKMARKS_TABLE": data_stack.bookmarks_table.table_name,
            "GROUPS_TABLE": data_stack.groups_table.table_name,
            "GROUP_MEMBERS_TABLE": data_stack.group_members_table.table_name,
            "SESSIONS_TABLE": data_stack.sessions_table.table_name,
            "BACKUP_BUCKET": data_stack.backup_bucket.bucket_name
        }

        # Lambda execution role
        lambda_role = iam.Role(
            self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
            ]
        )

        # Grant DynamoDB permissions
        for table in [data_stack.settings_table, data_stack.bookmarks_table, 
                     data_stack.groups_table, data_stack.group_members_table, data_stack.sessions_table]:
            table.grant_read_write_data(lambda_role)

        # Grant S3 permissions
        data_stack.backup_bucket.grant_read_write(lambda_role)

        # API Lambda function
        api_function = _lambda.Function(
            self, "ApiFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.handler",
            code=_lambda.Code.from_asset("services/api"),
            environment=common_env,
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            layers=[powertools_layer],
            tracing=_lambda.Tracing.ACTIVE,
            log_retention=logs.RetentionDays.ONE_MONTH
        )

        # HTTP API
        self.api = apigw.HttpApi(
            self, "HttpApi",
            api_name="sync-hub-api",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigw.CorsHttpMethod.ANY],
                allow_headers=["*"]
            )
        )

        # JWT Authorizer
        jwt_authorizer = apigw.CfnAuthorizer(
            self, "JwtAuthorizer",
            api_id=self.api.api_id,
            authorizer_type="JWT",
            identity_source=["$request.header.Authorization"],
            name="JwtAuthorizer",
            jwt_configuration=apigw.CfnAuthorizer.JWTConfigurationProperty(
                audience=[auth_stack.user_pool_client.user_pool_client_id],
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{auth_stack.user_pool.user_pool_id}"
            )
        )

        # API Integration
        lambda_integration = apigw.CfnIntegration(
            self, "LambdaIntegration",
            api_id=self.api.api_id,
            integration_type="AWS_PROXY",
            integration_uri=api_function.function_arn,
            payload_format_version="2.0"
        )

        # Grant API Gateway permission to invoke Lambda
        api_function.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{self.api.api_id}/*/*"
        )

        # Routes
        routes = [
            # Health check (public)
            ("GET", "/_health", None),
            # Auth
            ("POST", "/auth/device/start", jwt_authorizer.ref),
            ("POST", "/auth/device/confirm", jwt_authorizer.ref),
            # Settings
            ("GET", "/settings", jwt_authorizer.ref),
            ("POST", "/settings", jwt_authorizer.ref),
            ("GET", "/settings/{id}", jwt_authorizer.ref),
            ("PUT", "/settings/{id}", jwt_authorizer.ref),
            ("DELETE", "/settings/{id}", jwt_authorizer.ref),
            ("GET", "/settings/{id}/history", jwt_authorizer.ref),
            ("POST", "/settings/{id}/rollback", jwt_authorizer.ref),
            ("GET", "/settings/public", None),
            ("PUT", "/settings/{id}/visibility", jwt_authorizer.ref),
            # Bookmarks
            ("GET", "/bookmarks", jwt_authorizer.ref),
            ("POST", "/bookmarks", jwt_authorizer.ref),
            ("GET", "/bookmarks/{id}", jwt_authorizer.ref),
            ("PUT", "/bookmarks/{id}", jwt_authorizer.ref),
            ("DELETE", "/bookmarks/{id}", jwt_authorizer.ref),
            # Groups
            ("GET", "/groups", jwt_authorizer.ref),
            ("POST", "/groups", jwt_authorizer.ref),
            ("GET", "/groups/{id}", jwt_authorizer.ref),
            ("PUT", "/groups/{id}", jwt_authorizer.ref),
            ("DELETE", "/groups/{id}", jwt_authorizer.ref),
            ("POST", "/groups/{id}/invite", jwt_authorizer.ref),
            ("GET", "/groups/{id}/members", jwt_authorizer.ref),
            # Sessions
            ("POST", "/sessions/{id}/emoji", jwt_authorizer.ref)
        ]

        for method, path, authorizer in routes:
            apigw.CfnRoute(
                self, f"Route{method}{path.replace('/', '').replace('{', '').replace('}', '')}",
                api_id=self.api.api_id,
                route_key=f"{method} {path}",
                target=f"integrations/{lambda_integration.ref}",
                authorization_type="JWT" if authorizer else "NONE",
                authorizer_id=authorizer if authorizer else None
            )

        # Store API URL in SSM
        ssm.StringParameter(
            self, "ApiUrlParam",
            parameter_name="/sync-hub/api/url",
            string_value=self.api.api_endpoint
        )

        # Outputs
        CfnOutput(self, "ApiUrl", value=self.api.api_endpoint)
