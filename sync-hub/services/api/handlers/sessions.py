import json
import os
import time
from typing import Dict, Any
from aws_lambda_powertools import Logger
import boto3

logger = Logger()

class SessionsHandler:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.sessions_table = self.dynamodb.Table(os.environ['SESSIONS_TABLE'])
    
    def handle(self, event: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        method = event.get("requestContext", {}).get("http", {}).get("method")
        path = event.get("requestContext", {}).get("http", {}).get("path")
        
        if path.startswith("/sessions/") and path.endswith("/emoji") and method == "POST":
            session_id = path.split("/")[-2]
            return self._add_emoji_feedback(event, session_id, tenant_id)
        
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Not found"})
        }
    
    def _add_emoji_feedback(self, event: Dict[str, Any], session_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            body = json.loads(event.get("body", "{}"))
            emoji = body.get("emoji")
            
            if not emoji:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "emoji required"})
                }
            
            # Update session with emoji feedback
            self.sessions_table.update_item(
                Key={"tenant_id": tenant_id, "session_id": session_id},
                UpdateExpression="SET emoji_feedback = :emoji, feedback_at = :feedback_at",
                ExpressionAttributeValues={
                    ":emoji": emoji,
                    ":feedback_at": int(time.time())
                }
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"emoji": emoji, "session_id": session_id})
            }
        except Exception as e:
            logger.exception("Error adding emoji feedback")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
