#!/usr/bin/env python3
import requests
import boto3
import sys
import os

def get_endpoints():
    ssm = boto3.client('ssm', region_name='us-east-1')
    stage = os.environ.get('STAGE', 'dev')
    
    try:
        api_url = ssm.get_parameter(Name=f'/saas/{stage}/api/url')['Parameter']['Value']
        user_url = ssm.get_parameter(Name=f'/saas/{stage}/web/user-url')['Parameter']['Value']
        admin_url = ssm.get_parameter(Name=f'/saas/{stage}/web/admin-url')['Parameter']['Value']
        return api_url, user_url, admin_url
    except Exception as e:
        print(f"Error getting endpoints: {e}")
        return None, None, None

def test_health_endpoint(url, name):
    try:
        response = requests.get(f"{url}/_health", timeout=10)
        if response.status_code == 200:
            print(f"✓ {name} health check passed")
            return True
        else:
            print(f"✗ {name} health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ {name} health check failed: {e}")
        return False

def main():
    print("Running smoke tests...")
    
    api_url, user_url, admin_url = get_endpoints()
    
    if not all([api_url, user_url, admin_url]):
        print("Could not retrieve all endpoints")
        sys.exit(1)
    
    results = []
    results.append(test_health_endpoint(api_url, "API"))
    results.append(test_health_endpoint(user_url, "User Web"))
    results.append(test_health_endpoint(admin_url, "Admin Web"))
    
    if all(results):
        print("\n✓ All smoke tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some smoke tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
