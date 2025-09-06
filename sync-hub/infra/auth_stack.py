from aws_cdk import (
    Stack, Duration, CfnOutput, RemovalPolicy,
    aws_cognito as cognito,
    aws_ssm as ssm
)
from constructs import Construct

class AuthStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognito User Pool
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name="sync-hub-users",
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY
        )

        # User Pool Client for Web
        self.user_pool_client = cognito.UserPoolClient(
            self, "UserPoolClient",
            user_pool=self.user_pool,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                callback_urls=["https://localhost:3000/callback", "http://localhost:3000/callback"]
            ),
            generate_secret=False
        )

        # User Pool Domain
        self.user_pool_domain = cognito.UserPoolDomain(
            self, "UserPoolDomain",
            user_pool=self.user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"sync-hub-{self.account}-{self.region}"
            )
        )

        # Google Identity Provider
        google_provider = cognito.UserPoolIdentityProviderGoogle(
            self, "GoogleProvider",
            user_pool=self.user_pool,
            client_id="your-google-client-id",  # Replace with actual
            client_secret="your-google-client-secret",  # Replace with actual
            scopes=["email", "profile", "openid"],
            attribute_mapping=cognito.AttributeMapping(
                email=cognito.ProviderAttribute.GOOGLE_EMAIL,
                given_name=cognito.ProviderAttribute.GOOGLE_GIVEN_NAME,
                family_name=cognito.ProviderAttribute.GOOGLE_FAMILY_NAME
            )
        )

        self.user_pool_client.node.add_dependency(google_provider)

        # Store outputs in SSM
        ssm.StringParameter(
            self, "UserPoolIdParam",
            parameter_name="/sync-hub/auth/user-pool-id",
            string_value=self.user_pool.user_pool_id
        )

        ssm.StringParameter(
            self, "UserPoolClientIdParam", 
            parameter_name="/sync-hub/auth/user-pool-client-id",
            string_value=self.user_pool_client.user_pool_client_id
        )

        ssm.StringParameter(
            self, "HostedUiUrlParam",
            parameter_name="/sync-hub/auth/hosted-ui-url",
            string_value=f"https://{self.user_pool_domain.domain_name}.auth.{self.region}.amazoncognito.com"
        )

        # Outputs
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)
        CfnOutput(self, "HostedUiUrl", value=f"https://{self.user_pool_domain.domain_name}.auth.{self.region}.amazoncognito.com")
