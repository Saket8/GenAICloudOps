import asyncio
import os
import sys

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cloud_service import OCIService
from app.core.config import settings

# Sample compartment ID from previous debug output (cmp-oe-brm-p)
# Replace this with a valid specific compartment ID if needed, 
# or use the root tenancy ID if that's safer.
TEST_COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaam4qoruy3ea" # cmp-oe-brm-p (partial ID guessed from debug output)
# ACTUALLY, I shouldn't guess. I'll fetch compartments first and pick one.

async def debug_resources():
    print(f"DEBUG: Initializing OCIService (USE_DUMMY_OCI={settings.USE_DUMMY_OCI})...")
    
    try:
        oci_service = OCIService()
        
        print("\nDEBUG: Fetching compartments to pick a valid one...")
        compartments = await oci_service.get_compartments()
        
        if not compartments:
            print("ERROR: No compartments found. Cannot continue.")
            return

        # Pick one that likely has resources (e.g. not root, but maybe 'cmp-oe-brm-p')
        target_comp = next((c for c in compartments if 'brm' in c['name'] and 'root' not in c['name'].lower()), compartments[0])
        comp_id = target_comp['id']
        comp_name = target_comp['name']
        
        print(f"\nDEBUG: Selected Compartment: {comp_name} ({comp_id})")
        print("="*60)

        # Test Compute Instances
        print(f"\n[1] Fetching Compute Instances for {comp_name}...")
        try:
            instances = await oci_service.get_compute_instances(comp_id)
            print(f"[OK] Success: Retrieved {len(instances)} instances.")
        except Exception as e:
            print(f"[FAILED] Failed: {e}")

        # Test Databases
        print(f"\n[2] Fetching Databases for {comp_name}...")
        try:
            dbs = await oci_service.get_databases(comp_id)
            print(f"[OK] Success: Retrieved {len(dbs)} databases.")
        except Exception as e:
            print(f"[FAILED] Failed: {e}")

        # Test OKE Clusters
        print(f"\n[3] Fetching OKE Clusters for {comp_name}...")
        try:
            clusters = await oci_service.get_oke_clusters(comp_id)
            print(f"[OK] Success: Retrieved {len(clusters)} clusters.")
        except Exception as e:
            print(f"[FAILED] Failed: {e}")
            
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_resources())
