#!/usr/bin/env python3
import boto3
import json
import uuid
import time
from botocore.exceptions import ClientError

def get_ssm_parameter(name):
    ssm = boto3.client('ssm', region_name='us-east-1')
    try:
        response = ssm.get_parameter(Name=name)
        return response['Parameter']['Value']
    except ClientError:
        return None

def seed_data():
    print("🌱 Seeding Sync Hub with sample data...")
    
    # Get table names from SSM
    settings_table_name = get_ssm_parameter('/sync-hub/data/settings-table')
    bookmarks_table_name = get_ssm_parameter('/sync-hub/data/bookmarks-table')
    groups_table_name = get_ssm_parameter('/sync-hub/data/groups-table')
    
    if not all([settings_table_name, bookmarks_table_name, groups_table_name]):
        print("❌ Could not retrieve table names from SSM. Make sure stacks are deployed.")
        return
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Seed settings
    settings_table = dynamodb.Table(settings_table_name)
    sample_settings = [
        {
            "tenant_id": "default",
            "setting_id": str(uuid.uuid4()),
            "name": "VS Code Theme",
            "value": "Dark+ (default dark)",
            "is_public": True,
            "version": 1,
            "created_at": int(time.time()),
            "updated_at": int(time.time())
        },
        {
            "tenant_id": "default", 
            "setting_id": str(uuid.uuid4()),
            "name": "Font Size",
            "value": "14",
            "is_public": False,
            "version": 1,
            "created_at": int(time.time()),
            "updated_at": int(time.time())
        }
    ]
    
    for setting in sample_settings:
        settings_table.put_item(Item=setting)
        print(f"✅ Created setting: {setting['name']}")
    
    # Seed bookmarks
    bookmarks_table = dynamodb.Table(bookmarks_table_name)
    sample_bookmarks = [
        {
            "tenant_id": "default",
            "bookmark_id": str(uuid.uuid4()),
            "title": "AWS Documentation",
            "url": "https://docs.aws.amazon.com",
            "tags": ["aws", "documentation"],
            "created_at": int(time.time()),
            "updated_at": int(time.time())
        },
        {
            "tenant_id": "default",
            "bookmark_id": str(uuid.uuid4()),
            "title": "Python.org",
            "url": "https://python.org",
            "tags": ["python", "programming"],
            "created_at": int(time.time()),
            "updated_at": int(time.time())
        }
    ]
    
    for bookmark in sample_bookmarks:
        bookmarks_table.put_item(Item=bookmark)
        print(f"✅ Created bookmark: {bookmark['title']}")
    
    # Seed groups
    groups_table = dynamodb.Table(groups_table_name)
    sample_group = {
        "tenant_id": "default",
        "group_id": str(uuid.uuid4()),
        "name": "Development Team",
        "description": "Main development team settings",
        "owner_id": "default",
        "created_at": int(time.time()),
        "updated_at": int(time.time())
    }
    
    groups_table.put_item(Item=sample_group)
    print(f"✅ Created group: {sample_group['name']}")
    
    print("\n🎉 Seeding completed successfully!")
    print(f"📊 Default tenant_id: 'default'")
    print(f"👤 Admin user: admin@synchub.com")
    print(f"🔑 Temp password: TempPass123!")

if __name__ == "__main__":
    seed_data()
