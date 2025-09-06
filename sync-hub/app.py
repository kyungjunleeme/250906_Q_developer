#!/usr/bin/env python3
import aws_cdk as cdk
from infra.auth_stack import AuthStack
from infra.data_stack import DataStack
from infra.api_stack import ApiStack
from infra.web_stack import WebStack
from infra.observability_stack import ObservabilityStack

app = cdk.App()
env = cdk.Environment(region="us-east-1")

# Deploy stacks in dependency order
auth_stack = AuthStack(app, "SyncHubAuth", env=env)
data_stack = DataStack(app, "SyncHubData", env=env)
api_stack = ApiStack(app, "SyncHubApi", auth_stack=auth_stack, data_stack=data_stack, env=env)
web_stack = WebStack(app, "SyncHubWeb", auth_stack=auth_stack, api_stack=api_stack, env=env)
observability_stack = ObservabilityStack(app, "SyncHubObservability", api_stack=api_stack, env=env)

app.synth()
