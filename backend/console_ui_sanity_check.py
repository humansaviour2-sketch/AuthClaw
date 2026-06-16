import requests
import sys
import json

BASE_URL = "http://localhost:3001"

def run_sanity_check():
    print("Starting Phase 11 UI & App Shell Sanity Check...\n")
    session = requests.Session()

    # 1. Verify Login Page renders correctly
    print("1. Verifying login page rendering...")
    r = session.get(f"{BASE_URL}/login")
    if r.status_code == 200 and "AuthClaw Console" in r.text and "Email Address" in r.text:
        print("   [PASS] Login page HTML rendered successfully.")
    else:
        print("   [FAIL] Login page did not render expected content.")
        sys.exit(1)

    # 2. Verify Invalid API Key shows error
    print("2. Verifying invalid API key login rejection...")
    r = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@example.com",
        "apiKey": "invalid_key_value"
    })
    if r.status_code == 401 and "Invalid or expired API Key" in r.text:
        print("   [PASS] Invalid login rejected correctly with 401 and error message.")
    else:
        print(f"   [FAIL] Expected 401 rejection, got {r.status_code}: {r.text}")
        sys.exit(1)

    # 3. Verify Valid login redirects to Overview
    print("3. Verifying valid login credentials...")
    r = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@authclaw.com",
        "apiKey": "manual_verif_key_123"
    })
    if r.status_code == 200:
        data = r.json()
        if data.get("success") and "authclaw_session" in session.cookies:
            print("   [PASS] Valid login authenticated successfully and session cookie is set.")
        else:
            print("   [FAIL] Cookie or success flag missing on success response.")
            sys.exit(1)
    else:
        print(f"   [FAIL] Valid login failed with status {r.status_code}: {r.text}")
        sys.exit(1)

    # 4. Verify Sidebar Navigation & Overview Page
    print("4. Verifying Overview page & Sidebar navigation metadata...")
    r = session.get(f"{BASE_URL}/overview", allow_redirects=False)
    if r.status_code == 200:
        html = r.text
        # Check for sidebar elements and tenant context
        has_nav = "Overview" in html and "Gateway" in html and "Policies" in html and "Agent" in html and "Frameworks" in html and "Audit" in html and "Settings" in html
        has_tenant = "a0eebc99-0000-0000-0000-bb6d6bb9bd11" in html # tenant ID context
        has_user = "admin@authclaw.com" in html
        
        if has_nav and has_tenant and has_user:
            print("   [PASS] Overview page loads with active tenant context, user email, and full sidebar navigation shell.")
        else:
            print(f"   [FAIL] Overview page missing metadata. Sidebar navigation items found: {has_nav}, Tenant Context: {has_tenant}, User profile: {has_user}")
            sys.exit(1)
    else:
        print(f"   [FAIL] Overview page failed with status {r.status_code}")
        sys.exit(1)

    # 5. Verify all Stub Pages render
    stubs = ["gateway", "policies", "agent", "frameworks", "audit", "settings"]
    print("5. Verifying rendering of all stub routes...")
    for stub in stubs:
        r = session.get(f"{BASE_URL}/{stub}", allow_redirects=False)
        if r.status_code == 200:
            print(f"   [PASS] Route /{stub} rendered successfully.")
        else:
            print(f"   [FAIL] Route /{stub} failed with status {r.status_code}")
            sys.exit(1)

    # 6. Verify Logout works
    print("6. Verifying Logout clears session...")
    r = session.post(f"{BASE_URL}/api/auth/logout")
    if r.status_code == 200 and "authclaw_session" not in session.cookies:
        print("   [PASS] Logout endpoint cleared cookies successfully.")
    else:
        print("   [FAIL] Logout failed or cookie not cleared.")
        sys.exit(1)

    # 7. Verify Protected Routes redirect to login when unauthenticated
    print("7. Verifying protected route access control...")
    r = session.get(f"{BASE_URL}/overview", allow_redirects=False)
    if r.status_code == 307 and r.headers.get("Location") == "/login":
        print("   [PASS] Protected route correctly redirected unauthenticated request to /login.")
    else:
        print(f"   [FAIL] Accessing /overview without session returned status {r.status_code}, redirect header: {r.headers.get('Location')}")
        sys.exit(1)

    print("\nSANITY CHECK RESULT: ALL Exit Criteria Verified - [PASS]")

if __name__ == "__main__":
    run_sanity_check()
