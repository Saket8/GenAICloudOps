"""
Unit tests for AuthService
Tests authentication, user management, and vault integration
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.models.user import User, Role, UserRole, RoleEnum
from app.schemas.auth import UserCreate
from app.core.security import verify_password, get_password_hash


@pytest.mark.unit
class TestAuthService:
    """Test suite for AuthService functionality."""
    
    def test_authenticate_user_success(self, db_session: Session, test_admin_user: User):
        """Test successful user authentication."""
        # Test authentication with correct credentials
        authenticated_user = AuthService.authenticate_user(
            db=db_session,
            username="admin_test",
            password="admin123"
        )
        
        assert authenticated_user is not None
        assert authenticated_user.username == "admin_test"
        assert authenticated_user.email == "admin@test.com"
        assert authenticated_user.is_active is True
    
    def test_authenticate_user_wrong_password(self, db_session: Session, test_admin_user: User):
        """Test authentication with wrong password."""
        authenticated_user = AuthService.authenticate_user(
            db=db_session,
            username="admin_test",
            password="wrong_password"
        )
        
        assert authenticated_user is None
    
    def test_authenticate_user_not_found(self, db_session: Session):
        """Test authentication with non-existent user."""
        authenticated_user = AuthService.authenticate_user(
            db=db_session,
            username="nonexistent_user",
            password="any_password"
        )
        
        assert authenticated_user is None
    
    def test_authenticate_inactive_user(self, db_session: Session):
        """Test authentication with inactive user."""
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
        
        authenticated_user = AuthService.authenticate_user(
            db=db_session,
            username="inactive_user",
            password="password123"
        )
        
        assert authenticated_user is None
    
    def test_create_user_success(self, db_session: Session):
        """Test successful user creation."""
        user_create = UserCreate(
            username="new_user",
            email="newuser@test.com",
            password="newpassword123",
            full_name="New User"
        )
        
        new_user = AuthService.create_user(
            db=db_session,
            user_create=user_create
        )
        
        assert new_user.username == "new_user"
        assert new_user.email == "newuser@test.com"
        assert new_user.full_name == "New User"
        assert new_user.is_active is True
        assert verify_password("newpassword123", new_user.hashed_password)
    
    def test_create_user_duplicate_username(self, db_session: Session, test_admin_user: User):
        """Test user creation with duplicate username."""
        user_create = UserCreate(
            username="admin_test",  # Same as existing user
            email="different@test.com",
            password="password123",
            full_name="Different User"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.create_user(db=db_session, user_create=user_create)
        
        assert exc_info.value.status_code == 400
        assert "Username already registered" in str(exc_info.value.detail)
    
    def test_create_user_duplicate_email(self, db_session: Session, test_admin_user: User):
        """Test user creation with duplicate email."""
        user_create = UserCreate(
            username="different_user",
            email="admin@test.com",  # Same as existing user
            password="password123",
            full_name="Different User"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.create_user(db=db_session, user_create=user_create)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    def test_create_user_with_roles(self, db_session: Session):
        """Test user creation with role assignment."""
        # Create a role first
        admin_role = Role(
            name=RoleEnum.ADMIN,
            description="Admin role",
            permissions=["admin", "read", "write"]
        )
        db_session.add(admin_role)
        db_session.commit()
        
        user_create = UserCreate(
            username="admin_user",
            email="adminuser@test.com",
            password="password123",
            full_name="Admin User"
        )
        
        new_user = AuthService.create_user(
            db=db_session,
            user_create=user_create,
            assign_roles=[RoleEnum.ADMIN]
        )
        
        # Check user has admin role
        user_roles = db_session.query(UserRole).filter(UserRole.user_id == new_user.id).all()
        assert len(user_roles) == 1
        assert user_roles[0].role.name == RoleEnum.ADMIN
    
    def test_get_user_by_username(self, db_session: Session, test_admin_user: User):
        """Test getting user by username."""
        user = AuthService.get_user_by_username(db=db_session, username="admin_test")
        
        assert user is not None
        assert user.username == "admin_test"
        assert user.email == "admin@test.com"
    
    def test_get_user_by_username_not_found(self, db_session: Session):
        """Test getting non-existent user by username."""
        user = AuthService.get_user_by_username(db=db_session, username="nonexistent")
        
        assert user is None
    
    def test_get_user_by_email(self, db_session: Session, test_admin_user: User):
        """Test getting user by email."""
        user = AuthService.get_user_by_email(db=db_session, email="admin@test.com")
        
        assert user is not None
        assert user.username == "admin_test"
        assert user.email == "admin@test.com"
    
    def test_update_user_last_login(self, db_session: Session, test_admin_user: User):
        """Test updating user's last login time."""
        original_last_login = test_admin_user.last_login
        
        # Authenticate user (which updates last login)
        AuthService.authenticate_user(
            db=db_session,
            username="admin_test",
            password="admin123"
        )
        
        # Refresh user from database
        db_session.refresh(test_admin_user)
        
        # Check that last login was updated
        assert test_admin_user.last_login != original_last_login
    
    @pytest.mark.asyncio
    async def test_get_jwt_secret_from_vault_enabled(self):
        """Test getting JWT secret from vault when enabled."""
        with patch('app.services.auth_service.settings') as mock_settings, \
             patch('app.services.auth_service.get_jwt_secret') as mock_get_secret:
            
            mock_settings.OCI_VAULT_ENABLED = True
            mock_get_secret.return_value = "vault-jwt-secret"
            
            secret = await AuthService.get_jwt_secret_from_vault()
            
            assert secret == "vault-jwt-secret"
            mock_get_secret.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_jwt_secret_from_vault_disabled(self):
        """Test getting JWT secret when vault is disabled."""
        with patch('app.services.auth_service.settings') as mock_settings:
            mock_settings.OCI_VAULT_ENABLED = False
            mock_settings.SECRET_KEY = "config-secret-key"
            
            secret = await AuthService.get_jwt_secret_from_vault()
            
            assert secret == "config-secret-key"
    
    @pytest.mark.asyncio
    async def test_get_jwt_secret_vault_fallback(self):
        """Test JWT secret fallback when vault returns None."""
        with patch('app.services.auth_service.settings') as mock_settings, \
             patch('app.services.auth_service.get_jwt_secret') as mock_get_secret:
            
            mock_settings.OCI_VAULT_ENABLED = True
            mock_settings.SECRET_KEY = "fallback-secret"
            mock_get_secret.return_value = None
            
            secret = await AuthService.get_jwt_secret_from_vault()
            
            assert secret == "fallback-secret"
    
    @pytest.mark.asyncio
    async def test_rotate_jwt_secret_vault_enabled(self):
        """Test JWT secret rotation when vault is enabled."""
        with patch('app.services.auth_service.settings') as mock_settings, \
             patch('app.services.auth_service.vault_service') as mock_vault_service:
            
            mock_settings.OCI_VAULT_ENABLED = True
            mock_vault_service.rotate_secret = AsyncMock(return_value=True)
            
            result = await AuthService.rotate_jwt_secret("new-secret")
            
            assert result is True
            mock_vault_service.rotate_secret.assert_called_once_with('jwt_secret_key', 'new-secret')
    
    @pytest.mark.asyncio
    async def test_rotate_jwt_secret_vault_disabled(self):
        """Test JWT secret rotation when vault is disabled."""
        with patch('app.services.auth_service.settings') as mock_settings:
            mock_settings.OCI_VAULT_ENABLED = False
            
            result = await AuthService.rotate_jwt_secret("new-secret")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_rotate_jwt_secret_auto_generation(self):
        """Test JWT secret rotation with auto-generated secret."""
        with patch('app.services.auth_service.settings') as mock_settings, \
             patch('app.services.auth_service.vault_service') as mock_vault_service, \
             patch('secrets.token_urlsafe') as mock_token:
            
            mock_settings.OCI_VAULT_ENABLED = True
            mock_vault_service.rotate_secret = AsyncMock(return_value=True)
            mock_token.return_value = "auto-generated-secret"
            
            result = await AuthService.rotate_jwt_secret()
            
            assert result is True
            mock_vault_service.rotate_secret.assert_called_once_with('jwt_secret_key', 'auto-generated-secret')
            mock_token.assert_called_once_with(64)
    
    @pytest.mark.asyncio
    async def test_store_api_key_vault_enabled(self):
        """Test storing API key when vault is enabled."""
        with patch('app.services.auth_service.settings') as mock_settings, \
             patch('app.services.auth_service.vault_service') as mock_vault_service:
            
            mock_settings.OCI_VAULT_ENABLED = True
            mock_vault_service.store_secret = AsyncMock(return_value=True)
            
            result = await AuthService.store_api_key("groq", "test-api-key", "Test API key")
            
            assert result is True
            mock_vault_service.store_secret.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_api_key_vault_disabled(self):
        """Test storing API key when vault is disabled."""
        with patch('app.services.auth_service.settings') as mock_settings:
            mock_settings.OCI_VAULT_ENABLED = False
            
            result = await AuthService.store_api_key("groq", "test-api-key")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_api_key_vault_enabled(self):
        """Test getting API key when vault is enabled."""
        with patch('app.services.auth_service.settings') as mock_settings, \
             patch('app.services.auth_service.get_api_key') as mock_get_api_key:
            
            mock_settings.OCI_VAULT_ENABLED = True
            mock_get_api_key.return_value = "vault-api-key"
            
            api_key = await AuthService.get_api_key("groq")
            
            assert api_key == "vault-api-key"
            mock_get_api_key.assert_called_once_with("groq")
    
    @pytest.mark.asyncio
    async def test_get_api_key_vault_disabled_groq(self):
        """Test getting Groq API key when vault is disabled."""
        with patch('app.services.auth_service.settings') as mock_settings:
            mock_settings.OCI_VAULT_ENABLED = False
            mock_settings.GROQ_API_KEY = "config-groq-key"
            
            api_key = await AuthService.get_api_key("groq")
            
            assert api_key == "config-groq-key"
    
    @pytest.mark.asyncio
    async def test_get_api_key_vault_disabled_unknown_service(self):
        """Test getting API key for unknown service when vault is disabled."""
        with patch('app.services.auth_service.settings') as mock_settings:
            mock_settings.OCI_VAULT_ENABLED = False
            
            api_key = await AuthService.get_api_key("unknown")
            
            assert api_key is None
    
    @pytest.mark.asyncio
    async def test_rotate_api_key_vault_enabled(self):
        """Test rotating API key when vault is enabled."""
        with patch('app.services.auth_service.settings') as mock_settings, \
             patch('app.services.auth_service.vault_service') as mock_vault_service:
            
            mock_settings.OCI_VAULT_ENABLED = True
            mock_vault_service.rotate_secret = AsyncMock(return_value=True)
            
            result = await AuthService.rotate_api_key("groq", "new-api-key")
            
            assert result is True
            mock_vault_service.rotate_secret.assert_called_once_with('groq_api_key', 'new-api-key')
    
    @pytest.mark.asyncio
    async def test_rotate_api_key_vault_disabled(self):
        """Test rotating API key when vault is disabled."""
        with patch('app.services.auth_service.settings') as mock_settings:
            mock_settings.OCI_VAULT_ENABLED = False
            
            result = await AuthService.rotate_api_key("groq", "new-api-key")
            
            assert result is False


