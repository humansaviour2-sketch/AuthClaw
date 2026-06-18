import socket
import urllib.request
import urllib.error
import sys
import json
import time

def check_port(host, port, service_name):
    print(f"Checking port {port} ({service_name})... ", end="")
    try:
        with socket.create_connection((host, port), timeout=3):
            print("OPEN")
            return True
    except (socket.timeout, ConnectionRefusedError):
        print("CLOSED [FAIL]")
        return False

def check_http_endpoint(url, expected_status=200):
    print(f"Checking HTTP endpoint {url}... ", end="")
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            status = response.getcode()
            if status == expected_status:
                print(f"OK ({status})")
                return True
            else:
                print(f"FAIL (Expected {expected_status}, got {status}) [FAIL]")
                return False
    except urllib.error.HTTPError as e:
        if e.code == expected_status:
            print(f"OK ({e.code})")
            return True
        else:
            print(f"FAIL (HTTP Error {e.code}) [FAIL]")
            return False
    except Exception as e:
        print(f"ERROR ({str(e)}) [FAIL]")
        return False

def main():
    print("==================================================")
    print("AuthClaw Phase 13 System Smoke Test")
    print("==================================================")
    
    host = "localhost"
    ports = [
        (8000, "FastAPI Backend"),
        (8080, "Go Gateway"),
        (3001, "Next.js Console"),
        (8123, "ClickHouse"),
        (6379, "Redis"),
    ]
    
    all_passed = True
    for port, name in ports:
        if not check_port(host, port, name):
            all_passed = False
            
    print("\nValidating HTTP Service Health...")
    
    # 1. Backend health check
    if not check_http_endpoint("http://localhost:8000/health"):
        all_passed = False
        
    # 2. Console home page loading
    if not check_http_endpoint("http://localhost:3001/login"):
        all_passed = False

    print("==================================================")
    if all_passed:
        print("SMOKE TEST PASSED: All core services are healthy! [OK]")
        sys.exit(0)
    else:
        print("SMOKE TEST FAILED: Some services or endpoints are unhealthy! [FAIL]")
        sys.exit(1)

if __name__ == "__main__":
    main()
