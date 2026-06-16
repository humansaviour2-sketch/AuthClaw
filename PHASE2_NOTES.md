# Phase 2: Multi-Tenant Data Model & Auth Baseline

**Duration**: 2 weeks | **Hours**: 80  
**Status**: 🚀 Starting  
**Goal**: Database schema for multi-tenant isolation and RBAC foundation

---

## 📋 Deliverables Checklist

- [x] PostgreSQL schema design (8 core tables)
- [x] SQLAlchemy ORM models
- [x] Alembic migration system
- [x] Row-Level Security (RLS) policies
- [x] RBAC role system (admin, operator, viewer)
- [x] Envelope encryption stubs
- [x] Cross-tenant isolation tests
- [x] Python FastAPI backend skeleton
- [x] Pydantic schemas for validation

---

## 🏗️ Architecture

### Database Schema (8 Tables)

```
┌─────────────────────────────────────┐
│ tenants                             │
├─────────────────────────────────────┤
│ id (UUID)                           │
│ name (String, unique)               │
│ tier (starter|pro|enterprise)       │
│ status (active|suspended)           │
└─────────────────────────────────────┘
           ↓ (1-to-many)
┌─────────────────────────────────────┐
│ users, api_keys, policies,          │
│ gateway_configs, redaction_tokens,  │
│ pending_approvals, audit_logs       │
├─────────────────────────────────────┤
│ All have tenant_id (FK to tenants)  │
│ All have RLS policies               │
└─────────────────────────────────────┘
```

### Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **tenants** | Multi-tenant registry | id, name, tier, status |
| **users** | Team members per tenant | id, tenant_id, email, role, mfa_enabled |
| **api_keys** | Service-to-service auth | id, tenant_id, key_hash, scopes |
| **policies** | YAML policy storage | id, tenant_id, policy_yaml, version |
| **gateway_configs** | LLM provider routing | id, tenant_id, provider, endpoint |
| **redaction_tokens** | PII tokenization map | id, tenant_id, original_value, token_value |
| **pending_approvals** | HITL workflow state | id, tenant_id, action_id, status, approver_id |
| **audit_log_metadata** | ClickHouse reference | id, tenant_id, record_id, action |

---

## 🔐 Security Features Implemented

### Row-Level Security (RLS)

Every tenant-scoped table has RLS policies that enforce:

```sql
-- Example: users table isolation
CREATE POLICY users_isolation ON users
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

**Result**: Database enforces isolation. Even if someone exploits the application layer, PostgreSQL blocks cross-tenant access.

### RBAC Roles

| Role | Permissions |
|------|-------------|
| **admin** | All operations (create, read, update, delete) |
| **operator** | Create & update (limited delete) |
| **viewer** | Read-only access |

---

## 📁 Project Structure

```
backend/
├── main.py                          # FastAPI entry point
├── requirements.txt                 # Python dependencies
├── alembic.ini                      # Alembic config
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py               # Settings from .env.local
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                 # SQLAlchemy Base
│   │   ├── models.py               # ORM models (8 tables)
│   │   ├── session.py              # Session management
│   │   └── dependencies.py         # FastAPI dependencies
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py               # Pydantic schemas
├── alembic/
│   ├── env.py                      # Alembic environment
│   └── versions/
│       └── 001_initial_schema.py   # Initial migration
├── tests/
│   ├── __init__.py
│   └── test_tenant_isolation.py    # RLS tests
```

---

## 🧪 Testing

### Run All Tests

```powershell
cd backend
pytest tests/test_tenant_isolation.py -v
```

### Test Coverage

- ✅ Tenant isolation (SELECT)
- ✅ Cross-tenant insert prevention (RLS enforced)
- ✅ API key isolation
- ✅ Policy isolation
- ✅ Approval workflow isolation

### Test Expected Behavior

```python
# Test 1: Tenant A cannot see Tenant B's users
# Set context to Tenant A
SET app.current_tenant_id = <tenant_a_id>

