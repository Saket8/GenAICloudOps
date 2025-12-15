#!/usr/bin/env python3
"""
Force reload test to clear module cache
"""

import sys
import importlib
import requests

def force_reload_modules():
    """Force reload of our modules"""
    print("🔄 FORCING MODULE RELOAD")
    print("=" * 40)
    
    # Clear modules from cache
    modules_to_clear = [
        'app.api.routes',
        'app.api.endpoints.kubernetes_working',
        'app.api.endpoints',
    ]
    
    for module_name in modules_to_clear:
        if module_name in sys.modules:
            print(f"   Clearing {module_name} from cache")
            del sys.modules[module_name]
    
    # Reimport and check
    try:
        from app.api import routes
        importlib.reload(routes)
        print(f"   ✅ Routes reloaded: {len(routes.api_router.routes)} routes")
        
        # Check k8s routes
        route_paths = [route.path for route in routes.api_router.routes if hasattr(route, 'path')]
        k8s_routes = [path for path in route_paths if '/k8s' in path]
        print(f"   ✅ k8s routes found: {len(k8s_routes)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Reload failed: {e}")
        return False

def test_endpoint_after_reload():
    """Test endpoint after forced reload"""
    print(f"\n🌐 TESTING AFTER RELOAD")
    print("=" * 40)
    
    try:
        # Test k8s health
        response = requests.get("http://localhost:8000/api/v1/k8s/health", timeout=5)
        print(f"✅ /k8s/health: {response.status_code}")
        
        # Test API root for k8s
        response = requests.get("http://localhost:8000/api/v1/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            endpoints = data.get("endpoints", {})
            if 'k8s' in endpoints:
                print("✅ k8s found in API root response")
            else:
                print("❌ k8s still NOT in API root response")
                print(f"   Available: {list(endpoints.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    print("🔧 FORCE MODULE RELOAD AND TEST")
    print("=" * 50)
    
    # Add backend to path
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    
    reload_success = force_reload_modules()
    test_success = test_endpoint_after_reload()
    
    if reload_success and test_success:
        print(f"\n💡 SOLUTION:")
        print("The module reload should have cleared the cache.")
        print("If endpoints still don't work, the server itself needs restart.")
    else:
        print(f"\n💡 DIAGNOSIS:")
        print("Module reload or test failed - server restart required.")

if __name__ == "__main__":
    main() 