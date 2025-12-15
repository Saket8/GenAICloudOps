#!/usr/bin/env python3
"""
Create default admin user for GenAI CloudOps Dashboard
"""
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db, engine, Base
from app.models.user import User, Role, UserRole
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
from sqlalchemy import text

def create_admin_user():
    """Create the default admin user"""
    print("🔧 Creating default admin user...")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if admin role exists
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            print("❌ Admin role not found. Creating roles first...")
            
            # Create admin role
            admin_role = Role(
                name="admin",
                display_name="Administrator",
                description="Full system access with all permissions",
                can_view_dashboard=True,
                can_view_alerts=True,
                can_approve_remediation=True,
                can_execute_remediation=True,
                can_manage_users=True,
                can_manage_roles=True,
                can_view_access_analyzer=True,
                can_view_pod_analyzer=True,
                can_view_cost_analyzer=True,
                can_use_chatbot=True
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print("✅ Admin role created")
        
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("⚠️  Admin user already exists. Updating password...")
            existing_admin.hashed_password = get_password_hash("AdminPass123!")
            existing_admin.is_active = True
            existing_admin.is_verified = True
            db.commit()
            print("✅ Admin user password updated")
        else:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@genai-cloudops.com",
                full_name="System Administrator",
                hashed_password=get_password_hash("AdminPass123!"),
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("✅ Admin user created")
            
            # Assign admin role to admin user
            user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db.add(user_role)
            db.commit()
            print("✅ Admin role assigned to admin user")
        
        # Verify the setup
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            roles = db.query(Role).join(UserRole).filter(UserRole.user_id == admin_user.id).all()
            print(f"\n📊 Admin User Details:")
            print(f"   Username: {admin_user.username}")
            print(f"   Email: {admin_user.email}")
            print(f"   Full Name: {admin_user.full_name}")
            print(f"   Active: {admin_user.is_active}")
            print(f"   Verified: {admin_user.is_verified}")
            print(f"   Roles: {[role.name for role in roles]}")
            
            print(f"\n🔑 Login Credentials:")
            print(f"   Username: admin")
            print(f"   Password: AdminPass123!")
            
        print("\n✅ Admin user setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user() 