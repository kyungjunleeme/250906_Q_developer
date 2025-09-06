from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_ssm as ssm,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct

class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        stage = self.node.try_get_context("stage") or "dev"
        
        # Tenants Table
        self.tenants_table = dynamodb.Table(
            self, "TenantsTable",
            table_name=f"saas-tenants-{stage}",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if stage == "dev" else RemovalPolicy.RETAIN
        )
        
        # Users Table
        self.users_table = dynamodb.Table(
            self, "UsersTable",
            table_name=f"saas-users-{stage}",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if stage == "dev" else RemovalPolicy.RETAIN
        )
        
        # Add GSI for tenant_id
        self.users_table.add_global_secondary_index(
            index_name="tenant-index",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING)
        )
        
        # Items Table
        self.items_table = dynamodb.Table(
            self, "ItemsTable",
            table_name=f"saas-items-{stage}",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="item_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if stage == "dev" else RemovalPolicy.RETAIN
        )
        
        # SSM Parameters
        ssm.StringParameter(
            self, "TenantsTableParam",
            parameter_name=f"/saas/{stage}/data/tenants-table",
            string_value=self.tenants_table.table_name
        )
        
        ssm.StringParameter(
            self, "UsersTableParam",
            parameter_name=f"/saas/{stage}/data/users-table",
            string_value=self.users_table.table_name
        )
        
        ssm.StringParameter(
            self, "ItemsTableParam",
            parameter_name=f"/saas/{stage}/data/items-table",
            string_value=self.items_table.table_name
        )
        
        # Outputs
        CfnOutput(self, "TenantsTableName", value=self.tenants_table.table_name)
        CfnOutput(self, "UsersTableName", value=self.users_table.table_name)
        CfnOutput(self, "ItemsTableName", value=self.items_table.table_name)