# Query users table
SELECT * FROM users
# Returns: Only users where tenant_id = tenant_a_id

# Test 2: Cannot insert data for wrong tenant
INSERT INTO users (tenant_id, ...) VALUES (<tenant_b_id>, ...)
# Result: RLS policy denies INSERT
```

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 13+ (running in docker-compose)
- pip

### Step 1: Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### Step 2: Run Migrations

```powershell
cd backend
alembic upgrade head
```

This creates all 8 tables with proper indexes.

### Step 3: Enable RLS Policies

```powershell
docker-compose exec -T postgres psql -U authclaw -d authclaw \
  -f ../infra/postgres/02_enable_rls.sql
```

### Step 4: Run Tests

```powershell
pytest tests/test_tenant_isolation.py -v
```

### Or Use the Setup Script

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-phase2.ps1
```

---

## 📊 Exit Criteria

- [x] Schema migrated into PostgreSQL via Alembic
- [x] Cross-tenant read test fails (RLS enforced)
- [x] Admin, operator, viewer roles defined
- [x] MFA flag on users table (wired in later phases)
- [x] API key hash store working
- [x] All 8 tables created with proper indexes
- [x] RLS policies applied to all tenant-scoped tables

---

## 🔄 How RLS Works (Multi-Tenant Isolation)

### Setting Tenant Context

Before any query, the application sets the tenant context:

```python
# In FastAPI middleware (Phase 6)
db.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
```

### Query Filtering

RLS automatically filters queries:

```python
# Developer writes:
users = db.query(User).all()

# PostgreSQL executes (with RLS):
SELECT * FROM users 
WHERE tenant_id = current_setting('app.current_tenant_id')::uuid

# Result: Only that tenant's users returned
```

### Protection Against SQL Injection

Even if an attacker bypasses the ORM:

```sql
-- Attacker tries:
SELECT * FROM users WHERE email = 'admin@example.com' --

-- PostgreSQL still applies RLS:
SELECT * FROM users 
WHERE (email = 'admin@example.com' --) 
AND tenant_id = current_setting('app.current_tenant_id')::uuid

-- Result: No rows if admin is in different tenant
```

---

## 🔑 Encryption Notes (Phase 2 Stubs)

The following are prepared for Phase 2 but fully implemented in Phase 15:

- **MFA Secret Storage**: Encrypted via KMS (stub in Phase 2)
- **API Key Hashing**: SHA-256 (dev-friendly in Phase 2, production in Phase 15)
- **Original Value Encryption**: Envelope encryption (stub in Phase 2)

---

## 📚 Next Steps (Phase 3)

Phase 3 builds on this foundation:

- Gateway reverse proxy to intercept LLM traffic
- Uses `tenant_id` from Authorization header
- Sets RLS context before any database query
- Routes based on `gateway_configs` table

---

## 🆘 Troubleshooting

### Migration Fails

```powershell
# Check current revision
cd backend
alembic current

# Downgrade to start fresh
alembic downgrade base

# Upgrade again
alembic upgrade head
```

### RLS Tests Fail

```powershell
# Verify RLS is enabled
docker-compose exec -T postgres psql -U authclaw -d authclaw \
  -c "SELECT tablename, policyname FROM pg_policies LIMIT 10;"

# Should show multiple policies for each table
```

### Cross-Tenant Data Visible

```powershell
# Check if context is being set
docker-compose exec -T postgres psql -U authclaw -d authclaw \
  -c "SELECT current_setting('app.current_tenant_id');"

# If NULL, context not set (check FastAPI middleware)
```

---

## 📖 Reference

- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Pydantic Validation](https://docs.pydantic.dev/latest/)

---

**Phase 2 Status**: ✅ Scaffolding Complete  
**Next Phase**: Phase 3 - Gateway Skeleton  
**Document Version**: 1.0  
**Last Updated**: 2026-06-12
