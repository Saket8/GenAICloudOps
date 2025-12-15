"""
Test all compartments for file systems specifically
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_file_systems():
    print("=" * 60)
    print("FILE SYSTEMS DISCOVERY TEST")
    print("=" * 60)
    
    try:
        from app.services.cloud_service import get_oci_service
        
        oci_service = get_oci_service()
        
        if not oci_service.oci_available:
            print("[ERROR] OCI not available")
            return
        
        compartments = await oci_service.get_compartments()
        print(f"\n[INFO] Checking all {len(compartments)} compartments for file systems...")
        
        total_fs = 0
        
        for comp in compartments:
            try:
                file_systems = await oci_service.get_file_systems(comp['id'])
                count = len(file_systems) if file_systems else 0
                if count > 0:
                    total_fs += count
                    print(f"\n[OK] {comp['name']}: {count} file systems")
                    for fs in file_systems:
                        print(f"     - {fs.get('display_name', 'N/A')}")
            except Exception as e:
                print(f"[ERROR] {comp['name']}: {str(e)[:50]}")
        
        print(f"\n[TOTAL] {total_fs} file systems found across all compartments")
        
        if total_fs == 0:
            print("\n[INFO] No file systems found. This might be because:")
            print("       1. No file systems exist in this tenancy")
            print("       2. The file systems are in a different region")
            print("       3. IAM policy doesn't allow access")
        
    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_file_systems())
