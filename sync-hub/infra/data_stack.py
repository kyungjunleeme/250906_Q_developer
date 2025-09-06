from aws_cdk import (
    Stack, RemovalPolicy, CfnOutput,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_ssm as ssm
)
from constructs import Construct

class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Tables
        self.settings_table = dynamodb.Table(
            self, "SettingsTable",
            table_name="sync-hub-settings",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="setting_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.bookmarks_table = dynamodb.Table(
            self, "BookmarksTable", 
            table_name="sync-hub-bookmarks",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="bookmark_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.groups_table = dynamodb.Table(
            self, "GroupsTable",
            table_name="sync-hub-groups", 
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="group_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.group_members_table = dynamodb.Table(
            self, "GroupMembersTable",
            table_name="sync-hub-group-members",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="group_id#user_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.sessions_table = dynamodb.Table(
            self, "SessionsTable",
            table_name="sync-hub-sessions",
            partition_key=dynamodb.Attribute(name="tenant_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="session_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        # S3 Bucket for backups
        self.backup_bucket = s3.Bucket(
            self, "BackupBucket",
            bucket_name=f"sync-hub-backups-{self.account}-{self.region}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Store table names in SSM
        for table_name, table in [
            ("settings", self.settings_table),
            ("bookmarks", self.bookmarks_table), 
            ("groups", self.groups_table),
            ("group-members", self.group_members_table),
            ("sessions", self.sessions_table)
        ]:
            ssm.StringParameter(
                self, f"{table_name.title().replace('-', '')}TableParam",
                parameter_name=f"/sync-hub/data/{table_name}-table",
                string_value=table.table_name
            )

        ssm.StringParameter(
            self, "BackupBucketParam",
            parameter_name="/sync-hub/data/backup-bucket",
            string_value=self.backup_bucket.bucket_name
        )

        # Outputs
        CfnOutput(self, "SettingsTableName", value=self.settings_table.table_name)
        CfnOutput(self, "BackupBucketName", value=self.backup_bucket.bucket_name)
