from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    aws_ssm as ssm,
    CfnOutput
)
from constructs import Construct

class AuthStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        stage = self.node.try_get_context("stage") or "dev"
        
        # User Pool
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name=f"saas-users-{stage}",
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True)
            ),
            custom_attributes={
                "tenant_id": cognito.StringAttribute(min_len=1, max_len=256, mutable=True)
            }
        )
        
        # User Pool Domain
        self.user_pool_domain = cognito.UserPoolDomain(
            self, "UserPoolDomain",
            user_pool=self.user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"saas-auth-{stage}"
            )
        )
        
        # App Client
        self.user_pool_client = cognito.UserPoolClient(
            self, "UserPoolClient",
            user_pool=self.user_pool,
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                callback_urls=["http://localhost:8000/callback", "https://example.com/callback"]
            )
        )
        
        # Groups
        cognito.CfnUserPoolGroup(
            self, "AdminGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="admin",
            description="Admin users"
        )
        
        cognito.CfnUserPoolGroup(
            self, "MemberGroup", 
            user_pool_id=self.user_pool.user_pool_id,
            group_name="member",
            description="Member users"
        )
        
        # SSM Parameters
        ssm.StringParameter(
            self, "UserPoolIdParam",
            parameter_name=f"/saas/{stage}/auth/user-pool-id",
            string_value=self.user_pool.user_pool_id
        )
        
        ssm.StringParameter(
            self, "UserPoolClientIdParam",
            parameter_name=f"/saas/{stage}/auth/user-pool-client-id",
            string_value=self.user_pool_client.user_pool_client_id
        )
        
        ssm.StringParameter(
            self, "UserPoolDomainParam",
            parameter_name=f"/saas/{stage}/auth/user-pool-domain",
            string_value=self.user_pool_domain.domain_name
        )
        
        # Outputs
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)
        CfnOutput(self, "UserPoolDomain", value=self.user_pool_domain.domain_name)
