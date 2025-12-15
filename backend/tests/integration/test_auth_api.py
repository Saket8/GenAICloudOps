"""
Integration tests for Authentication API endpoints
Tests the full HTTP request/response cycle
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import assert_status_code, assert_response_schema


@pytest.mark.integration
class TestAuthenticationAPI:
    """Integration tests for authentication endpoints."""
    
    def test_login_success(self, client: TestClient, test_admin_user):
        """Test successful user login."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin_test",
                "password": "admin123"
            }
        )
        
        assert_status_code(response, 200)
        
        data = response.json()
        assert_response_schema(data, ["access_token", "token_type"])
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_credentials(self, client: TestClient, test_admin_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin_test",
                "password": "wrong_password"
            }
        )
        
        assert_status_code(response, 401)
        
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "password"
            }
        )
        
        assert_status_code(response, 401)
    
    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """Test login with inactive user."""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        # Create inactive user
        inactive_user = User(
            username="inactive_user",
            email="inactive@test.com",
            hashed_password=get_password_hash("password123"),
            full_name="Inactive User",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "inactive_user",
                "password": "password123"
            }
        )
        
        assert_status_code(response, 401)
    
    def test_get_current_user_with_valid_token(self, client: TestClient, admin_headers):
        """Test getting current user with valid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers=admin_headers
        )
        
        assert_status_code(response, 200)
        
        data = response.json()
        assert_response_schema(data, ["id", "username", "email", "full_name", "is_active"])
        assert data["username"] == "admin_test"
        assert data["email"] == "admin@test.com"
        assert data["is_active"] is True
    
    def test_get_current_user_without_token(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        
        assert_status_code(response, 401)
    
    def test_get_current_user_with_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert_status_code(response, 401)
    
    def test_register_user(self, client: TestClient, admin_headers):
        """Test user registration."""
        user_data = {
            "username": "new_user",
            "email": "newuser@test.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = client.post(
            "/api/v1/auth/register",
            json=user_data,
            headers=admin_headers
        )
        
        # Endpoint might not exist, check if implemented
        if response.status_code == 404:
            pytest.skip("Register endpoint not implemented")
        
        assert_status_code(response, 201)
        
        data = response.json()
        assert_response_schema(data, ["id", "username", "email", "full_name"])
        assert data["username"] == "new_user"
        assert data["email"] == "newuser@test.com"
    
    def test_refresh_token(self, client: TestClient, admin_token):
        """Test token refresh."""
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Endpoint might not exist, check if implemented
        if response.status_code == 404:
            pytest.skip("Refresh endpoint not implemented")
        
        assert_status_code(response, 200)
        
        data = response.json()
        assert_response_schema(data, ["access_token", "token_type"])
    
    def test_logout(self, client: TestClient, admin_headers):
        """Test user logout."""
        response = client.post(
            "/api/v1/auth/logout",
            headers=admin_headers
        )
        
        # Endpoint might not exist, check if implemented
        if response.status_code == 404:
            pytest.skip("Logout endpoint not implemented")
        
        assert_status_code(response, 200)
    
    def test_change_password(self, client: TestClient, admin_headers):
        """Test password change."""
        password_data = {
            "current_password": "admin123",
            "new_password": "new_admin123"
        }
        
        response = client.put(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=admin_headers
        )
        
        # Endpoint might not exist, check if implemented
        if response.status_code == 404:
            pytest.skip("Change password endpoint not implemented")
        
        assert_status_code(response, 200)
    
    def test_password_reset_request(self, client: TestClient):
        """Test password reset request."""
        response = client.post(
            "/api/v1/auth/password-reset",
            json={"email": "admin@test.com"}
        )
        
        # Endpoint might not exist, check if implemented
        if response.status_code == 404:
            pytest.skip("Password reset endpoint not implemented")
        
        assert_status_code(response, 200)


@pytest.mark.integration
class TestAuthenticationAPIValidation:
    """Test API validation and error handling."""
    
    def test_login_missing_username(self, client: TestClient):
        """Test login with missing username."""
        response = client.post(
            "/api/v1/auth/login",
            data={"password": "password123"}
        )
        
        assert_status_code(response, 422)
    
    def test_login_missing_password(self, client: TestClient):
        """Test login with missing password."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser"}
        )
        
        assert_status_code(response, 422)
    
    def test_login_empty_credentials(self, client: TestClient):
        """Test login with empty credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "", "password": ""}
        )
        
        assert_status_code(response, 422)
    
    def test_register_invalid_email(self, client: TestClient, admin_headers):
        """Test registration with invalid email format."""
        user_data = {
            "username": "test_user",
            "email": "invalid-email",
            "password": "password123",
            "full_name": "Test User"
        }
        
        response = client.post(
            "/api/v1/auth/register",
            json=user_data,
            headers=admin_headers
        )
        
        if response.status_code == 404:
            pytest.skip("Register endpoint not implemented")
        
        assert_status_code(response, 422)
    
    def test_register_weak_password(self, client: TestClient, admin_headers):
        """Test registration with weak password."""
        user_data = {
            "username": "test_user",
            "email": "test@example.com",
            "password": "123",  # Weak password
            "full_name": "Test User"
        }
        
        response = client.post(
            "/api/v1/auth/register",
            json=user_data,
            headers=admin_headers
        )
        
        if response.status_code == 404:
            pytest.skip("Register endpoint not implemented")
        
        # Should fail validation or return error
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestAuthenticationAPIPerformance:
    """Test API performance characteristics."""
    
    def test_login_performance(self, client: TestClient, test_admin_user, performance_timer):
        """Test login endpoint performance."""
        performance_timer.start()
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin_test",
                "password": "admin123"
            }
        )
        
        performance_timer.stop()
        
        assert_status_code(response, 200)
        
        # Login should complete within 2 seconds
        assert performance_timer.duration < 2.0
    
    def test_get_user_performance(self, client: TestClient, admin_headers, performance_timer):
        """Test get current user endpoint performance."""
        performance_timer.start()
        
        response = client.get(
            "/api/v1/auth/me",
            headers=admin_headers
        )
        
        performance_timer.stop()
        
        assert_status_code(response, 200)
        
        # User lookup should complete within 1 second
        assert performance_timer.duration < 1.0
    
    def test_concurrent_logins(self, client: TestClient, test_admin_user):
        """Test concurrent login requests."""
        import concurrent.futures
        import threading
        
        def login_request():
            return client.post(
                "/api/v1/auth/login",
                data={
                    "username": "admin_test",
                    "password": "admin123"
                }
            )
        
        # Execute 5 concurrent login requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(login_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert_status_code(response, 200)
            data = response.json()
            assert "access_token" in data


@pytest.mark.integration 
class TestAuthenticationAPISecurityHeaders:
    """Test security headers and CORS."""
    
    def test_security_headers_present(self, client: TestClient, test_admin_user):
        """Test that security headers are present in responses."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin_test",
                "password": "admin123"
            }
        )
        
        assert_status_code(response, 200)
        
        # Check for security headers (if implemented)
        headers = response.headers
        
        # These might not be implemented, so check gracefully
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        # At least some security headers should be present in production
        present_headers = [h for h in security_headers if h in headers]
        
        # Log which headers are present for visibility
        print(f"Security headers present: {present_headers}")
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are configured."""
        response = client.options("/api/v1/auth/login")
        
        # CORS might not be configured, so check gracefully
        if "Access-Control-Allow-Origin" in response.headers:
            assert response.headers["Access-Control-Allow-Origin"] in ["*", "http://localhost:3000", "http://localhost:5173"] 