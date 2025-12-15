from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends, Header
from app.models.user import User, Role, UserRole, RoleEnum
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_token,
    verify_refresh_token,
    create_password_reset_token,
    verify_password_reset_token
)
from app.schemas.auth import UserCreate, UserLogin, Token
from app.core.config import settings
from .oci_vault_service import get_jwt_secret, get_vault_service

class AuthService:
    """Authentication service for user management and JWT tokens with OCI Vault integration"""
    
    @staticmethod
    async def get_jwt_secret_from_vault() -> str:
        """Get JWT secret from OCI Vault or fallback to config"""
        if settings.OCI_VAULT_ENABLED:
            vault_secret = await get_jwt_secret()
            if vault_secret:
                return vault_secret
        
        # Fallback to config-based secret
        return settings.SECRET_KEY
    
    @staticmethod
    async def rotate_jwt_secret(new_secret: Optional[str] = None) -> bool:
        """Rotate JWT secret in OCI Vault"""
        if not settings.OCI_VAULT_ENABLED:
            return False
        
        if not new_secret:
            # Generate a new secure random secret
            import secrets
            new_secret = secrets.token_urlsafe(64)
        
        # Store new secret in vault
        return await get_vault_service().rotate_secret('jwt_secret_key', new_secret)
    
    @staticmethod
    async def store_api_key(service_name: str, api_key: str, description: str = "") -> bool:
        """Store API key for a service in OCI Vault"""
        if not settings.OCI_VAULT_ENABLED:
            return False
        
        from .oci_vault_service import SecretType
        return await get_vault_service().store_secret(
            f'{service_name}_api_key',
            api_key,
            SecretType.API_KEY,
            description or f"API key for {service_name} service",
            tags={'service': service_name, 'type': 'api_key'}
        )
    
    @staticmethod
    async def get_api_key(service_name: str) -> Optional[str]:
        """Get API key for a service from OCI Vault"""
        if not settings.OCI_VAULT_ENABLED:
            # Fallback to config-based API keys
            if service_name.lower() == 'groq':
                return settings.GROQ_API_KEY
            return None
        
        from .oci_vault_service import get_api_key
        return await get_api_key(service_name)
    
    @staticmethod
    async def rotate_api_key(service_name: str, new_api_key: str) -> bool:
        """Rotate API key for a service"""
        if not settings.OCI_VAULT_ENABLED:
            return False
        
        return await get_vault_service().rotate_secret(f'{service_name}_api_key', new_api_key)
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate, assign_roles: list[RoleEnum] = None) -> User:
        """Create new user with optional role assignment"""
        # Check if username already exists
        if db.query(User).filter(User.username == user_create.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        if db.query(User).filter(User.email == user_create.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            is_active=True,
            is_verified=False
        )
        
        db.add(db_user)
        db.flush()  # Flush to get user ID
        
        # Assign roles
        if assign_roles:
            for role_name in assign_roles:
                role = db.query(Role).filter(Role.name == role_name).first()
                if role:
                    user_role = UserRole(user_id=db_user.id, role_id=role.id)
                    db.add(user_role)
        else:
            # Assign default VIEWER role
            default_role = db.query(Role).filter(Role.name == RoleEnum.VIEWER).first()
            if default_role:
                user_role = UserRole(user_id=db_user.id, role_id=default_role.id)
                db.add(user_role)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def create_tokens(user: User) -> Token:
        """Create access and refresh tokens for user"""
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Token:
        """Create new access token from refresh token"""
        user_id = verify_refresh_token(refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return AuthService.create_tokens(user)
    
    @staticmethod
    def get_current_user_from_token(token: str) -> User:
        """Get current user from JWT token"""
        user_data = verify_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID from token
        user_id = int(user_data) if isinstance(user_data, str) else user_data.get('user_id', 1)
        
        # Fetch real user from database
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user
        finally:
            db.close()
    
    async def get_user_from_token(self, token: str) -> User:
        """Async version of get_current_user_from_token for WebSocket use"""
        try:
            return self.get_current_user_from_token(token)
        except HTTPException:
            return None
    
    @staticmethod
    def extract_token_from_header(authorization: str = Header(None)) -> str:
        """Extract Bearer token from Authorization header"""
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def get_current_user(authorization: str = Header(None)) -> User:
        """FastAPI dependency to get current user from Authorization header"""
        token = AuthService.extract_token_from_header(authorization)
        return AuthService.get_current_user_from_token(token)
    
    @staticmethod
    def get_user_permissions(db: Session, user: User) -> Dict[str, bool]:
        """Get user permissions based on roles"""
        permissions = {
            "can_view_dashboard": False,
            "can_view_alerts": False,
            "can_approve_remediation": False,
            "can_execute_remediation": False,
            "can_manage_users": False,
            "can_manage_roles": False,
            "can_view_access_analyzer": False,
            "can_view_pod_analyzer": False,
            "can_view_cost_analyzer": False,
            "can_use_chatbot": False
        }
        
        # Get all user roles
        user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        
        for user_role in user_roles:
            role = db.query(Role).filter(Role.id == user_role.role_id).first()
            if role:
                # Combine permissions (OR operation - if any role grants permission)
                permissions["can_view_dashboard"] |= role.can_view_dashboard
                permissions["can_view_alerts"] |= role.can_view_alerts
                permissions["can_approve_remediation"] |= role.can_approve_remediation
                permissions["can_execute_remediation"] |= role.can_execute_remediation
                permissions["can_manage_users"] |= role.can_manage_users
                permissions["can_manage_roles"] |= role.can_manage_roles
                permissions["can_view_access_analyzer"] |= role.can_view_access_analyzer
                permissions["can_view_pod_analyzer"] |= role.can_view_pod_analyzer
                permissions["can_view_cost_analyzer"] |= role.can_view_cost_analyzer
                permissions["can_use_chatbot"] |= role.can_use_chatbot
        
        return permissions
    
    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
        """Change user password"""
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True
    
    @staticmethod
    def initiate_password_reset(db: Session, email: str) -> str:
        """Initiate password reset process"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if email exists for security
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="If email exists, reset instructions have been sent"
            )
        
        reset_token = create_password_reset_token(email)
        # In a real implementation, you would send this token via email
        return reset_token
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        email = verify_password_reset_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True 