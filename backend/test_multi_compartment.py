"""
Multi-compartment Resource Discovery Test
Tests all compartments to find resources of each type
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_all_compartments():
    print("=" * 70)
    print("MULTI-COMPARTMENT RESOURCE DISCOVERY TEST")
    print("=" * 70)
    
    try:
        from app.services.cloud_service import get_oci_service
        
        oci_service = get_oci_service()
        
        if not oci_service.oci_available:
            print("[ERROR] OCI not available")
            return
        
        compartments = await oci_service.get_compartments()
        print(f"\n[INFO] Testing {len(compartments)} compartments...")
        
        # Track totals across all compartments
        resource_totals = {
            "compute_instances": 0,
            "databases": 0,
            "oke_clusters": 0,
            "api_gateways": 0,
            "load_balancers": 0,
            "network_resources": 0,
            "block_volumes": 0,
            "file_systems": 0,
            "object_storage_buckets": 0,
            "vaults": 0
        }
        
        # Test up to 10 compartments for speed
        sample_size = min(10, len(compartments))
        test_compartments = compartments[:sample_size]
        
        for comp in test_compartments:
            try:
                result = await oci_service.get_all_resources(comp['id'])
                resources = result.get('resources', {})
                total = result.get('total_resources', 0)
                
                if total > 0:
                    print(f"\n[OK] {comp['name']}: {total} resources")
                    for rtype, items in resources.items():
                        count = len(items) if items else 0
                        if count > 0:
                            resource_totals[rtype] += count
                            print(f"     - {rtype}: {count}")
                else:
                    print(f"[--] {comp['name']}: 0 resources")
                    
            except Exception as e:
                print(f"[ERROR] {comp['name']}: {str(e)[:40]}")
        
        print("\n" + "=" * 70)
        print("TOTAL RESOURCES DISCOVERED (across sampled compartments)")
        print("=" * 70)
        
        grand_total = 0
        for rtype, count in resource_totals.items():
            icon = "[OK]" if count > 0 else "[--]"
            print(f"{icon} {rtype}: {count}")
            grand_total += count
        
        print(f"\n[TOTAL] {grand_total} resources across {sample_size} compartments")
        
    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_all_compartments())
