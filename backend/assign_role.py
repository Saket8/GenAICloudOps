from app.core.database import SessionLocal
from app.models.user import User, Role, UserRole

db = SessionLocal()
try:
    username = "souravb"
    role_name = "CLOUD_ADMIN"
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"User {username} not found")
        exit(1)
        
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        print(f"Role {role_name} not found")
        exit(1)
        
    # Check if already assigned
    existing = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).first()
    if existing:
        print(f"Role {role_name} already assigned to {username}")
    else:
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)
        db.commit()
        print(f"Successfully assigned role {role_name} to {username}")
        
finally:
    db.close()
