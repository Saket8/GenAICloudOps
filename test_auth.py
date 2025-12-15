#!/usr/bin/env python3
"""
Comprehensive Authentication System Test Script
Tests all authentication endpoints and functionality for Task-002 validation
"""

import requests
import json
import sys
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

class AuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        print(f"{status} | {test_name}")
        if details:
            print(f"      {details}")
        print()

    def test_api_health(self):
        """Test API health endpoints"""
        try:
            # Test root endpoint
            response = self.session.get(f"{BASE_URL}/")
            root_working = response.status_code == 200
            
            # Test health endpoint
            response = self.session.get(f"{BASE_URL}/health")
            health_working = response.status_code == 200
            
            passed = root_working and health_working
            details = f"Root: {response.status_code}, Health: {response.status_code}"
            self.log_test("API Health Check", passed, details)
            return passed
            
        except requests.exceptions.ConnectionError:
            self.log_test("API Health Check", False, "Backend server not running on port 8000")
            return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
            return False

    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            test_user = {
                "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
                "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
                "password": "TestPass123!",
                "full_name": "Test User"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            passed = response.status_code == 201
            
            if passed:
                user_data = response.json()
                details = f"Created user ID: {user_data.get('id')} ({user_data.get('username')})"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
                
            self.log_test("User Registration", passed, details)
            return passed, test_user if passed else None
            
        except Exception as e:
            self.log_test("User Registration", False, f"Error: {str(e)}")
            return False, None

    def test_user_login(self, username, password):
        """Test user login endpoint"""
        try:
            login_data = {
                "username": username,
                "password": password
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            passed = response.status_code == 200
            
            if passed:
                token_data = response.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                details = f"Tokens received - Access: {access_token[:20]}..., Refresh: {refresh_token[:20]}..."
                return passed, token_data
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
                self.log_test("User Login", passed, details)
                return False, None
                
        except Exception as e:
            self.log_test("User Login", False, f"Error: {str(e)}")
            return False, None

    def test_protected_endpoints(self, access_token):
        """Test protected endpoints with authentication"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            # Test /me endpoint
            response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
            me_working = response.status_code == 200
            
            # Test /permissions endpoint
            response = self.session.get(f"{BASE_URL}/auth/me/permissions", headers=headers)
            permissions_working = response.status_code == 200
            
            # Test token verification
            response = self.session.get(f"{BASE_URL}/auth/verify-token", headers=headers)
            verify_working = response.status_code == 200
            
            passed = me_working and permissions_working and verify_working
            details = f"Me: {me_working}, Permissions: {permissions_working}, Verify: {verify_working}"
            
            self.log_test("Protected Endpoints", passed, details)
            return passed
            
        except Exception as e:
            self.log_test("Protected Endpoints", False, f"Error: {str(e)}")
            return False

    def test_token_refresh(self, refresh_token):
        """Test token refresh functionality"""
        try:
            refresh_data = {"refresh_token": refresh_token}
            response = self.session.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
            
            passed = response.status_code == 200
            
            if passed:
                new_tokens = response.json()
                details = f"New access token: {new_tokens.get('access_token')[:20]}..."
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
                
            self.log_test("Token Refresh", passed, details)
            return passed
            
        except Exception as e:
            self.log_test("Token Refresh", False, f"Error: {str(e)}")
            return False

    def test_role_based_access(self):
        """Test different user roles and their permissions"""
        test_users = [
            {"username": "admin", "password": "AdminPass123!", "expected_role": "admin"},
            {"username": "operator", "password": "OperatorPass123!", "expected_role": "operator"},
            {"username": "viewer", "password": "ViewerPass123!", "expected_role": "viewer"}
        ]
        
        for user in test_users:
            try:
                # Login as user
                login_success, token_data = self.test_user_login(user["username"], user["password"])
                
                if login_success:
                    # Check permissions
                    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                    response = self.session.get(f"{BASE_URL}/auth/me/permissions", headers=headers)
                    
                    if response.status_code == 200:
                        permissions = response.json()["permissions"]
                        
                        # Validate role-specific permissions
                        if user["expected_role"] == "admin":
                            passed = permissions.get("can_manage_users", False)
                        elif user["expected_role"] == "operator":
                            passed = permissions.get("can_approve_remediation", False) and not permissions.get("can_manage_users", True)
                        else:  # viewer
                            passed = not permissions.get("can_approve_remediation", True) and not permissions.get("can_manage_users", True)
                        
                        details = f"User: {user['username']}, Role permissions validated"
                    else:
                        passed = False
                        details = f"Failed to get permissions for {user['username']}"
                else:
                    passed = False
                    details = f"Failed to login as {user['username']}"
                    
                self.log_test(f"Role-Based Access ({user['expected_role']})", passed, details)
                
            except Exception as e:
                self.log_test(f"Role-Based Access ({user['expected_role']})", False, f"Error: {str(e)}")

    def test_invalid_credentials(self):
        """Test handling of invalid credentials"""
        try:
            # Test with invalid username
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": "nonexistent",
                "password": "wrongpassword"
            })
            
            passed = response.status_code == 401
            details = f"Invalid login properly rejected with status {response.status_code}"
            
            self.log_test("Invalid Credentials Handling", passed, details)
            return passed
            
        except Exception as e:
            self.log_test("Invalid Credentials Handling", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run comprehensive authentication system tests"""
        print("🧪 STARTING AUTHENTICATION SYSTEM VALIDATION")
        print("=" * 60)
        print()
        
        # Test 1: API Health
        if not self.test_api_health():
            print("❌ Backend server not accessible. Please start the server with 'python main.py'")
            return False
            
        # Test 2: User Registration
        reg_success, test_user = self.test_user_registration()
        
        # Test 3: User Login (with test user if registration worked, otherwise use admin)
        if reg_success:
            login_success, token_data = self.test_user_login(test_user["username"], test_user["password"])
        else:
            login_success, token_data = self.test_user_login("admin", "AdminPass123!")
            
        if login_success:
            self.log_test("User Login", True, f"Successfully logged in")
            
            # Test 4: Protected Endpoints
            self.test_protected_endpoints(token_data["access_token"])
            
            # Test 5: Token Refresh
            self.test_token_refresh(token_data["refresh_token"])
        
        # Test 6: Role-Based Access Control
        self.test_role_based_access()
        
        # Test 7: Invalid Credentials
        self.test_invalid_credentials()
        
        # Summary
        print("=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for test in self.test_results if test["passed"])
        total_tests = len(self.test_results)
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Authentication system is working perfectly!")
            return True
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed. Please check the errors above.")
            return False

def main():
    """Main test execution"""
    tester = AuthTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Task-002 Authentication System: VALIDATED ✅")
        print("\n🚀 Ready to proceed with Task-003!")
    else:
        print("\n❌ Some tests failed. Please review and fix issues.")
        sys.exit(1)

if __name__ == "__main__":
    main() 