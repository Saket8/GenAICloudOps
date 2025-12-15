"""
Backend Resource Discovery Verification Script
Tests all resource discovery methods directly against the OCIService
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def verify_resource_discovery():
    print("=" * 60)
    print("BACKEND RESOURCE DISCOVERY VERIFICATION")
    print("=" * 60)
    
    try:
        from app.services.cloud_service import get_oci_service
        
        oci_service = get_oci_service()
        print(f"\n[OK] OCI Service initialized")
        print(f"     OCI Available: {oci_service.oci_available}")
        
        if not oci_service.oci_available:
            print("\n[ERROR] OCI is not available - cannot proceed with verification")
            return
        
        # Get compartments
        print("\n[INFO] Fetching compartments...")
        compartments = await oci_service.get_compartments()
        print(f"       Found {len(compartments)} compartments")
        
        # Select first non-tenancy compartment for testing
        test_compartment = None
        for comp in compartments:
            if 'tenancy' not in comp['id']:
                test_compartment = comp
                break
        
        if not test_compartment:
            test_compartment = compartments[0] if compartments else None
        
        if not test_compartment:
            print("\n[ERROR] No compartments available for testing")
            return
        
        print(f"\n[TEST] Testing resource discovery in compartment: {test_compartment['name']}")
        comp_id = test_compartment['id']
        
        # Test each resource type
        resource_methods = [
            ("Compute Instances", oci_service.get_compute_instances),
            ("Databases", oci_service.get_databases),
            ("OKE Clusters", oci_service.get_oke_clusters),
            ("API Gateways", oci_service.get_api_gateways),
            ("Load Balancers", oci_service.get_load_balancers),
            ("Network Resources", oci_service.get_network_resources),
            ("Block Volumes", oci_service.get_block_volumes),
            ("File Systems", oci_service.get_file_systems),
            ("Object Storage Buckets", oci_service.get_object_storage_buckets),
            ("Vaults", oci_service.get_vaults),
        ]
        
        results = {}
        print("\n" + "-" * 60)
        print("RESOURCE DISCOVERY RESULTS")
        print("-" * 60)
        
        for name, method in resource_methods:
            try:
                resources = await method(comp_id)
                count = len(resources) if resources else 0
                results[name] = {"status": "OK", "count": count}
                status_icon = "[OK]" if count > 0 else "[WARN]"
                print(f"{status_icon} {name}: {count} resources found")
                
                # Show first resource as sample
                if resources and count > 0:
                    first = resources[0]
                    display_name = first.get('display_name', first.get('name', 'N/A'))
                    print(f"        Sample: {display_name[:50]}...")
                    
            except Exception as e:
                results[name] = {"status": "ERROR", "error": str(e)}
                print(f"[ERROR] {name}: {str(e)[:60]}...")
        
        # Test aggregate method
        print("\n" + "-" * 60)
        print("AGGREGATE RESOURCE DISCOVERY TEST")
        print("-" * 60)
        
        try:
            all_resources = await oci_service.get_all_resources(comp_id)
            total = all_resources.get('total_resources', 0)
            resource_breakdown = all_resources.get('resources', {})
            
            print(f"\n[OK] get_all_resources() returned {total} total resources")
            print("\nBreakdown by type:")
            for rtype, items in resource_breakdown.items():
                count = len(items) if items else 0
                icon = "[OK]" if count > 0 else "[WARN]"
                print(f"   {icon} {rtype}: {count}")
                
        except Exception as e:
            print(f"\n[ERROR] get_all_resources() failed: {e}")
        
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)
        
        # Summary
        errors = [name for name, res in results.items() if res["status"] == "ERROR"]
        if errors:
            print(f"\n[WARN] Errors in: {', '.join(errors)}")
        else:
            print("\n[OK] All resource discovery methods executed without errors")
            
    except Exception as e:
        print(f"\n[FATAL] Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_resource_discovery())
