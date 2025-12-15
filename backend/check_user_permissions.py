"""
Check which user is logged in and their role/permission details
"""
from app.core.database import SessionLocal
from app.models.user import User, UserRole, Role

db = SessionLocal()

try:
    # Get all users
    users = db.query(User).all()
    
    print("=" * 80)
    print("USER DETAILS AND PERMISSIONS")
    print("=" * 80)
    print()
    
    for user in users:
        print(f"User: {user.username} (ID: {user.id}, Email: {user.email})")
        print(f"  Active: {user.is_active}")
        
        # Get user's roles
        user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        print(f"  Role Assignments ({len(user_roles)}):")
        
        for user_role in user_roles:
            role = db.query(Role).filter(Role.id == user_role.role_id).first()
            if role:
                print(f"    - Role ID {role.id}: {role.name} ({role.display_name})")
                print(f"      can_view_dashboard: {role.can_view_dashboard}")
                print(f"      can_view_alerts: {role.can_view_alerts}")
                print(f"      can_manage_users: {role.can_manage_users}")
        
        print()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
