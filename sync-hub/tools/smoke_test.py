#!/usr/bin/env python3
import requests
import json
import time
import boto3
from botocore.exceptions import ClientError

def get_ssm_parameter(name):
    ssm = boto3.client('ssm', region_name='us-east-1')
    try:
        response = ssm.get_parameter(Name=name)
        return response['Parameter']['Value']
    except ClientError:
        return None

def run_smoke_tests():
    print("🧪 Running Sync Hub Smoke Tests...")
    
    # Get API URL from SSM
    api_url = get_ssm_parameter('/sync-hub/api/url')
    if not api_url:
        print("❌ Could not retrieve API URL from SSM")
        return False
    
    print(f"🔗 Testing API at: {api_url}")
    
    # Test 1: Health Check
    print("\n1️⃣ Testing health check...")
    try:
        response = requests.get(f"{api_url}/_health", timeout=10)
        if response.status_code == 200 and response.json().get('ok'):
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Device Flow Start
    print("\n2️⃣ Testing device flow start...")
    try:
        # Note: This will fail without proper JWT, but we can test the endpoint exists
        response = requests.post(f"{api_url}/auth/device/start", timeout=10)
        if response.status_code in [401, 403]:  # Expected without auth
            print("✅ Device flow endpoint accessible (auth required as expected)")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Device flow error: {e}")
        return False
    
    # Test 3: Public Settings (no auth required)
    print("\n3️⃣ Testing public settings...")
    try:
        response = requests.get(f"{api_url}/settings/public", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Public settings retrieved: {len(data.get('settings', []))} items")
        else:
            print(f"❌ Public settings failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Public settings error: {e}")
        return False
    
    # Test 4: Protected endpoint (should require auth)
    print("\n4️⃣ Testing protected endpoint...")
    try:
        response = requests.get(f"{api_url}/settings", timeout=10)
        if response.status_code in [401, 403]:
            print("✅ Protected endpoint properly secured")
        else:
            print(f"⚠️ Unexpected response for protected endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")
        return False
    
    # Test 5: CORS headers
    print("\n5️⃣ Testing CORS headers...")
    try:
        response = requests.options(f"{api_url}/_health", timeout=10)
        cors_headers = [h for h in response.headers.keys() if h.lower().startswith('access-control')]
        if cors_headers:
            print(f"✅ CORS headers present: {cors_headers}")
        else:
            print("⚠️ No CORS headers found")
    except Exception as e:
        print(f"❌ CORS test error: {e}")
    
    print("\n🎉 Smoke tests completed!")
    return True

def test_web_console():
    print("\n🌐 Testing Web Console...")
    
    web_url = get_ssm_parameter('/sync-hub/web/url')
    if not web_url:
        print("❌ Could not retrieve Web URL from SSM")
        return False
    
    try:
        response = requests.get(web_url, timeout=10)
        if response.status_code == 200 and 'Sync Hub' in response.text:
            print(f"✅ Web console accessible at: {web_url}")
            return True
        else:
            print(f"❌ Web console failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web console error: {e}")
        return False

if __name__ == "__main__":
    api_success = run_smoke_tests()
    web_success = test_web_console()
    
    if api_success and web_success:
        print("\n🎊 All smoke tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check the logs above.")
        exit(1)
