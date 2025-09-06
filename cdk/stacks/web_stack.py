from aws_cdk import (
    Stack,
    aws_apprunner as apprunner,
    aws_iam as iam,
    aws_ssm as ssm,
    CfnOutput
)
from constructs import Construct

class WebStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, auth_stack, api_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        stage = self.node.try_get_context("stage") or "dev"
        
        # IAM Role for App Runner
        app_runner_role = iam.Role(
            self, "AppRunnerRole",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess")
            ]
        )
        
        # User Web App
        self.user_app = apprunner.CfnService(
            self, "UserApp",
            service_name=f"saas-user-{stage}",
            source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                auto_deployments_enabled=False,
                code_repository=apprunner.CfnService.CodeRepositoryProperty(
                    repository_url="https://github.com/placeholder/repo",
                    source_code_version=apprunner.CfnService.SourceCodeVersionProperty(
                        type="BRANCH",
                        value="main"
                    ),
                    code_configuration=apprunner.CfnService.CodeConfigurationProperty(
                        configuration_source="REPOSITORY"
                    )
                )
            ),
            instance_configuration=apprunner.CfnService.InstanceConfigurationProperty(
                cpu="0.25 vCPU",
                memory="0.5 GB",
                instance_role_arn=app_runner_role.role_arn
            )
        )
        
        # Admin Web App
        self.admin_app = apprunner.CfnService(
            self, "AdminApp",
            service_name=f"saas-admin-{stage}",
            source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                auto_deployments_enabled=False,
                code_repository=apprunner.CfnService.CodeRepositoryProperty(
                    repository_url="https://github.com/placeholder/repo",
                    source_code_version=apprunner.CfnService.SourceCodeVersionProperty(
                        type="BRANCH",
                        value="main"
                    ),
                    code_configuration=apprunner.CfnService.CodeConfigurationProperty(
                        configuration_source="REPOSITORY"
                    )
                )
            ),
            instance_configuration=apprunner.CfnService.InstanceConfigurationProperty(
                cpu="0.25 vCPU",
                memory="0.5 GB",
                instance_role_arn=app_runner_role.role_arn
            )
        )
        
        # SSM Parameters
        ssm.StringParameter(
            self, "UserAppUrlParam",
            parameter_name=f"/saas/{stage}/web/user-url",
            string_value=f"https://{self.user_app.attr_service_url}"
        )
        
        ssm.StringParameter(
            self, "AdminAppUrlParam",
            parameter_name=f"/saas/{stage}/web/admin-url",
            string_value=f"https://{self.admin_app.attr_service_url}"
        )
        
        # Outputs
        CfnOutput(self, "UserAppUrl", value=f"https://{self.user_app.attr_service_url}")
        CfnOutput(self, "AdminAppUrl", value=f"https://{self.admin_app.attr_service_url}")
