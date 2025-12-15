#!/usr/bin/env python3
"""
Script to clean up test/mock remediation data from the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, create_tables
from app.models.remediation import RemediationAction, RemediationAuditLog
from sqlalchemy import or_

def cleanup_test_data():
    """Clean up test/mock remediation data"""
    print("🧹 Cleaning up test remediation data...")
    
    try:
        # Create database session
        db = SessionLocal()
        
        # Test patterns to identify mock data
        test_patterns = [
            "Test OCI Instance Restart",
            "test",
            "mock",
            "demo",
            "ocid1.instance.test"
        ]
        
        deleted_count = 0
        
        for pattern in test_patterns:
            # Find actions matching test patterns
            test_actions = db.query(RemediationAction).filter(
                or_(
                    RemediationAction.title.ilike(f"%{pattern}%"),
                    RemediationAction.action_command.ilike(f"%{pattern}%"),
                    RemediationAction.service_name.ilike(f"%{pattern}%")
                )
            ).all()
            
            for action in test_actions:
                print(f"  🗑️  Deleting: {action.title} (ID: {action.id})")
                
                # Delete associated audit logs first
                audit_logs_deleted = db.query(RemediationAuditLog).filter(
                    RemediationAuditLog.action_id == action.id
                ).delete()
                
                if audit_logs_deleted > 0:
                    print(f"    📝 Deleted {audit_logs_deleted} audit logs")
                
                # Delete the action
                db.delete(action)
                deleted_count += 1
        
        # Commit changes
        db.commit()
        
        print(f"✅ Successfully cleaned up {deleted_count} test remediation actions")
        
        # Show remaining actions
        remaining = db.query(RemediationAction).count()
        print(f"📊 {remaining} remediation actions remaining in database")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Failed to cleanup test data: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False
    
    return True

if __name__ == "__main__":
    success = cleanup_test_data()
    sys.exit(0 if success else 1) 