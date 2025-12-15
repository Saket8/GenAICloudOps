"""
Script to update existing role permissions in the database.
This ensures all roles have the correct permissions as defined in database.py.
"""
from app.core.database import init_default_roles

print("=" * 60)
print("Updating Role Permissions in Database")
print("=" * 60)
print()

init_default_roles()

print()
print("=" * 60)
print("Role permissions update complete!")
print("=" * 60)
