import requests

BASE_URL = "http://localhost:8000"

def check_endpoints():
    """Check which endpoints are available"""
    print("🔍 CHECKING AVAILABLE ENDPOINTS")
    print("=" * 40)
    
    endpoints_to_test = [
        "/api/v1/",
        "/api/v1/health",
        "/api/v1/kubernetes/health",
        "/api/v1/k8s/health",
        "/docs"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"✅ {endpoint}: {response.status_code}")
            if endpoint == "/api/v1/" and response.status_code == 200:
                data = response.json()
                endpoints = data.get("endpoints", {})
                print(f"   Available endpoints: {list(endpoints.keys())}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

if __name__ == "__main__":
    check_endpoints() 