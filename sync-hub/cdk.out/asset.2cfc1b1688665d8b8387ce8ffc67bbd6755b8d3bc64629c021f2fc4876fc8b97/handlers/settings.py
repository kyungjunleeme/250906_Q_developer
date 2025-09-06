import json
import os
import uuid
import time
from typing import Dict, Any
from aws_lambda_powertools import Logger
import boto3
from boto3.dynamodb.conditions import Key

logger = Logger()

class SettingsHandler:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.settings_table = self.dynamodb.Table(os.environ['SETTINGS_TABLE'])
    
    def handle(self, event: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        method = event.get("requestContext", {}).get("http", {}).get("method")
        path = event.get("requestContext", {}).get("http", {}).get("path")
        
        if path == "/settings" and method == "GET":
            return self._list_settings(tenant_id)
        elif path == "/settings" and method == "POST":
            return self._create_setting(event, tenant_id)
        elif path.startswith("/settings/") and method == "GET":
            setting_id = path.split("/")[-1]
            if path.endswith("/history"):
                return self._get_setting_history(setting_id, tenant_id)
            else:
                return self._get_setting(setting_id, tenant_id)
        elif path.startswith("/settings/") and method == "PUT":
            setting_id = path.split("/")[-1]
            if path.endswith("/visibility"):
                return self._update_visibility(event, setting_id, tenant_id)
            else:
                return self._update_setting(event, setting_id, tenant_id)
        elif path.startswith("/settings/") and method == "DELETE":
            setting_id = path.split("/")[-1]
            return self._delete_setting(setting_id, tenant_id)
        elif path.startswith("/settings/") and path.endswith("/rollback") and method == "POST":
            setting_id = path.split("/")[-2]
            return self._rollback_setting(event, setting_id, tenant_id)
        elif path == "/settings/public" and method == "GET":
            return self._list_public_settings()
        
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Not found"})
        }
    
    def _list_settings(self, tenant_id: str) -> Dict[str, Any]:
        try:
            response = self.settings_table.query(
                KeyConditionExpression=Key('tenant_id').eq(tenant_id)
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"settings": response["Items"]})
            }
        except Exception as e:
            logger.exception("Error listing settings")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _create_setting(self, event: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        try:
            body = json.loads(event.get("body", "{}"))
            setting_id = str(uuid.uuid4())
            
            setting = {
                "tenant_id": tenant_id,
                "setting_id": setting_id,
                "name": body.get("name"),
                "value": body.get("value"),
                "is_public": body.get("is_public", False),
                "version": 1,
                "created_at": int(time.time()),
                "updated_at": int(time.time())
            }
            
            self.settings_table.put_item(Item=setting)
            
            return {
                "statusCode": 201,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(setting)
            }
        except Exception as e:
            logger.exception("Error creating setting")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _get_setting(self, setting_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            response = self.settings_table.get_item(
                Key={"tenant_id": tenant_id, "setting_id": setting_id}
            )
            
            if "Item" not in response:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Setting not found"})
                }
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response["Item"])
            }
        except Exception as e:
            logger.exception("Error getting setting")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _update_setting(self, event: Dict[str, Any], setting_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            body = json.loads(event.get("body", "{}"))
            
            # Get current setting to increment version
            current = self.settings_table.get_item(
                Key={"tenant_id": tenant_id, "setting_id": setting_id}
            )
            
            if "Item" not in current:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Setting not found"})
                }
            
            # Create history entry
            history_id = f"{setting_id}#v{current['Item']['version']}"
            history_item = current["Item"].copy()
            history_item["setting_id"] = history_id
            self.settings_table.put_item(Item=history_item)
            
            # Update current setting
            updated_setting = current["Item"].copy()
            updated_setting.update({
                "name": body.get("name", updated_setting["name"]),
                "value": body.get("value", updated_setting["value"]),
                "version": updated_setting["version"] + 1,
                "updated_at": int(time.time())
            })
            
            self.settings_table.put_item(Item=updated_setting)
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(updated_setting)
            }
        except Exception as e:
            logger.exception("Error updating setting")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _delete_setting(self, setting_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            self.settings_table.delete_item(
                Key={"tenant_id": tenant_id, "setting_id": setting_id}
            )
            
            return {
                "statusCode": 204,
                "headers": {"Content-Type": "application/json"},
                "body": ""
            }
        except Exception as e:
            logger.exception("Error deleting setting")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _get_setting_history(self, setting_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            response = self.settings_table.query(
                KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('setting_id').begins_with(f"{setting_id}#v")
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"history": response["Items"]})
            }
        except Exception as e:
            logger.exception("Error getting setting history")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _rollback_setting(self, event: Dict[str, Any], setting_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            body = json.loads(event.get("body", "{}"))
            version = body.get("version")
            
            if not version:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "version required"})
                }
            
            # Get historical version
            history_response = self.settings_table.get_item(
                Key={"tenant_id": tenant_id, "setting_id": f"{setting_id}#v{version}"}
            )
            
            if "Item" not in history_response:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Version not found"})
                }
            
            # Restore as new version
            historical_item = history_response["Item"]
            restored_setting = {
                "tenant_id": tenant_id,
                "setting_id": setting_id,
                "name": historical_item["name"],
                "value": historical_item["value"],
                "is_public": historical_item.get("is_public", False),
                "version": historical_item["version"] + 1,
                "created_at": historical_item["created_at"],
                "updated_at": int(time.time())
            }
            
            self.settings_table.put_item(Item=restored_setting)
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(restored_setting)
            }
        except Exception as e:
            logger.exception("Error rolling back setting")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _update_visibility(self, event: Dict[str, Any], setting_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            body = json.loads(event.get("body", "{}"))
            is_public = body.get("is_public", False)
            
            self.settings_table.update_item(
                Key={"tenant_id": tenant_id, "setting_id": setting_id},
                UpdateExpression="SET is_public = :public, updated_at = :updated",
                ExpressionAttributeValues={
                    ":public": is_public,
                    ":updated": int(time.time())
                }
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"is_public": is_public})
            }
        except Exception as e:
            logger.exception("Error updating visibility")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _list_public_settings(self) -> Dict[str, Any]:
        try:
            response = self.settings_table.scan(
                FilterExpression="is_public = :public",
                ExpressionAttributeValues={":public": True}
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"settings": response["Items"]})
            }
        except Exception as e:
            logger.exception("Error listing public settings")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
