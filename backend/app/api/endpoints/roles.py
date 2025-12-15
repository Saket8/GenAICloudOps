from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.user import Role, User
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.get("/", response_model=List[RoleResponse])
def read_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    """
    Retrieve roles.
    """
    # Check permissions - assuming any authenticated user can view roles, 
    # or restrict to those with can_manage_roles or can_manage_users
    if not (current_user.user_roles and any(ur.role.can_manage_roles or ur.role.can_manage_users for ur in current_user.user_roles)):
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    roles = db.query(Role).offset(skip).limit(limit).all()
    return roles

@router.post("/", response_model=RoleResponse)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    """
    Create new role.
    """
    # Check permissions
    if not (current_user.user_roles and any(ur.role.can_manage_roles for ur in current_user.user_roles)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    role = db.query(Role).filter(Role.name == role_in.name).first()
    if role:
        raise HTTPException(
            status_code=400,
            detail="The role with this name already exists in the system.",
        )
        
    role = Role(**role_in.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    """
    Update a role.
    """
    if not (current_user.user_roles and any(ur.role.can_manage_roles for ur in current_user.user_roles)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )
        
    update_data = role_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)
        
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.delete("/{role_id}", response_model=RoleResponse)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    """
    Delete a role.
    """
    if not (current_user.user_roles and any(ur.role.can_manage_roles for ur in current_user.user_roles)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )
        
    # Check if role is assigned to any user?
    # For now, let cascade delete handle it or prevent it?
    # Usually better to prevent if in use.
    if role.user_roles:
         raise HTTPException(
            status_code=400,
            detail="Cannot delete role that is assigned to users.",
        )

    db.delete(role)
    db.commit()
    return role