@pytest.mark.unit
class TestAuthServiceRoleManagement:
    """Test suite for role management functionality."""
    
    def test_assign_role_to_user(self, db_session: Session):
        """Test assigning a role to a user."""
        # Create user and role
        user = User(
            username="test_user",
            email="test@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Test User",
            is_active=True
        )
        role = Role(
            name=RoleEnum.USER,
            description="User role",
            permissions=["read"]
        )
        db_session.add(user)
        db_session.add(role)
        db_session.commit()
        
        # Assign role using AuthService (if method exists) or directly
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(user_role)
        db_session.commit()
        
        # Verify assignment
        assigned_roles = db_session.query(UserRole).filter(UserRole.user_id == user.id).all()
        assert len(assigned_roles) == 1
        assert assigned_roles[0].role.name == RoleEnum.USER
    
    def test_user_has_permission(self, db_session: Session, test_admin_user: User):
        """Test checking if user has specific permission."""
        # Get user's roles and check permissions
        user_roles = db_session.query(UserRole).filter(UserRole.user_id == test_admin_user.id).all()
        
        assert len(user_roles) > 0
        
        # Check if user has admin permission
        has_admin_permission = any(
            "admin" in role.role.permissions 
            for role in user_roles
        )
        assert has_admin_permission is True
    
    def test_create_multiple_roles(self, db_session: Session):
        """Test creating multiple roles with different permissions."""
        roles_data = [
            {
                "name": RoleEnum.ADMIN,
                "description": "Administrator",
                "permissions": ["admin", "read", "write", "execute"]
            },
            {
                "name": RoleEnum.USER,
                "description": "Regular User",
                "permissions": ["read"]
            },
            {
                "name": RoleEnum.VIEWER,
                "description": "Read-only User",
                "permissions": ["read"]
            }
        ]
        
        created_roles = []
        for role_data in roles_data:
            role = Role(**role_data)
            db_session.add(role)
            created_roles.append(role)
        
        db_session.commit()
        
        # Verify all roles were created
        assert len(created_roles) == 3
        
        # Verify permissions
        admin_role = next(r for r in created_roles if r.name == RoleEnum.ADMIN)
        assert "admin" in admin_role.permissions
        assert len(admin_role.permissions) == 4


