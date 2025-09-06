from aws_cdk import (
    Stack, CfnOutput, Duration,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_ssm as ssm
)
from constructs import Construct

class ObservabilityStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, api_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SNS Topic for alerts
        alert_topic = sns.Topic(
            self, "AlertTopic",
            topic_name="sync-hub-alerts"
        )

        # CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self, "Dashboard",
            dashboard_name="SyncHub-Monitoring"
        )

        # API Gateway metrics
        api_5xx_metric = cloudwatch.Metric(
            namespace="AWS/ApiGatewayV2",
            metric_name="5XXError",
            dimensions_map={"ApiId": api_stack.api.api_id},
            statistic="Sum",
            period=Duration.minutes(5)
        )

        api_latency_metric = cloudwatch.Metric(
            namespace="AWS/ApiGatewayV2", 
            metric_name="IntegrationLatency",
            dimensions_map={"ApiId": api_stack.api.api_id},
            statistic="Average",
            period=Duration.minutes(5)
        )

        # Lambda error metrics
        lambda_error_metric = cloudwatch.Metric(
            namespace="AWS/Lambda",
            metric_name="Errors",
            statistic="Sum",
            period=Duration.minutes(5)
        )

        # Dashboard widgets
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="API 5XX Errors",
                left=[api_5xx_metric],
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="API Latency",
                left=[api_latency_metric],
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="Lambda Errors",
                left=[lambda_error_metric],
                width=12,
                height=6
            )
        )

        # Alarms
        api_5xx_alarm = cloudwatch.Alarm(
            self, "Api5xxAlarm",
            metric=api_5xx_metric,
            threshold=10,
            evaluation_periods=2,
            alarm_description="API 5XX errors exceeded threshold"
        )
        api_5xx_alarm.add_alarm_action(cw_actions.SnsAction(alert_topic))

        api_latency_alarm = cloudwatch.Alarm(
            self, "ApiLatencyAlarm", 
            metric=api_latency_metric,
            threshold=5000,
            evaluation_periods=3,
            alarm_description="API latency exceeded 5 seconds"
        )
        api_latency_alarm.add_alarm_action(cw_actions.SnsAction(alert_topic))

        # Store dashboard URL in SSM
        ssm.StringParameter(
            self, "DashboardUrlParam",
            parameter_name="/sync-hub/observability/dashboard-url",
            string_value=f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}"
        )

        # Outputs
        CfnOutput(self, "DashboardUrl", value=f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}")
        CfnOutput(self, "AlertTopicArn", value=alert_topic.topic_arn)
