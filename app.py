#!/usr/bin/env python3
import aws_cdk as cdk
from cdk.stacks.auth_stack import AuthStack
from cdk.stacks.data_stack import DataStack
from cdk.stacks.api_stack import ApiStack
from cdk.stacks.web_stack import WebStack
from cdk.stacks.observability_stack import ObservabilityStack

app = cdk.App()

stage = app.node.try_get_context("stage") or "dev"
region = "us-east-1"

auth_stack = AuthStack(app, f"Auth-{stage}", env=cdk.Environment(region=region))
data_stack = DataStack(app, f"Data-{stage}", env=cdk.Environment(region=region))
api_stack = ApiStack(app, f"Api-{stage}", 
                    auth_stack=auth_stack,
                    data_stack=data_stack,
                    env=cdk.Environment(region=region))
web_stack = WebStack(app, f"Web-{stage}",
                    auth_stack=auth_stack,
                    api_stack=api_stack,
                    env=cdk.Environment(region=region))
obs_stack = ObservabilityStack(app, f"Observability-{stage}",
                              api_stack=api_stack,
                              web_stack=web_stack,
                              env=cdk.Environment(region=region))

app.synth()