@pytest.mark.unit
class TestAuthServiceValidation:
    """Test suite for input validation and edge cases."""
    
    def test_create_user_empty_username(self, db_session: Session):
        """Test user creation with empty username."""
        user_create = UserCreate(
            username="",
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
        
        # This should be handled by Pydantic validation
        # If it reaches the service, test the behavior
        try:
            AuthService.create_user(db=db_session, user_create=user_create)
            pytest.fail("Should have raised validation error")
        except Exception as e:
            # Expected to fail due to validation
            assert True
    
    def test_create_user_invalid_email(self, db_session: Session):
        """Test user creation with invalid email format."""
        user_create = UserCreate(
            username="test_user",
            email="invalid-email",
            password="password123",
            full_name="Test User"
        )
        
        # This should be handled by Pydantic validation
        try:
            AuthService.create_user(db=db_session, user_create=user_create)
            pytest.fail("Should have raised validation error")
        except Exception as e:
            # Expected to fail due to validation
            assert True
    
    def test_authenticate_user_case_sensitivity(self, db_session: Session, test_admin_user: User):
        """Test username case sensitivity in authentication."""
        # Test with different case
        authenticated_user = AuthService.authenticate_user(
            db=db_session,
            username="ADMIN_TEST",  # Uppercase
            password="admin123"
        )
        
        # Depending on implementation, this might return None
        # Most systems are case-sensitive for usernames
        assert authenticated_user is None
    
    def test_password_hashing_consistency(self, db_session: Session):
        """Test that password hashing is consistent and secure."""
        password = "test_password_123"
        
        # Hash the same password multiple times
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
        
        # Wrong password should not verify
        assert verify_password("wrong_password", hash1) is False 