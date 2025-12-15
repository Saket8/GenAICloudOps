#!/usr/bin/env python3
"""
Simple Frontend Validation Test
Checks if the React frontend is accessible and running
"""

import requests
import sys

def test_frontend():
    """Test if frontend development server is running"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        
        if response.status_code == 200:
            print("✅ Frontend development server is running on http://localhost:3000")
            print("✅ React application is accessible")
            return True
        else:
            print(f"❌ Frontend returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Frontend development server not running on port 3000")
        print("   Please run 'npm run dev' in the frontend directory")
        return False
    except requests.exceptions.Timeout:
        print("❌ Frontend server timeout")
        return False
    except Exception as e:
        print(f"❌ Error connecting to frontend: {str(e)}")
        return False

def main():
    print("🌐 FRONTEND VALIDATION")
    print("=" * 30)
    
    if test_frontend():
        print("\n✅ Frontend Status: VALIDATED")
        print("\n🎯 You can now test the full authentication flow:")
        print("   1. Open http://localhost:3000 in your browser")
        print("   2. Try logging in with:")
        print("      • Username: admin, Password: AdminPass123!")
        print("      • Username: operator, Password: OperatorPass123!")
        print("      • Username: viewer, Password: ViewerPass123!")
        print("   3. Verify role-based access and protected routes")
    else:
        print("\n❌ Frontend validation failed")
        print("   Make sure the frontend server is running with 'npm run dev'")

if __name__ == "__main__":
    main() 