import json
import os
import uuid
import time
from typing import Dict, Any
from aws_lambda_powertools import Logger
import boto3
from boto3.dynamodb.conditions import Key

logger = Logger()

class BookmarksHandler:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.bookmarks_table = self.dynamodb.Table(os.environ['BOOKMARKS_TABLE'])
    
    def handle(self, event: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        method = event.get("requestContext", {}).get("http", {}).get("method")
        path = event.get("requestContext", {}).get("http", {}).get("path")
        
        if path == "/bookmarks" and method == "GET":
            return self._list_bookmarks(tenant_id)
        elif path == "/bookmarks" and method == "POST":
            return self._create_bookmark(event, tenant_id)
        elif path.startswith("/bookmarks/") and method == "GET":
            bookmark_id = path.split("/")[-1]
            return self._get_bookmark(bookmark_id, tenant_id)
        elif path.startswith("/bookmarks/") and method == "PUT":
            bookmark_id = path.split("/")[-1]
            return self._update_bookmark(event, bookmark_id, tenant_id)
        elif path.startswith("/bookmarks/") and method == "DELETE":
            bookmark_id = path.split("/")[-1]
            return self._delete_bookmark(bookmark_id, tenant_id)
        
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Not found"})
        }
    
    def _list_bookmarks(self, tenant_id: str) -> Dict[str, Any]:
        try:
            response = self.bookmarks_table.query(
                KeyConditionExpression=Key('tenant_id').eq(tenant_id)
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"bookmarks": response["Items"]})
            }
        except Exception as e:
            logger.exception("Error listing bookmarks")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _create_bookmark(self, event: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        try:
            body = json.loads(event.get("body", "{}"))
            bookmark_id = str(uuid.uuid4())
            
            bookmark = {
                "tenant_id": tenant_id,
                "bookmark_id": bookmark_id,
                "title": body.get("title"),
                "url": body.get("url"),
                "tags": body.get("tags", []),
                "created_at": int(time.time()),
                "updated_at": int(time.time())
            }
            
            self.bookmarks_table.put_item(Item=bookmark)
            
            return {
                "statusCode": 201,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(bookmark)
            }
        except Exception as e:
            logger.exception("Error creating bookmark")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _get_bookmark(self, bookmark_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            response = self.bookmarks_table.get_item(
                Key={"tenant_id": tenant_id, "bookmark_id": bookmark_id}
            )
            
            if "Item" not in response:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Bookmark not found"})
                }
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response["Item"])
            }
        except Exception as e:
            logger.exception("Error getting bookmark")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _update_bookmark(self, event: Dict[str, Any], bookmark_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            body = json.loads(event.get("body", "{}"))
            
            update_expression = "SET updated_at = :updated"
            expression_values = {":updated": int(time.time())}
            
            if "title" in body:
                update_expression += ", title = :title"
                expression_values[":title"] = body["title"]
            
            if "url" in body:
                update_expression += ", #url = :url"
                expression_values[":url"] = body["url"]
            
            if "tags" in body:
                update_expression += ", tags = :tags"
                expression_values[":tags"] = body["tags"]
            
            self.bookmarks_table.update_item(
                Key={"tenant_id": tenant_id, "bookmark_id": bookmark_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={"#url": "url"} if "url" in body else None,
                ExpressionAttributeValues=expression_values,
                ReturnValues="ALL_NEW"
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Bookmark updated"})
            }
        except Exception as e:
            logger.exception("Error updating bookmark")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
    
    def _delete_bookmark(self, bookmark_id: str, tenant_id: str) -> Dict[str, Any]:
        try:
            self.bookmarks_table.delete_item(
                Key={"tenant_id": tenant_id, "bookmark_id": bookmark_id}
            )
            
            return {
                "statusCode": 204,
                "headers": {"Content-Type": "application/json"},
                "body": ""
            }
        except Exception as e:
            logger.exception("Error deleting bookmark")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"})
            }
