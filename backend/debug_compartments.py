import asyncio
import os
import sys

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cloud_service import OCIService
from app.core.config import settings

async def debug_compartments():
    print(f"DEBUG: Initializing OCIService (USE_DUMMY_OCI={settings.USE_DUMMY_OCI})...")
    header_border = "="*80
    print(header_border)
    
    try:
        oci_service = OCIService()
        
        print("\nDEBUG: Fetching compartments from OCI...")
        compartments = await oci_service.get_compartments()
        
        print(f"\nDEBUG: Retrieved {len(compartments)} compartments.\n")
        print(f"{'NAME':<40} | {'ID':<30} | {'PARENT ID'}")
        print("-" * 100)
        
        # Sort by name for easier reading
        sorted_comps = sorted(compartments, key=lambda x: x['name'])
        
        # Build a map for parent lookup
        comp_map = {c['id']: c for c in sorted_comps}
        
        for c in sorted_comps:
            name = c['name']
            c_id = c['id'][-10:] # Last 10 chars for brevity
            p_id = c.get('compartment_id')
            p_id_short = p_id[-10:] if p_id else "None"
            
            # Check if parent exists in our list
            parent_status = ""
            if p_id and p_id not in comp_map:
                 # If parent is the tenancy root, that's okay, but we should see if tenancy root is in the list
                 if p_id == settings.OCI_TENANCY_ID:
                     parent_status = " (IS TENANCY ROOT)"
                 else:
                     parent_status = " (PARENT NOT IN LIST - ORPHAN?)"
            
            print(f"{name:<40} | ...{c_id:<27} | ...{p_id_short}{parent_status}")

        print(header_border)

    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_compartments())
