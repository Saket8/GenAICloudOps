"""
Fix the PermissionChecker __call__ method to check actual permission flags
"""
import re

# Read the file
with open('app/core/permissions.py', 'r') as f:
    content = f.read()

# Find and replace the __call__ method in PermissionChecker
old_method = r'''    def __call__\(self, 
                 current_user: User = Depends\(AuthService\.get_current_user\)\) -> User:
        """Check if user has required permissions"""
        # Note: We simplified this to not expose Session in the function signature
        # Permission checking can be done based on user roles directly
        
        # Check if user has required role permissions  
        # Get user roles from database relationship
        from app\.core\.database import SessionLocal
        db = SessionLocal\(\)
        try:
            from app\.models\.user import UserRole, Role
            user_roles_records = db\.query\(UserRole\)\.filter\(UserRole\.user_id == current_user\.id\)\.all\(\)
            user_roles = \[]
            for user_role in user_roles_records:
                role = db\.query\(Role\)\.filter\(Role\.id == user_role\.role_id\)\.first\(\)
                if role:
                    user_roles\.append\(role\.name\.value\)
        finally:
            db\.close\(\)
        
        # Map permissions to roles
        permission_role_map = {
            "viewer": \["viewer", "operator", "admin"\],
            "operator": \["operator", "admin"\], 
            "admin": \["admin"\]
        }
        
        for permission in self\.required_permissions:
            allowed_roles = permission_role_map\.get\(permission, \[]\)
            if not any\(role in user_roles for role in allowed_roles\):
                raise HTTPException\(
                    status_code=status\.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions\. Required: {permission}"
                \)
        
        return current_user'''

new_method = '''    def __call__(self, 
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
                        aggregated_permissions[perm_field] = aggregated_permissions.get(perm_field, False) | getattr(role, perm_field, False)
        finally:
            db.close()
        
        # Check if user has all required permissions
        for permission in self.required_permissions:
            if not aggregated_permissions.get(permission, False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission}"
                )
        
        return current_user'''

# Try simpler approach - just replace the logic inside the method
# Find start and end of the __call__ method
start_marker = "    def __call__(self"
end_marker = "        return current_user\n\nclass Role"

start_idx = content.find(start_marker)
if start_idx == -1:
    print("ERROR: Could not find __call__ method start")
    exit(1)

# Find the end - look for the return statement before RoleChecker class
end_search_start = start_idx
end_idx = content.find("class RoleChecker:", end_search_start)
if end_idx == -1:
    print("ERROR: Could not find RoleChecker class")
    exit(1)

# Find the last "return current_user" before RoleChecker
snippet_before_role_checker = content[start_idx:end_idx]
last_return_idx = snippet_before_role_checker.rfind("        return current_user")
if last_return_idx == -1:
    print("ERROR: Could not find return statement")
    exit(1)

actual_end_idx = start_idx + last_return_idx + len("        return current_user\n")

# Replace the method
new_content = content[:start_idx] + new_method + "\n\n" + content[end_idx:]

# Write back
with open('app/core/permissions.py', 'w') as f:
    f.write(new_content)

print("✅ Successfully updated PermissionChecker.__call__ method")
