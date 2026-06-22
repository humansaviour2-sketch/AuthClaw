import requests
import sys

BASE_URL = "http://localhost:3001"

def run_checks():
    print("Starting Phase 12 Console API & Integration Verification...\n")
    session = requests.Session()

    # 1. Log in to establish session
    print("1. Authenticating using database key manual_verif_key_123...")
    r = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@authclaw.com",
        "apiKey": "manual_verif_key_123"
    })
    if r.status_code == 200 and "authclaw_session" in session.cookies:
        print("   [PASS] Login successful, session cookie set.")
    else:
        print(f"   [FAIL] Login failed: status={r.status_code}, body={r.text}")
        sys.exit(1)

    # 2. Verify Session Endpoint
    print("2. Verifying session data retrieval...")
    r = session.get(f"{BASE_URL}/api/auth/session")
    if r.status_code == 200:
        data = r.json()
        if data.get("tenantId") and data.get("email") == "admin@authclaw.com":
            print(f"   [PASS] Session resolved: tenantId={data['tenantId']}, name={data.get('tenantName')}")
        else:
            print(f"   [FAIL] Session response data missing: {data}")
            sys.exit(1)
    else:
        print(f"   [FAIL] Session endpoint failed: status={r.status_code}")
        sys.exit(1)

    # 3. Verify Dashboard Endpoint
    print("3. Verifying dashboard metrics...")
    r = session.get(f"{BASE_URL}/api/dashboard")
    if r.status_code == 200:
        data = r.json()
        required_keys = ["openApprovals", "redactions24h", "totalRequests"]
        if all(k in data for k in required_keys):
            print(f"   [PASS] Dashboard metrics resolved. Approvals={data['openApprovals']}, Redactions={data['redactions24h']}, Total={data['totalRequests']}")
        else:
            print(f"   [FAIL] Dashboard metrics missing fields: {data}")
            sys.exit(1)
    else:
        print(f"   [FAIL] Dashboard endpoint failed: status={r.status_code}")
        sys.exit(1)

    # 4. Verify Gateway Route CRUD
    print("4. Testing Gateway route CRUD...")
    # List initial routes
    r = session.get(f"{BASE_URL}/api/gateways")
    if r.status_code == 200:
        routes = r.json()
        print(f"   [PASS] Gateways list retrieved (current size: {len(routes)})")
    else:
        print(f"   [FAIL] Gateway list failed: status={r.status_code}, body={r.text}")
        sys.exit(1)

    # Create new route
    new_route_payload = {
        "name": "Validation Test Route",
        "provider": "openai",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "redaction_strategy": "mask",
        "model_whitelist": ["gpt-4o"]
    }
    r = session.post(f"{BASE_URL}/api/gateways", json=new_route_payload)
    if r.status_code == 201:
        created_route = r.json()
        route_id = created_route["id"]
        print(f"   [PASS] Gateway route registered successfully: ID={route_id}")
    else:
        print(f"   [FAIL] Gateway registration failed: status={r.status_code}, body={r.text}")
        sys.exit(1)

    # Update route
    update_route_payload = {
        **new_route_payload,
        "redaction_strategy": "hash"
    }
    r = session.put(f"{BASE_URL}/api/gateways/{route_id}", json=update_route_payload)
    if r.status_code == 200:
        updated_route = r.json()
        if updated_route["redaction_strategy"] == "hash":
            print("   [PASS] Gateway route updated successfully.")
        else:
            print(f"   [FAIL] Gateway strategy not updated: {updated_route}")
            sys.exit(1)
    else:
        print(f"   [FAIL] Gateway update failed: status={r.status_code}")
        sys.exit(1)

    # Delete route
    r = session.delete(f"{BASE_URL}/api/gateways/{route_id}")
    if r.status_code == 204:
        print("   [PASS] Gateway route deleted successfully.")
    else:
        print(f"   [FAIL] Gateway deletion failed: status={r.status_code}")
        sys.exit(1)

    # 5. Verify Policy Revisions history & Active policy
    print("5. Verifying policy operations...")
    # List history
    r = session.get(f"{BASE_URL}/api/policies")
    if r.status_code == 200:
        history = r.json()
        print(f"   [PASS] Policy revision list fetched successfully (size: {len(history)}).")
    else:
        print(f"   [FAIL] Policy list failed: {r.status_code}")
        sys.exit(1)

    # Validate active policy
    r = session.get(f"{BASE_URL}/api/policies/active")
    if r.status_code in [200, 404]:
        print(f"   [PASS] Active policy fetched successfully (status={r.status_code}).")
    else:
        print(f"   [FAIL] Active policy check failed: {r.status_code}")
        sys.exit(1)

    # 6. Verify Audit log explorer queries
    print("6. Verifying audit log queries...")
    r = session.get(f"{BASE_URL}/api/audit?limit=5&integrity_check=true")
    if r.status_code == 200:
        data = r.json()
        print(f"   [PASS] Audit logs query successful. Source={data.get('source')}, Records={len(data.get('records', []))}")
    else:
        print(f"   [FAIL] Audit log query failed: status={r.status_code}")
        sys.exit(1)

    # 7. Verify User Management CRUD
    print("7. Testing user management CRUD...")
    # List users
    r = session.get(f"{BASE_URL}/api/users")
    if r.status_code == 200:
        users = r.json()
        print(f"   [PASS] User list retrieved successfully (size: {len(users)})")
    else:
        print(f"   [FAIL] User list failed: status={r.status_code}")
        sys.exit(1)

    # Create user
    new_user_payload = {
        "email": "test-operator@authclaw.com",
        "password": "temporary_password_123",
        "role": "operator"
    }
    r = session.post(f"{BASE_URL}/api/users", json=new_user_payload)
    if r.status_code == 201:
        created_user = r.json()
        user_id = created_user["id"]
        print(f"   [PASS] User created successfully: ID={user_id}")
    else:
        print(f"   [FAIL] User creation failed: status={r.status_code}, body={r.text}")
        sys.exit(1)

    # Delete user
    r = session.delete(f"{BASE_URL}/api/users/{user_id}")
    if r.status_code == 204:
        print("   [PASS] User deleted successfully.")
    else:
        print(f"   [FAIL] User deletion failed: status={r.status_code}")
        sys.exit(1)

    # 8. Verify API Key lifecycle
    print("8. Testing API key generation and revocation...")
    # List keys
    r = session.get(f"{BASE_URL}/api/api-keys")
    if r.status_code == 200:
        keys = r.json()
        print(f"   [PASS] API keys list retrieved (size: {len(keys)})")
    else:
        print(f"   [FAIL] Key list failed: status={r.status_code}")
        sys.exit(1)

    # Generate key
    r = session.post(f"{BASE_URL}/api/api-keys", json={
        "name": "Integration Test Key",
        "scopes": ["read", "write"]
    })
    if r.status_code == 201:
        data = r.json()
        key_id = data["id"]
        raw_secret = data["api_key"]
        print(f"   [PASS] API key generated successfully. ID={key_id}, Raw secret token revealed once: {raw_secret[:8]}...")
    else:
        print(f"   [FAIL] API key generation failed: status={r.status_code}, body={r.text}")
        sys.exit(1)

    # Revoke key
    r = session.delete(f"{BASE_URL}/api/api-keys/{key_id}")
    if r.status_code == 204:
        print("   [PASS] API key revoked/deleted successfully.")
    else:
        print(f"   [FAIL] Key revocation failed: status={r.status_code}")
        sys.exit(1)

    # 9. Verify Workflows & approvals query
    print("9. Verifying workflow queries...")
    r = session.get(f"{BASE_URL}/api/workflows")
    if r.status_code == 200:
        data = r.json()
        print(f"   [PASS] Workflows & pending approvals queried successfully. Workflows={len(data.get('workflows', []))}, Approvals={len(data.get('approvals', []))}")
    else:
        print(f"   [FAIL] Workflow query failed: status={r.status_code}")
        sys.exit(1)

    print("\nALL PHASE 12 CONSOLE INTEGRATIONS VERIFIED SUCCESSFULLY - [PASS]")

if __name__ == "__main__":
    run_checks()
