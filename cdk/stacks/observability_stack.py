from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    CfnOutput
)
from constructs import Construct

class ObservabilityStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, api_stack, web_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        stage = self.node.try_get_context("stage") or "dev"
        
        # SNS Topic for alerts
        alert_topic = sns.Topic(self, "AlertTopic", topic_name=f"saas-alerts-{stage}")
        
        # Dashboard
        dashboard = cloudwatch.Dashboard(
            self, "Dashboard",
            dashboard_name=f"SaaS-{stage}"
        )
        
        # API Lambda Metrics
        api_error_metric = cloudwatch.Metric(
            namespace="AWS/Lambda",
            metric_name="Errors",
            dimensions_map={"FunctionName": api_stack.api_lambda.function_name},
            statistic="Sum"
        )
        
        api_duration_metric = cloudwatch.Metric(
            namespace="AWS/Lambda",
            metric_name="Duration",
            dimensions_map={"FunctionName": api_stack.api_lambda.function_name},
            statistic="Average"
        )
        
        # API Gateway Metrics
        api_5xx_metric = cloudwatch.Metric(
            namespace="AWS/ApiGateway",
            metric_name="5XXError",
            dimensions_map={"ApiName": api_stack.api.rest_api_name},
            statistic="Sum"
        )
        
        api_latency_metric = cloudwatch.Metric(
            namespace="AWS/ApiGateway",
            metric_name="Latency",
            dimensions_map={"ApiName": api_stack.api.rest_api_name},
            statistic="Average"
        )
        
        # Add widgets to dashboard
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="API Errors",
                left=[api_error_metric, api_5xx_metric]
            ),
            cloudwatch.GraphWidget(
                title="API Latency",
                left=[api_duration_metric, api_latency_metric]
            )
        )
        
        # Alarms
        cloudwatch.Alarm(
            self, "ApiErrorAlarm",
            alarm_name=f"SaaS-API-Errors-{stage}",
            metric=api_error_metric,
            threshold=5,
            evaluation_periods=2,
            alarm_description="API Lambda errors"
        ).add_alarm_action(cw_actions.SnsAction(alert_topic))
        
        cloudwatch.Alarm(
            self, "Api5xxAlarm",
            alarm_name=f"SaaS-API-5xx-{stage}",
            metric=api_5xx_metric,
            threshold=10,
            evaluation_periods=2,
            alarm_description="API Gateway 5xx errors"
        ).add_alarm_action(cw_actions.SnsAction(alert_topic))
        
        cloudwatch.Alarm(
            self, "ApiLatencyAlarm",
            alarm_name=f"SaaS-API-Latency-{stage}",
            metric=api_latency_metric,
            threshold=5000,
            evaluation_periods=3,
            alarm_description="API high latency"
        ).add_alarm_action(cw_actions.SnsAction(alert_topic))
        
        # Outputs
        CfnOutput(self, "DashboardUrl", 
                 value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}")
        CfnOutput(self, "AlertTopicArn", value=alert_topic.topic_arn)
