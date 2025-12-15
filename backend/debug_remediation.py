#!/usr/bin/env python3
"""
Debug script to test remediation generation and see what instances are being found
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.remediation_service import generate_oci_remediation_actions
from app.services.cloud_service import OCIService
from app.models.user import User

async def debug_remediation():
    """Debug remediation action generation"""
    print("🔍 DEBUG: Testing remediation generation...")
    
    try:
        # Get database session
        db = SessionLocal()
        
        # Get admin user
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("❌ Admin user not found")
            return
        
        print(f"✅ Using user: {user.username}")
        
        # Test OCI service directly first
        oci_service = OCIService()
        print(f"🌐 OCI Available: {oci_service.oci_available}")
        
        if oci_service.oci_available:
            # Get compartments
            compartments = await oci_service.get_compartments()
            print(f"📁 Found {len(compartments)} compartments")
            
            for comp in compartments:
                comp_id = comp.get('id')
                comp_name = comp.get('name', 'Unknown')
                print(f"   📂 {comp_name} ({comp_id})")
                
                # Get instances in this compartment
                instances = await oci_service.get_compute_instances(comp_id)
                print(f"      💻 {len(instances)} compute instances")
                
                for inst in instances:
                    inst_name = inst.get('display_name', 'Unknown')
                    inst_state = inst.get('lifecycle_state', 'UNKNOWN')
                    inst_id = inst.get('id', 'Unknown')
                    print(f"         🖥️  {inst_name} | State: '{inst_state}' | ID: {inst_id[:50]}...")
                    
                    if inst_state == 'STOPPED':
                        print(f"         🚨 FOUND STOPPED INSTANCE: {inst_name}")
                    elif inst_state.upper() == 'STOPPED':
                        print(f"         🚨 FOUND STOPPED INSTANCE (case mismatch): {inst_name}")
        
        # Now test the actual remediation generation
        print("\n🔧 Testing remediation generation...")
        actions = await generate_oci_remediation_actions(
            current_user=user,
            environment="production",
            db=db
        )
        
        print(f"✅ Generated {len(actions)} remediation actions")
        
        for action in actions:
            print(f"   🎯 {action.title} | Severity: {action.severity.value} | Service: {action.service_name}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_remediation()) 