#!/usr/bin/env python3
import os
import sys
import requests
import json
from pathlib import Path

# Add project root to Python path to ensure imports work
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def check_file_exists():
    """Check if auth.py exists on the server"""
    auth_path = Path('app/routers/auth.py')
    if auth_path.exists():
        print(f"✓ Auth file exists at: {auth_path.absolute()}")
        return True
    else:
        print(f"✗ Auth file NOT found at: {auth_path.absolute()}")
        return False

def test_auth_endpoints(base_url="http://localhost:8000"):
    """Test authentication endpoints"""
    endpoints = [
        {"url": f"{base_url}/api/auth/login", "method": "POST"},
        {"url": f"{base_url}/health", "method": "GET"},
    ]
    
    results = []
    
    for endpoint in endpoints:
        url = endpoint["url"]
        method = endpoint["method"]
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                # Just testing connection, not actual login
                response = requests.post(url, json={"username": "test", "password": "test"}, timeout=5)
            
            status = response.status_code
            success = 200 <= status < 500  # Any response that's not a server error
            
            results.append({
                "endpoint": url,
                "status": status,
                "success": success,
                "response": response.json() if success else str(response.content)
            })
            
            print(f"{'✓' if success else '✗'} {method} {url}: {status}")
            
        except Exception as e:
            results.append({
                "endpoint": url,
                "status": "Error",
                "success": False,
                "response": str(e)
            })
            print(f"✗ {method} {url}: Error - {str(e)}")
    
    return results

def main():
    print("\n--- Testing Introgy Authentication System ---\n")
    
    # Check if we're on the production server
    is_production = os.getenv("ENVIRONMENT") == "production"
    print(f"Environment: {'Production' if is_production else 'Development'}")
    
    # Check if auth.py exists
    file_exists = check_file_exists()
    
    if not file_exists:
        print("\nCannot find auth.py. Please verify deployment.")
        return
    
    # Get server URL
    server_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    print(f"\nTesting server at: {server_url}\n")
    
    # Test authentication endpoints
    results = test_auth_endpoints(server_url)
    
    # Summary
    successes = sum(1 for r in results if r["success"])
    print(f"\nResults: {successes}/{len(results)} endpoints reachable")
    
    if successes == len(results):
        print("\n✓ Auth system is properly deployed and responding")
    else:
        print("\n✗ Some auth endpoints failed - check server logs for details")

if __name__ == "__main__":
    main() 