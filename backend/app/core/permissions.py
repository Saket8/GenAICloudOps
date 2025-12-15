from typing import List
from fastapi import HTTPException, status, Depends
from app.services.auth_service import AuthService
from app.models.user import User, RoleEnum

class PermissionChecker:
    """Permission checker class for role-based access control"""
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    def __call__(self, 
                 current_user: User = Depends(AuthService.get_current_user)) -> User:
        """Check if user has required permissions"""
        # Get user roles from database and aggregate permissions
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            from app.models.user import UserRole, Role
            user_roles_records = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
            
            # Aggregate permissions from all roles (OR operation)
            aggregated_permissions = {}
            for user_role in user_roles_records:
                role = db.query(Role).filter(Role.id == user_role.role_id).first()
                if role:
                    # Aggregate all permission flags
                    for perm_field in ["can_view_dashboard", "can_view_alerts", "can_approve_remediation",
                                       "can_execute_remediation", "can_manage_users", "can_manage_roles",
                                       "can_view_access_analyzer", "can_view_pod_analyzer", 
                                       "can_view_cost_analyzer", "can_use_chatbot"]:
                        current_value = aggregated_permissions.get(perm_field, False)
                        role_value = getattr(role, perm_field, False)
                        aggregated_permissions[perm_field] = current_value or role_value
        finally:
            db.close()
        
        # Check if user has all required permissions
        for permission in self.required_permissions:
            if not aggregated_permissions.get(permission, False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission}"
                )
        
        return current_user

class RoleChecker:
    """Role checker class for role-based access control"""
    
    def __init__(self, required_roles: List[RoleEnum]):
        self.required_roles = required_roles
    
    def __call__(self, 
                 current_user: User = Depends(AuthService.get_current_user)) -> User:
        """Check if user has required roles"""
        if current_user.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role privileges. Required one of: {[role.value for role in self.required_roles]}"
            )
        return current_user

def require_permissions(*permissions: str):
    """Decorator to require specific permissions"""
    return PermissionChecker(list(permissions))

def require_roles(*roles: RoleEnum):
    """Decorator to require specific roles"""
    return RoleChecker(list(roles))

RequireAdminRole = RoleChecker([RoleEnum.ADMIN])
RequireOperatorRole = RoleChecker([RoleEnum.ADMIN, RoleEnum.OPERATOR])
RequireAnyRole = RoleChecker([RoleEnum.ADMIN, RoleEnum.OPERATOR, RoleEnum.VIEWER])
RequireDashboardAccess = PermissionChecker(["can_view_dashboard"])
RequireAlertsAccess = PermissionChecker(["can_view_alerts"])
RequireRemediationApproval = PermissionChecker(["can_approve_remediation"])
RequireRemediationExecution = PermissionChecker(["can_execute_remediation"])
RequireUserManagement = PermissionChecker(["can_manage_users"])
RequireRoleManagement = PermissionChecker(["can_manage_roles"])
RequireAccessAnalyzer = PermissionChecker(["can_view_access_analyzer"])
RequirePodAnalyzer = PermissionChecker(["can_view_pod_analyzer"])
RequireCostAnalyzer = PermissionChecker(["can_view_cost_analyzer"])
RequireChatbotAccess = PermissionChecker(["can_use_chatbot"])

def check_user_permissions(user: User, **permissions):
    """Check if user has required permissions (direct function call)"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        from app.models.user import UserRole, Role
        user_roles_records = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        
        # Aggregate permissions from all roles
        aggregated_permissions = {}
        for user_role in user_roles_records:
            role = db.query(Role).filter(Role.id == user_role.role_id).first()
            if role:
                for perm_field in ["can_view_dashboard", "can_view_alerts", "can_approve_remediation",
                                   "can_execute_remediation", "can_manage_users", "can_manage_roles",
                                   "can_view_access_analyzer", "can_view_pod_analyzer", 
                                   "can_view_cost_analyzer", "can_use_chatbot"]:
                    current_value = aggregated_permissions.get(perm_field, False)
                    role_value = getattr(role, perm_field, False)
                    aggregated_permissions[perm_field] = current_value or role_value
    finally:
        db.close()
    
    # Check each required permission
    for perm_name, required in permissions.items():
        if required and not aggregated_permissions.get(perm_name, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {perm_name}"
            )
