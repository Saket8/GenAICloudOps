#!/usr/bin/env python3
"""
Database initialization script for GenAI CloudOps
This script creates the database tables and initializes default data including a default admin user.
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import create_tables, init_default_roles
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate
from app.models.user import RoleEnum
from app.core.database import SessionLocal

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        from app.models.user import User
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if admin_user:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin_data = UserCreate(
            username="admin",
            email="admin@example.com",
            password="AdminPass123!",  # Change this in production!
            full_name="System Administrator"
        )
        
        user = AuthService.create_user(
            db, 
            admin_data, 
            assign_roles=[RoleEnum.ADMIN]
        )
        
        print(f"Created admin user: {user.username} (ID: {user.id})")
        print("Default admin credentials:")
        print("  Username: admin")
        print("  Password: AdminPass123!")
        print("  ⚠️  CHANGE THE DEFAULT PASSWORD IMMEDIATELY!")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def create_demo_users():
    """Create demo users for testing"""
    db = SessionLocal()
    try:
        demo_users = [
            {
                "data": UserCreate(
                    username="operator",
                    email="operator@example.com",
                    password="OperatorPass123!",
                    full_name="Demo Operator"
                ),
                "roles": [RoleEnum.OPERATOR]
            },
            {
                "data": UserCreate(
                    username="viewer",
                    email="viewer@example.com",
                    password="ViewerPass123!",
                    full_name="Demo Viewer"
                ),
                "roles": [RoleEnum.VIEWER]
            }
        ]
        
        for user_config in demo_users:
            # Check if user already exists
            from app.models.user import User
            existing_user = db.query(User).filter(User.username == user_config["data"].username).first()
            
            if existing_user:
                print(f"User {user_config['data'].username} already exists")
                continue
            
            user = AuthService.create_user(
                db, 
                user_config["data"], 
                assign_roles=user_config["roles"]
            )
            
            print(f"Created demo user: {user.username} (Role: {user_config['roles'][0].value})")
    
    except Exception as e:
        print(f"Error creating demo users: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("🚀 Initializing GenAI CloudOps Database...")
    
    try:
        # Create tables
        print("📋 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully")
        
        # Initialize default roles
        print("👥 Initializing default roles...")
        init_default_roles()
        print("✅ Default roles initialized successfully")
        
        # Create admin user
        print("👤 Creating admin user...")
        create_admin_user()
        print("✅ Admin user created successfully")
        
        # Create demo users
        print("🎭 Creating demo users...")
        create_demo_users()
        print("✅ Demo users created successfully")
        
        print("\n🎉 Database initialization completed!")
        print("\n📝 Next steps:")
        print("1. Install frontend dependencies: cd frontend && npm install")
        print("2. Start the backend: python main.py")
        print("3. Start the frontend: cd frontend && npm run dev")
        print("4. Access the application at http://localhost:5173")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 