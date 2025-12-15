from app.core.database import SessionLocal
from app.models.user import Role

db = SessionLocal()
try:
    roles = db.query(Role).all()
    print(f"{'ID':<5} | {'Name':<20} | {'Display Name':<30}")
    print("-" * 60)
    for role in roles:
        print(f"{role.id:<5} | {role.name:<20} | {role.display_name:<30}")
finally:
    db.close()
