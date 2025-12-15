from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserCreate, 
    UserLogin, 
    Token, 
    TokenRefresh, 
    UserResponse,
    PasswordReset,
    PasswordResetConfirm,
    PasswordChange
)
from app.models.user import User
from typing import Dict, Any

router = APIRouter()
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return AuthService.get_current_user_from_token(token)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        user = AuthService.create_user(db, user_create)
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens"""
    user = AuthService.authenticate_user(db, user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return AuthService.create_tokens(user)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_refresh: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    return AuthService.refresh_access_token(db, token_refresh.refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.get("/me/permissions")
async def get_current_user_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current user permissions"""
    permissions = AuthService.get_user_permissions(db, current_user)
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "permissions": permissions
    }

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    AuthService.change_password(
        db, 
        current_user, 
        password_change.current_password, 
        password_change.new_password
    )
    return {"message": "Password changed successfully"}

@router.post("/password-reset/initiate")
async def initiate_password_reset(
    password_reset: PasswordReset,
    db: Session = Depends(get_db)
):
    """Initiate password reset process"""
    reset_token = AuthService.initiate_password_reset(db, password_reset.email)
    
    # In production, you would send the reset_token via email
    # For development, we'll return it (remove this in production!)
    return {
        "message": "If email exists, reset instructions have been sent",
        "reset_token": reset_token  # Remove this in production!
    }

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    AuthService.reset_password(
        db, 
        password_reset_confirm.token, 
        password_reset_confirm.new_password
    )
    return {"message": "Password reset successfully"}

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """Logout user (client should discard tokens)"""
    # In a more advanced implementation, you might blacklist the token
    return {"message": "Successfully logged out"}

@router.get("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """Verify if token is valid"""
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username
    } 