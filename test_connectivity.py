#!/usr/bin/env python3
"""
Quick connectivity test for GenAI CloudOps application
Tests both frontend and backend accessibility
"""

import requests
import time

def test_backend():
    """Test backend connectivity"""
    try:
        print("🔄 Testing backend connectivity...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is accessible at http://localhost:8000")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_frontend():
    """Test frontend connectivity"""
    try:
        print("🔄 Testing frontend connectivity...")
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible at http://localhost:3000")
            return True
        else:
            print(f"❌ Frontend returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend connection failed: {e}")
        return False

def test_login():
    """Test login functionality with admin credentials"""
    try:
        print("🔄 Testing login functionality...")
        login_data = {
            "username": "admin",
            "password": "AdminPass123!"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Login successful with admin credentials")
            data = response.json()
            print(f"   Access token received: {data.get('access_token', 'N/A')[:20]}...")
            return True
        else:
            print(f"❌ Login failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Login test failed: {e}")
        return False

def main():
    """Run all connectivity tests"""
    print("🚀 GenAI CloudOps - Connectivity Test")
    print("=" * 50)
    
    # Test backend
    backend_ok = test_backend()
    time.sleep(1)
    
    # Test frontend
    frontend_ok = test_frontend()
    time.sleep(1)
    
    # Test login if backend is working
    login_ok = False
    if backend_ok:
        login_ok = test_login()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Backend:  {'✅ Working' if backend_ok else '❌ Failed'}")
    print(f"   Frontend: {'✅ Working' if frontend_ok else '❌ Failed'}")
    print(f"   Login:    {'✅ Working' if login_ok else '❌ Failed'}")
    
    if backend_ok and frontend_ok and login_ok:
        print("\n🎉 All systems working! You can now:")
        print("   1. Open http://localhost:3000 in your browser")
        print("   2. Login with: admin / AdminPass123!")
    else:
        print("\n⚠️  Some issues detected. Check the errors above.")
        
        if not backend_ok:
            print("   • Backend may not be running. Start with: python main.py")
        if not frontend_ok:
            print("   • Frontend may not be running. Start with: npm run dev")

if __name__ == "__main__":
    main() 