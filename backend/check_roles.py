from app.core.database import SessionLocal
from app.models.user import Role
import sys

# Redirect stdout to a file
sys.stdout = open('roles_output.txt', 'w')

db = SessionLocal()
roles = db.query(Role).all()

print(f"{'Role Name':<20} | {'Dashboard':<10} | {'Alerts':<10} | {'Remediation':<12} | {'Users':<10}")
print("-" * 70)

for role in roles:
    print(f"{role.name.value:<20} | {str(role.can_view_dashboard):<10} | {str(role.can_view_alerts):<10} | {str(role.can_approve_remediation):<12} | {str(role.can_manage_users):<10}")

db.close()
