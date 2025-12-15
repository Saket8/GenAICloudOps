#!/usr/bin/env python3
"""
Targeted installation script for missing GenAI-CloudOps dependencies
Only installs what's actually missing based on verification results
"""

import subprocess
import sys
import os

def run_pip_install(packages):
    """Install packages using pip"""
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Installation successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def install_missing_deps():
    """Install only the missing dependencies identified by verification"""
    
    print("🔧 Installing Missing Dependencies for GenAI-CloudOps")
    print("=" * 60)
    
    # Group installations by category for better organization
    dependency_groups = {
        "Database & Migration Tools": [
            "alembic==1.13.0",
            "psycopg2-binary==2.9.10"
        ],
        "Cloud & Resilience": [
            "tenacity==8.2.3", 
            "redis==5.0.1",
            "kubernetes==28.1.0"
        ],
        "Development & Testing": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1", 
            "python-dotenv==1.0.0"
        ]
    }
    
    total_success = True
    
    for group_name, packages in dependency_groups.items():
        print(f"\n📦 Installing {group_name}:")
        print("-" * 40)
        
        success = run_pip_install(packages)
        if success:
            print(f"✅ {group_name} installed successfully")
        else:
            print(f"❌ {group_name} installation failed")
            total_success = False
    
    return total_success

def verify_installation():
    """Quick verification that everything installed correctly"""
    print("\n🔍 Verifying Installation:")
    print("-" * 30)
    
    test_imports = [
        ("alembic", "Alembic"),
        ("psycopg2", "PostgreSQL Driver"),
        ("tenacity", "Tenacity"),
        ("redis", "Redis"),
        ("kubernetes", "Kubernetes"),
        ("pytest", "pytest"),
        ("dotenv", "python-dotenv")
    ]
    
    all_good = True
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name}")
            all_good = False
    
    return all_good

def main():
    """Main installation process"""
    print("🚀 GenAI-CloudOps Targeted Dependency Installation")
    print("This will install ONLY the missing dependencies identified during verification")
    print("=" * 80)
    
    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Error: Please run this script from the backend/ directory")
        sys.exit(1)
    
    # Install missing dependencies
    installation_success = install_missing_deps()
    
    if installation_success:
        print("\n🎉 All missing dependencies installed successfully!")
        
        # Verify installation
        verification_success = verify_installation()
        
        if verification_success:
            print("\n✅ INSTALLATION COMPLETE!")
            print("All dependencies are now properly installed and verified.")
            print("\nNext steps:")
            print("1. Update OCI config path in app/core/config.py")
            print("2. Run the verification script again: python verify_dependencies.py")
            print("3. Test the application: python main.py")
        else:
            print("\n⚠️ Some verification checks failed. Please check the output above.")
    else:
        print("\n❌ Some installations failed. Please check the errors above.")

if __name__ == "__main__":
    main() 