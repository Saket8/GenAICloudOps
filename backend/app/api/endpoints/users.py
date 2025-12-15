from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User, Role, UserRole, RoleEnum
from app.schemas.auth import UserResponse, UserCreate, UserUpdate, UserWithRoles
from app.services.auth_service import AuthService

router = APIRouter()

def check_admin_permissions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    permissions = AuthService.get_user_permissions(db, current_user)
    if not permissions.get("can_manage_users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage users"
        )
    return current_user

@router.get("/", response_model=List[UserWithRoles])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    users = db.query(User).offset(skip).limit(limit).all()
    # Populate roles for each user
    result = []
    for user in users:
        user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        roles = []
        for ur in user_roles:
            role = db.query(Role).filter(Role.id == ur.role_id).first()
            if role:
                roles.append(role)
        
        user_dict = UserWithRoles.model_validate(user)
        user_dict.roles = roles
        result.append(user_dict)
    return result

@router.post("/", response_model=UserWithRoles)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    user = AuthService.create_user(db, user_in, assign_roles=user_in.roles)
    
    # Fetch roles to return
    user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    roles = []
    for ur in user_roles:
        role = db.query(Role).filter(Role.id == ur.role_id).first()
        if role:
            roles.append(role)
            
    user_dict = UserWithRoles.model_validate(user)
    user_dict.roles = roles
    return user_dict

@router.put("/{user_id}", response_model=UserWithRoles)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
        
    if user_in.roles is not None:
        # Remove existing roles
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()
        # Add new roles
        for role_enum in user_in.roles:
            role = db.query(Role).filter(Role.name == role_enum).first()
            if role:
                db.add(UserRole(user_id=user.id, role_id=role.id))
                
    db.commit()
    db.refresh(user)
    
    # Fetch roles to return
    user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    roles = []
    for ur in user_roles:
        role = db.query(Role).filter(Role.id == ur.role_id).first()
        if role:
            roles.append(role)
            
    user_dict = UserWithRoles.model_validate(user)
    user_dict.roles = roles
    return user_dict

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete own account"
        )
        
    db.delete(user)
    db.commit()
