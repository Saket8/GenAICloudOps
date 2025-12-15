#!/usr/bin/env python3
"""
Debug script to check what routes are actually registered in the FastAPI app
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def debug_routes():
    """Debug what routes are registered"""
    print("🔍 DEBUGGING FASTAPI ROUTE REGISTRATION")
    print("=" * 60)
    
    try:
        # Import the main app
        from main import app
        
        print(f"✅ Main app imported: {app}")
        print(f"✅ App routes count: {len(app.routes)}")
        
        print("\n📋 All registered routes:")
        for i, route in enumerate(app.routes):
            if hasattr(route, 'path'):
                print(f"   {i+1:2d}. {route.path}")
                if hasattr(route, 'methods'):
                    print(f"       Methods: {route.methods}")
        
        # Check if /k8s routes are present
        k8s_routes = [route for route in app.routes if hasattr(route, 'path') and '/k8s' in route.path]
        print(f"\n🔍 /k8s routes found: {len(k8s_routes)}")
        for route in k8s_routes:
            print(f"   - {route.path}")
        
        # Check API router specifically
        print(f"\n🔍 Checking API router...")
        from app.api.routes import api_router
        print(f"✅ API router imported: {api_router}")
        print(f"✅ API router routes count: {len(api_router.routes)}")
        
        print("\n📋 API router routes:")
        for i, route in enumerate(api_router.routes):
            if hasattr(route, 'path'):
                print(f"   {i+1:2d}. {route.path}")
        
        # Check if /k8s routes are in API router
        api_k8s_routes = [route for route in api_router.routes if hasattr(route, 'path') and '/k8s' in route.path]
        print(f"\n🔍 /k8s routes in API router: {len(api_k8s_routes)}")
        for route in api_k8s_routes:
            print(f"   - {route.path}")
        
        # Check kubernetes_working module
        print(f"\n🔍 Checking kubernetes_working module...")
        from app.api.endpoints import kubernetes_working
        print(f"✅ kubernetes_working imported: {kubernetes_working}")
        print(f"✅ kubernetes_working router: {kubernetes_working.router}")
        print(f"✅ kubernetes_working routes count: {len(kubernetes_working.router.routes)}")
        
        print("\n📋 kubernetes_working routes:")
        for i, route in enumerate(kubernetes_working.router.routes):
            if hasattr(route, 'path'):
                print(f"   {i+1:2d}. {route.path}")
                if hasattr(route, 'methods'):
                    print(f"       Methods: {route.methods}")
        
        return True
        
    except Exception as e:
        print(f"❌ Route debugging failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_import_chain():
    """Check the import chain to see where it might be failing"""
    print(f"\n🔗 CHECKING IMPORT CHAIN")
    print("=" * 60)
    
    try:
        print("1. Importing kubernetes_working...")
        from app.api.endpoints import kubernetes_working
        print(f"   ✅ Success: {kubernetes_working}")
        
        print("2. Checking router in kubernetes_working...")
        router = kubernetes_working.router
        print(f"   ✅ Router: {router}")
        print(f"   ✅ Routes: {len(router.routes)}")
        
        print("3. Importing api routes...")
        from app.api.routes import api_router
        print(f"   ✅ API Router: {api_router}")
        
        print("4. Checking if kubernetes_working is in routes.py...")
        import app.api.routes as routes_module
        import inspect
        source = inspect.getsource(routes_module)
        if 'kubernetes_working' in source:
            print("   ✅ kubernetes_working found in routes.py source")
        else:
            print("   ❌ kubernetes_working NOT found in routes.py source")
        
        print("5. Importing main app...")
        from main import app
        print(f"   ✅ Main app: {app}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import chain check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🐛 FASTAPI ROUTE REGISTRATION DEBUG")
    print("=" * 70)
    
    # Check import chain first
    import_success = check_import_chain()
    
    if import_success:
        # Debug actual routes
        debug_success = debug_routes()
        
        if debug_success:
            print(f"\n✅ DEBUG COMPLETE")
            print("The route registration issue should be identified above")
        else:
            print(f"\n❌ Route debugging failed")
    else:
        print(f"\n❌ Import chain check failed")

if __name__ == "__main__":
    main() 