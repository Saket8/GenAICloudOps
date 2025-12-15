"""
Debug script to identify the source of NoneType iteration in RBAC analysis
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def debug_rbac_data():
    """Debug the exact data being returned by kubernetes service"""
    try:
        from app.services.kubernetes_service_working import working_kubernetes_service
        
        # Configure cluster
        kubeconfig_path = r"C:\Users\2375603\.kube\config"
        if os.path.exists(kubeconfig_path):
            with open(kubeconfig_path, 'r') as f:
                kubeconfig_content = f.read()
            
            success = working_kubernetes_service.configure_cluster(
                kubeconfig_content, "debug-test"
            )
            
            if not success:
                print("Failed to configure cluster")
                return
        else:
            print("No kubeconfig found")
            return
        
        print("=== DEBUGGING RBAC DATA ===")
        
        # Test get_rbac_roles
        print("\n1. Testing get_rbac_roles...")
        try:
            roles = working_kubernetes_service.get_rbac_roles(namespace=None)
            print(f"Roles type: {type(roles)}")
            print(f"Roles value: {roles}")
            
            if roles is not None and len(roles) > 0:
                print(f"First role: {roles[0]}")
                print(f"First role type: {type(roles[0])}")
                print(f"First role name: {getattr(roles[0], 'name', 'NO NAME ATTR')}")
                print(f"First role rules: {getattr(roles[0], 'rules', 'NO RULES ATTR')}")
                if hasattr(roles[0], 'rules') and roles[0].rules:
                    print(f"First rule: {roles[0].rules[0] if len(roles[0].rules) > 0 else 'NO RULES'}")
            
        except Exception as e:
            print(f"Error in get_rbac_roles: {e}")
            import traceback
            traceback.print_exc()
        
        # Test get_rbac_bindings
        print("\n2. Testing get_rbac_bindings...")
        try:
            bindings = working_kubernetes_service.get_rbac_bindings(namespace=None)
            print(f"Bindings type: {type(bindings)}")
            print(f"Bindings count: {len(bindings) if bindings else 'None'}")
            
            if bindings is not None and len(bindings) > 0:
                print(f"First binding: {bindings[0]}")
                print(f"First binding role_ref: {getattr(bindings[0], 'role_ref', 'NO ROLE_REF')}")
                print(f"First binding subjects: {getattr(bindings[0], 'subjects', 'NO SUBJECTS')}")
            
        except Exception as e:
            print(f"Error in get_rbac_bindings: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"Overall error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rbac_data() 