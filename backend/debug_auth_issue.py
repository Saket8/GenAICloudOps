#!/usr/bin/env python3
"""
Debug authentication issues and test system health
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_basic_health():
    """Test basic system health"""
    print("🔍 SYSTEM HEALTH DIAGNOSTICS")
    print("=" * 50)
    
    # Test basic health
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        print(f"✅ Basic Health: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Basic Health: {e}")
    
    # Test API root
    try:
        response = requests.get(f"{BASE_URL}/api/v1/", timeout=5)
        print(f"✅ API Root: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Features: {len(data.get('features', []))}")
    except Exception as e:
        print(f"❌ API Root: {e}")

def test_database_connection():
    """Test if database is accessible"""
    print("\n💾 DATABASE CONNECTION TEST")
    print("=" * 50)
    
    # Try to access an endpoint that might show database status
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", timeout=5)
        print(f"Auth Me Endpoint: {response.status_code}")
        if response.status_code == 401:
            print("✅ Auth endpoint accessible (401 expected without token)")
        elif response.status_code == 500:
            print("❌ Database/Auth system error")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Auth endpoint: {e}")

def test_individual_services():
    """Test individual service health endpoints"""
    print("\n🔧 SERVICE HEALTH CHECKS")
    print("=" * 50)
    
    services = [
        ("GenAI", "/api/v1/genai/health"),
        ("Monitoring", "/api/v1/monitoring/test"),
        ("Remediation", "/api/v1/remediation/health"),
        ("Kubernetes", "/api/v1/kubernetes/health")
    ]
    
    for service_name, endpoint in services:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: OK")
            else:
                print(f"⚠️  {service_name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {service_name}: {e}")

def simple_auth_test():
    """Try simple authentication without user creation"""
    print("\n🔐 AUTHENTICATION DEBUG")
    print("=" * 50)
    
    # Check if there are any existing users by trying a simple registration
    print("Attempting simple user registration...")
    
    simple_user = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=simple_user, timeout=10)
        print(f"Registration attempt: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ User created successfully!")
            
            # Try to login
            login_data = {"username": "testuser", "password": "test123"}
            login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data, timeout=10)
            print(f"Login attempt: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data.get("access_token")
                print(f"✅ Login successful! Token: {token[:20] if token else 'None'}...")
                return token
            else:
                print(f"❌ Login failed: {login_response.text}")
        
        elif response.status_code == 400:
            print("ℹ️  User might exist, trying login...")
            
            # Try to login with existing user
            login_data = {"username": "testuser", "password": "test123"}
            login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data, timeout=10)
            print(f"Login attempt: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data.get("access_token")
                print(f"✅ Login successful! Token: {token[:20] if token else 'None'}...")
                return token
            else:
                print(f"❌ Login failed: {login_response.text}")
        
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Auth test error: {e}")
    
    return None

def test_with_admin_token(token):
    """Test Kubernetes configuration with working token"""
    if not token:
        print("\n❌ No token available for Kubernetes testing")
        return
    
    print(f"\n🎯 KUBERNETES TEST WITH TOKEN")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test Kubernetes health
    try:
        response = requests.get(f"{BASE_URL}/api/v1/kubernetes/health", timeout=5)
        print(f"K8s Health (no auth): {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Clusters: {data.get('clusters_configured', 0)}")
    except Exception as e:
        print(f"❌ K8s Health: {e}")
    
    # Test protected endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/kubernetes/cluster-info", headers=headers, timeout=5)
        print(f"K8s Cluster Info (with auth): {response.status_code}")
        if response.status_code == 400:
            print("✅ Auth working, no cluster configured yet (expected)")
        elif response.status_code == 200:
            print("✅ Auth working, cluster already configured!")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ K8s Cluster Info: {e}")

def main():
    print("🔧 AUTHENTICATION & SYSTEM DIAGNOSTICS")
    print("=" * 70)
    
    test_basic_health()
    test_database_connection()
    test_individual_services()
    
    # Try simple authentication
    token = simple_auth_test()
    
    # If we have a token, test Kubernetes
    test_with_admin_token(token)
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    
    if token:
        print("✅ Authentication working!")
        print("✅ Ready to configure Kubernetes with real cluster")
        print(f"\nTo configure cluster manually:")
        print(f"   Token: {token}")
        print(f"   Use this token to call the configure endpoint")
    else:
        print("❌ Authentication issues detected")
        print("   Check backend logs for detailed error information")
        print("   May need to restart backend or check database")

if __name__ == "__main__":
    main() 