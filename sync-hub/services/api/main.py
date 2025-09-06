import json
import os
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from handlers.auth import AuthHandler
from handlers.settings import SettingsHandler
from handlers.bookmarks import BookmarksHandler
from handlers.groups import GroupsHandler
from handlers.sessions import SessionsHandler

logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize handlers
auth_handler = AuthHandler()
settings_handler = SettingsHandler()
bookmarks_handler = BookmarksHandler()
groups_handler = GroupsHandler()
sessions_handler = SessionsHandler()

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics
def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        method = event.get("requestContext", {}).get("http", {}).get("method")
        path = event.get("requestContext", {}).get("http", {}).get("path")
        
        logger.info(f"Processing {method} {path}")
        metrics.add_metric(name="RequestCount", unit=MetricUnit.Count, value=1)
        
        # Health check
        if path == "/_health":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"ok": True})
            }
        
        # Extract tenant_id from JWT claims
        tenant_id = "default"  # Default tenant for demo
        if "authorizer" in event.get("requestContext", {}):
            claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
            tenant_id = claims.get("sub", "default")
        
        # Route to appropriate handler
        if path.startswith("/auth/"):
            return auth_handler.handle(event, tenant_id)
        elif path.startswith("/settings"):
            return settings_handler.handle(event, tenant_id)
        elif path.startswith("/bookmarks"):
            return bookmarks_handler.handle(event, tenant_id)
        elif path.startswith("/groups"):
            return groups_handler.handle(event, tenant_id)
        elif path.startswith("/sessions"):
            return sessions_handler.handle(event, tenant_id)
        else:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Not found"})
            }
            
    except Exception as e:
        logger.exception("Unhandled error")
        metrics.add_metric(name="ErrorCount", unit=MetricUnit.Count, value=1)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }
