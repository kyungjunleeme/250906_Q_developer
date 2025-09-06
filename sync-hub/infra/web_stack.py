from aws_cdk import (
    Stack, CfnOutput, RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_ssm as ssm
)
from constructs import Construct

class WebStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, auth_stack, api_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for web hosting
        self.web_bucket = s3.Bucket(
            self, "WebBucket",
            bucket_name=f"sync-hub-web-{self.account}-{self.region}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Origin Access Identity
        oai = cloudfront.OriginAccessIdentity(
            self, "OAI",
            comment="Sync Hub Web OAI"
        )

        self.web_bucket.grant_read(oai)

        # CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self, "WebDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.web_bucket, origin_access_identity=oai),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html"
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html"
                )
            ]
        )

        # Deploy web assets
        s3deploy.BucketDeployment(
            self, "WebDeployment",
            sources=[s3deploy.Source.asset("web/dist")],
            destination_bucket=self.web_bucket,
            distribution=self.distribution,
            distribution_paths=["/*"]
        )

        # Store web URL in SSM
        ssm.StringParameter(
            self, "WebUrlParam",
            parameter_name="/sync-hub/web/url",
            string_value=f"https://{self.distribution.distribution_domain_name}"
        )

        # Outputs
        CfnOutput(self, "WebUrl", value=f"https://{self.distribution.distribution_domain_name}")
        CfnOutput(self, "WebBucketName", value=self.web_bucket.bucket_name)
