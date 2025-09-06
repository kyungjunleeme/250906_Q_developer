import boto3
from typing import Dict, List, Optional
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')

class TenantRepository:
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)
    
    def create(self, name: str) -> Dict:
        tenant_id = str(uuid.uuid4())
        item = {
            'tenant_id': tenant_id,
            'name': name,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        self.table.put_item(Item=item)
        return item
    
    def get(self, tenant_id: str) -> Optional[Dict]:
        response = self.table.get_item(Key={'tenant_id': tenant_id})
        return response.get('Item')

class UserRepository:
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)
    
    def create(self, tenant_id: str, email: str, role: str) -> Dict:
        user_id = str(uuid.uuid4())
        item = {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'email': email,
            'role': role,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        self.table.put_item(Item=item)
        return item
    
    def list_by_tenant(self, tenant_id: str) -> List[Dict]:
        response = self.table.query(
            IndexName='tenant-index',
            KeyConditionExpression='tenant_id = :tid',
            ExpressionAttributeValues={':tid': tenant_id}
        )
        return response.get('Items', [])

class ItemRepository:
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)
    
    def create(self, tenant_id: str, name: str, description: str = None) -> Dict:
        item_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        item = {
            'tenant_id': tenant_id,
            'item_id': item_id,
            'name': name,
            'description': description,
            'created_at': now,
            'updated_at': now
        }
        self.table.put_item(Item=item)
        return item
    
    def list_by_tenant(self, tenant_id: str) -> List[Dict]:
        response = self.table.query(
            KeyConditionExpression='tenant_id = :tid',
            ExpressionAttributeValues={':tid': tenant_id}
        )
        return response.get('Items', [])
    
    def update(self, tenant_id: str, item_id: str, name: str, description: str = None) -> Dict:
        self.table.update_item(
            Key={'tenant_id': tenant_id, 'item_id': item_id},
            UpdateExpression='SET #name = :name, description = :desc, updated_at = :updated',
            ExpressionAttributeNames={'#name': 'name'},
            ExpressionAttributeValues={
                ':name': name,
                ':desc': description,
                ':updated': datetime.utcnow().isoformat()
            }
        )
        return self.get(tenant_id, item_id)
    
    def get(self, tenant_id: str, item_id: str) -> Optional[Dict]:
        response = self.table.get_item(Key={'tenant_id': tenant_id, 'item_id': item_id})
        return response.get('Item')
    
    def delete(self, tenant_id: str, item_id: str):
        self.table.delete_item(Key={'tenant_id': tenant_id, 'item_id': item_id})
