import os
import sys
import uuid
import requests
import json
from sqlalchemy import create_engine, text
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib

# Add parent dir to path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.db.base import Base
from app.db.models import Tenant, User, APIKey
from app.core.auth import hash_key

def seed_db():
    print("Seeding database...")
    db_url = settings.DATABASE_URL.replace("authclaw:authclaw@", "authclaw_app:authclaw@")
    # For seeding as owner, we can use the main settings.DATABASE_URL directly
    engine = create_engine(settings.DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    
    tenant_id = uuid.UUID("a0eebc99-0000-0000-0000-bb6d6bb9bd11")
    user_id = uuid.UUID("a0eebc99-0000-0000-0000-bb6d6bb9bd33")
    api_key_raw = "manual_verif_key_123"
    api_key_hash = hash_key(api_key_raw)
    
    with engine.connect() as conn:
        # Clear existing keys to avoid unique constraint violations
        conn.execute(text("TRUNCATE TABLE approval_audit, audit_log_metadata, pending_approvals, compliance_workflows, api_keys, users, tenants CASCADE;"))
        conn.commit()
        
        # Bypass RLS for inserts
        conn.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
        
        # Insert Tenant
        conn.execute(text(
            "INSERT INTO tenants (id, name, tier, status) VALUES (:id, 'Manual Tenant A', 'enterprise', 'active')"
        ), {"id": tenant_id})
        
        # Insert User
        conn.execute(text(
            "INSERT INTO users (id, tenant_id, email, role, mfa_enabled, is_active) VALUES (:id, :tenant_id, 'manualA@example.com', 'admin', false, true)"
        ), {"id": user_id, "tenant_id": tenant_id})
        
        # Insert API Key
        conn.execute(text(
            "INSERT INTO api_keys (id, tenant_id, key_hash, name, scopes, is_active, created_by) VALUES (:id, :tenant_id, :key_hash, 'Key A', :scopes, true, :created_by)"
        ), {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "key_hash": api_key_hash,
            "scopes": ["admin", "read", "write"],
            "created_by": user_id
        })
        conn.commit()
    print("Database seeded successfully.")
    return api_key_raw

def run_connectivity_test(api_key_raw):
    print("Testing live Gemini 2.5 Flash-Lite connectivity through AuthClaw Gateway...")
    
    url = "http://localhost:8080/v1/models/gemini-2.5-flash-lite:generateContent"
    headers = {
        "Authorization": f"Bearer {api_key_raw}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "My name is John Smith. My email is john.smith@example.com. My SSN is 123-45-6789. Summarize this information."}
                ]
            }
        ]
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"Response Status Code: {r.status_code}")
        print("Response Body:")
        print(json.dumps(r.json(), indent=2))
        
        resp_json = r.json()
        if "candidates" in resp_json:
            text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
            print(f"\nExtracted Response Text: {text.strip()}")
            print("\nRESULT: PASS")
            sys.exit(0)
        else:
            print("\nRESULT: FAIL - Response did not contain candidates.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nRESULT: FAIL - Connection error or API failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    key = seed_db()
    run_connectivity_test(key)
