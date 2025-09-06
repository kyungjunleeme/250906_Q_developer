import json
import os
import uuid
import time
from typing import Dict, Any
from aws_lambda_powertools import Logger
import boto3

logger = Logger()

class AuthHandler:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.sessions_table = self.dynamodb.Table(os.environ['SESSIONS_TABLE'])
    
    def handle(self, event: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        method = event.get("requestContext", {}).get("http", {}).get("method")
        path = event.get("requestContext", {}).get("http", {}).get("path")
        
        if path == "/auth/device/start" and method == "POST":
            return self._start_device_flow(tenant_id)
        elif path == "/auth/device/confirm" and method == "POST":
            return self._confirm_device_flow(event, tenant_id)
        
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Not found"})
        }
    
    def _start_device_flow(self, tenant_id: str) -> Dict[str, Any]:
        device_code = str(uuid.uuid4())[:8].upper()
        session_id = str(uuid.uuid4())
        
        # Store device session
        self.sessions_table.put_item(
            Item={
                "tenant_id": tenant_id,
                "session_id": session_id,
                "device_code": device_code,
                "status": "pending",
                "created_at": int(time.time()),
                "ttl": int(time.time()) + 600  # 10 minutes
            }
        )
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "device_code": device_code,
                "session_id": session_id,
                "expires_in": 600
            })
        }
    
    def _confirm_device_flow(self, event: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        try:
            body = json.loads(event.get("body", "{}"))
            device_code = body.get("device_code")
            
            if not device_code:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "device_code required"})
                }
            
            # Find session by device code
            response = self.sessions_table.scan(
                FilterExpression="device_code = :code AND #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":code": device_code, ":status": "pending"}
            )
            
            if not response["Items"]:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Invalid device code"})
                }
            
            session = response["Items"][0]
            
            # Update session status
            self.sessions_table.update_item(
                Key={"tenant_id": session["tenant_id"], "session_id": session["session_id"]},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": "confirmed"}
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"status": "confirmed"})
            }
            
        except Exception as e:
            logger.exception("Error confirming device flow")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
