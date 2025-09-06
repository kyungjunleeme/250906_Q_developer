#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import (
    Stack, Duration, CfnOutput, RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigw,
    aws_iam as iam,
    aws_logs as logs,
    aws_ssm as ssm
)
from constructs import Construct

class SimpleApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table
        settings_table = dynamodb.Table(
            self, "SettingsTable",
            table_name="sync-hub-settings",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="setting_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Lambda function
        api_function = _lambda.Function(
            self, "ApiFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_inline("""
import json
import uuid
import time
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['SETTINGS_TABLE'])

def handler(event, context):
    try:
        method = event.get("requestContext", {}).get("http", {}).get("method")
        path = event.get("requestContext", {}).get("http", {}).get("path")
        
        if path == "/_health":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"ok": True, "message": "Sync Hub API is running!"})
            }
        
        if path == "/settings/public":
            response = table.scan(
                FilterExpression="is_public = :public",
                ExpressionAttributeValues={":public": True}
            )
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"settings": response.get("Items", [])})
            }
        
        if path == "/settings" and method == "POST":
            body = json.loads(event.get("body", "{}"))
            setting = {
                "tenant_id": "default",
                "setting_id": str(uuid.uuid4()),
                "name": body.get("name", "Sample Setting"),
                "value": body.get("value", "Sample Value"),
                "is_public": body.get("is_public", True),
                "created_at": int(time.time())
            }
            table.put_item(Item=setting)
            return {
                "statusCode": 201,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(setting)
            }
        
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Not found"})
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
"""),
            environment={
                "SETTINGS_TABLE": settings_table.table_name
            },
            timeout=Duration.seconds(30)
        )

        # Grant DynamoDB permissions
        settings_table.grant_read_write_data(api_function)

        # HTTP API
        api = apigw.HttpApi(
            self, "HttpApi",
            api_name="sync-hub-simple-api",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigw.CorsHttpMethod.ANY],
                allow_headers=["*"]
            )
        )

        # Integration
        integration = apigw.CfnIntegration(
            self, "LambdaIntegration",
            api_id=api.api_id,
            integration_type="AWS_PROXY",
            integration_uri=api_function.function_arn,
            payload_format_version="2.0"
        )

        # Grant API Gateway permission
        api_function.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{api.api_id}/*/*"
        )

        # Routes
        routes = [
            ("GET", "/_health"),
            ("GET", "/settings/public"),
            ("POST", "/settings")
        ]

        for method, path in routes:
            apigw.CfnRoute(
                self, f"Route{method}{path.replace('/', '').replace('{', '').replace('}', '')}",
                api_id=api.api_id,
                route_key=f"{method} {path}",
                target=f"integrations/{integration.ref}"
            )

        # Store outputs
        ssm.StringParameter(
            self, "ApiUrlParam",
            parameter_name="/sync-hub/api/url",
            string_value=api.api_endpoint
        )

        ssm.StringParameter(
            self, "SettingsTableParam",
            parameter_name="/sync-hub/data/settings-table",
            string_value=settings_table.table_name
        )

        # Outputs
        CfnOutput(self, "ApiUrl", value=api.api_endpoint)
        CfnOutput(self, "SettingsTableName", value=settings_table.table_name)

app = cdk.App()
SimpleApiStack(app, "SyncHubSimple", env=cdk.Environment(region="us-east-1"))
app.synth()
