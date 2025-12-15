#!/usr/bin/env python3
"""
Comprehensive dependency verification script for GenAI-CloudOps project
Tests all imports and dependencies from tasks 1-7
"""

import sys
import importlib
from typing import Dict, List, Tuple

def test_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """Test if a module can be imported"""
    try:
        if package_name:
            module = importlib.import_module(module_name, package_name)
        else:
            module = importlib.import_module(module_name)
        
        # Try to get version if available
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError as e:
        return False, str(e)

def check_core_dependencies():
    """Check core web framework dependencies"""
    print("🔍 Testing Core Web Framework Dependencies:")
    
    dependencies = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('pydantic_settings', 'Pydantic Settings'),
        ('starlette', 'Starlette'),
    ]
    
    for module, name in dependencies:
        success, result = test_import(module)
        if success:
            print(f"  ✅ {name}: {result}")
        else:
            print(f"  ❌ {name}: {result}")

def check_database_dependencies():
    """Check database and ORM dependencies"""
    print("\n🗄️ Testing Database Dependencies:")
    
    dependencies = [
        ('sqlalchemy', 'SQLAlchemy'),
        ('alembic', 'Alembic'),
        ('psycopg2', 'PostgreSQL Driver'),
    ]
    
    for module, name in dependencies:
        success, result = test_import(module)
        if success:
            print(f"  ✅ {name}: {result}")
        else:
            print(f"  ❌ {name}: {result}")

def check_auth_dependencies():
    """Check authentication and security dependencies"""
    print("\n🔐 Testing Authentication Dependencies:")
    
    dependencies = [
        ('jose', 'Python JOSE'),
        ('passlib', 'Passlib'),
        ('bcrypt', 'bcrypt'),
        ('cryptography', 'Cryptography'),
    ]
    
    for module, name in dependencies:
        success, result = test_import(module)
        if success:
            print(f"  ✅ {name}: {result}")
        else:
            print(f"  ❌ {name}: {result}")

def check_cloud_dependencies():
    """Check OCI SDK and cloud dependencies"""
    print("\n☁️ Testing Cloud Dependencies:")
    
    dependencies = [
        ('oci', 'OCI SDK'),
        ('tenacity', 'Tenacity'),
        ('redis', 'Redis'),
        ('kubernetes', 'Kubernetes'),
        ('psutil', 'psutil'),
    ]
    
    for module, name in dependencies:
        success, result = test_import(module)
        if success:
            print(f"  ✅ {name}: {result}")
        else:
            print(f"  ❌ {name}: {result}")

def check_utility_dependencies():
    """Check utility and development dependencies"""
    print("\n🛠️ Testing Utility Dependencies:")
    
    dependencies = [
        ('httpx', 'HTTPX'),
        ('pytest', 'pytest'),
        ('python_multipart', 'Python Multipart'),
        ('python_dotenv', 'Python Dotenv'),
    ]
    
    for module, name in dependencies:
        success, result = test_import(module)
        if success:
            print(f"  ✅ {name}: {result}")
        else:
            print(f"  ❌ {name}: {result}")

def test_project_imports():
    """Test actual project imports from the codebase"""
    print("\n🏗️ Testing Project-Specific Imports:")
    
    # Add the current directory to Python path
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    project_imports = [
        ('app.core.config', 'Configuration Module'),
        ('app.core.database', 'Database Module'),
        ('app.core.security', 'Security Module'),
        ('app.models.user', 'User Models'),
        ('app.services.auth_service', 'Auth Service'),
        ('app.services.cloud_service', 'Cloud Service'),
        ('app.services.monitoring_service', 'Monitoring Service'),
        ('app.api.routes', 'API Routes'),
    ]
    
    for module, name in project_imports:
        success, result = test_import(module)
        if success:
            print(f"  ✅ {name}: Import successful")
        else:
            print(f"  ❌ {name}: {result}")

def main():
    """Run all dependency checks"""
    print("🔬 GenAI-CloudOps Dependency Verification")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print("=" * 50)
    
    check_core_dependencies()
    check_database_dependencies()
    check_auth_dependencies()
    check_cloud_dependencies()
    check_utility_dependencies()
    test_project_imports()
    
    print("\n" + "=" * 50)
    print("✅ Verification complete!")
    print("Any ❌ entries indicate missing dependencies that need installation.")

if __name__ == "__main__":
    main() 