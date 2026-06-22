import requests
import json
import sys

def main():
    print("Testing AuthClaw Gateway connection...")
    
    # 1. Health check
    try:
        r = requests.get("http://localhost:8080/health", timeout=3)
        print(f"Health check status: {r.status_code}")
        print(f"Health check body: {r.text}")
    except Exception as e:
        print(f"Health check failed: {e}")
        
if __name__ == "__main__":
    main()
