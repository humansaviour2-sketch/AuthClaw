# AuthClaw Implementation Plan — Solo AI Engineer Edition
**Project**: AI Governance & Compliance Platform  
**Format**: 15 Mini-Phases (not following original 4-phase model)  
**Solo Engineer Hours Budget**: ~1,200–1,400 hours to MVP (Phase 1–12) + hardening (Phase 13–15)  
**Target Calendar**: ~30 weeks at 40 hrs/week effective delivery  

---

## 📋 Mini-Phase Roadmap

| Phase | Focus | Est. Hours | Owner | Status |
|-------|-------|-----------|-------|--------|
| **1** | Dev environment & infra validation | 40 | Solo | Not started |
| **2** | Multi-tenant data model & auth baseline | 80 | Solo | Not started |
| **3** | Gateway skeleton (reverse proxy, routing) | 80 | Solo | Not started |
| **4** | PII/PHI redaction engine integration | 100 | Solo | Not started |
| **5** | Policy enforcement (OPA + YAML) | 80 | Solo | Not started |
| **6** | Backend APIs (FastAPI control plane) | 100 | Solo | Not started |
| **7** | Audit log storage & event backbone | 80 | Solo | Not started |
| **8** | LangGraph orchestrator foundation | 100 | Solo | Not started |
| **9** | Ephemeral workers & cloud connectors | 90 | Solo | Not started |
| **10** | HITL approval workflow & state machine | 80 | Solo | Not started |
| **11** | Console foundation (Next.js app shell) | 60 | Solo | Not started |
| **12** | Console UX: dashboard, config, audit | 100 | Solo | Not started |
| **13** | Integration testing & smoke suite | 60 | Solo | Not started |
| **14** | Compliance automation (SOC 2/GDPR scoring) | 80 | Solo | Not started |
| **15** | Security hardening & production readiness | 100 | Solo | Not started |
| | **Total** | **1,360** | | |

---

## Phase-by-Phase Breakdown

### Phase 1: Dev Environment & Infra Validation ⚙️
**Duration**: 1 week | **Hours**: 40  
**Owner**: Solo  
**Goal**: Have a working local development environment with all services running.

#### Tasks
- [ ] Clone repo, review docker-compose.yml
- [ ] Verify Docker & Docker Compose installed
- [ ] Run `docker-compose up` and confirm all services start (postgres, redis, opa, presidio)
- [ ] Create `.env.local` with test database credentials
- [ ] Set up PostgreSQL client tool (psql or GUI)
- [ ] Verify OPA is accessible at `http://localhost:8181`
- [ ] Verify Presidio is accessible at `http://localhost:3000`
- [ ] Document setup steps in README.md

#### Exit Criteria
✅ `docker-compose up -d` brings all 5 services online  
✅ Can connect to postgres and run basic queries  
✅ OPA responds at /v1/policies 
✅ Presidio analyzer is reachable  
✅ `.env.local` template created for team  

#### Tech Stack Used
- Docker, Docker Compose, PostgreSQL, Redis, OPA, Presidio

---

### Phase 2: Multi-Tenant Data Model & Auth Baseline 🔐
**Duration**: 2 weeks | **Hours**: 80  
**Owner**: Solo  
**Goal**: Database schema for multi-tenant isolation and RBAC foundation.

#### Tasks
- [ ] Design PostgreSQL schema:
  - `tenants` table (id, name, tier, created_at)
  - `users` table (id, tenant_id, email, role, mfa_enabled)
  - `api_keys` table (id, tenant_id, key_hash, name, scopes)
  - `audit_log` metadata table for ClickHouse reference
- [ ] Implement Row-Level Security (RLS) policies on all tenant-scoped tables
- [ ] Create migration system (Alembic for Python)
- [ ] Design RBAC roles: admin, operator, viewer
- [ ] Stub OIDC/IdP integration (auth placeholder)
- [ ] Envelope encryption for provider credentials (KMS stub using local key for dev)
- [ ] Write automated tests to verify cross-tenant isolation fails

#### Exit Criteria
✅ Schema migrated into postgres via Alembic  
✅ Cross-tenant read test fails (RLS enforced)  
✅ Admin, operator, viewer roles defined  
✅ MFA flag on users table (wired in later phases)  
✅ API key hash store working  

#### Tech Stack Used
- PostgreSQL, Alembic, SQLAlchemy ORM, Python

---

### Phase 3: Gateway Skeleton (Reverse Proxy & Routing) 🚪
**Duration**: 2 weeks | **Hours**: 80  
**Owner**: Solo  
**Goal**: Basic reverse proxy that routes requests to LLM providers without alteration.

#### Tasks
- [ ] Initialize gateway project (Go or Rust; recommend Go for speed)
- [ ] Implement HTTP/HTTPS reverse proxy ingress
- [ ] Route table for OpenAI, Anthropic, Cohere, Azure OpenAI
- [ ] Request/response adapter layer (normalizes provider payloads)
- [ ] Tenant & API-key extraction from headers
- [ ] Audit event emission to Kafka (stub, no Kafka server yet)
- [ ] Contract tests for provider payload fidelity (OpenAI, Anthropic)
- [ ] Local dev: curl tests against real provider sandboxes (or mocks)

#### Exit Criteria
✅ Gateway listens on `localhost:8080`  
✅ `POST /v1/chat/completions` to OpenAI is proxied transparently  
✅ Tenant ID extracted from Authorization header  
✅ Requests/responses logged to stdout (audit placeholder)  
✅ Contract tests pass (fidelity check)  

#### Tech Stack Used
- Go (net/http), Chi router, contract testing

---

### Phase 4: PII/PHI Redaction Engine Integration 🔍
**Duration**: 2.5 weeks | **Hours**: 100  
**Owner**: Solo  
**Goal**: Redaction of sensitive data before egress to LLM providers.

#### Tasks
- [ ] Integrate Microsoft Presidio (already in docker-compose)
- [ ] Custom NER pipelines (name, email, phone, SSN, health data)
- [ ] Three redaction strategies:
  - Masking (replace with `[REDACTED]`)
  - SHA-256+salt hashing (reversible via tenant key)
  - Synthetic replacement (generate fake but realistic data)
- [ ] Tokenization map: store mappings in PostgreSQL per tenant
- [ ] Apply redaction to inbound prompts
- [ ] Apply redaction to outbound completions (including streaming)
- [ ] Performance profiling (must not exceed 50 ms per request)
- [ ] Unit tests for each redaction strategy

#### Exit Criteria
✅ Presidio integration deployed in gateway  
✅ Inbound prompt redaction works (PII masked/hashed)  
✅ Outbound completion redaction works  
✅ Streaming responses redacted without fragmentation  
✅ Latency profiling shows < 50 ms overhead  
✅ Tokenization map reversible per tenant  

#### Tech Stack Used
- Microsoft Presidio, spaCy NER, PostgreSQL (tokenization store)

---

### Phase 5: Policy Enforcement (OPA + YAML) 📋
**Duration**: 2 weeks | **Hours**: 80  
**Owner**: Solo  
**Goal**: Block requests that violate enterprise policies.

#### Tasks
- [ ] OPA integration in gateway (already in docker-compose)
- [ ] YAML policy-as-code format:
  - Topic classification blocking (no medical data to non-medical model)
  - Regex patterns for sensitive topics
  - Model whitelist/blacklist per tenant
  - Rate limits (requests/minute)
- [ ] Policy validator: reject malformed policies at deploy time
- [ ] Load policies from PostgreSQL
- [ ] Audit trail for policy decisions (block reason logged)
- [ ] Policy editor stub in backend API
- [ ] Unit & integration tests for policy evaluation

#### Exit Criteria
✅ OPA queries policies from PostgreSQL  
✅ YAML validator rejects invalid policies  
✅ Request blocked if topic matches forbidden pattern  
✅ Audit event logged for each policy decision  
✅ Policy hot-reload (no gateway restart needed)  
✅ Tests cover allow/block decision paths  

#### Tech Stack Used
- Open Policy Agent (OPA), YAML, Go test framework

---

### Phase 6: Backend APIs (FastAPI Control Plane) 🔧
**Duration**: 2.5 weeks | **Hours**: 100  
**Owner**: Solo  
**Goal**: REST APIs for configuring gateway, managing tenants, viewing logs.

#### Tasks
- [ ] Initialize FastAPI project with SQLAlchemy ORM
- [ ] Core endpoints:
  - `POST /tenants` — create new tenant (admin only)
  - `POST /gateways` — register a gateway config per tenant
  - `POST /policies` — upload/update YAML policy
  - `GET /gateway/{id}/config` — retrieve gateway routing config
  - `GET /redaction/{id}/tokenization-map` — retrieve reversible tokens
  - `GET /audit-logs` — stub endpoint (full audit in Phase 7)
- [ ] Tenant context middleware (extract from token, enforce isolation)
- [ ] API authentication (bearer token, API key validation)
- [ ] Request/response validation (Pydantic)
- [ ] Unit tests for each endpoint
- [ ] OpenAPI schema auto-generated

#### Exit Criteria
✅ FastAPI server runs on `localhost:8000`  
✅ POST /tenants creates a tenant in PostgreSQL  
✅ POST /gateways stores routing config  
✅ POST /policies validates and stores YAML  
✅ All reads enforce tenant isolation  
✅ OpenAPI /docs endpoint works  
✅ Auth middleware validates API keys  

#### Tech Stack Used
- FastAPI, SQLAlchemy, Pydantic, Python

---

### Phase 7: Audit Log Storage & Event Backbone 📊
**Duration**: 2 weeks | **Hours**: 80  
**Owner**: Solo  
**Goal**: Immutable audit trail stored in ClickHouse; event publishing via Kafka.

#### Tasks
- [ ] Set up ClickHouse (add to docker-compose if not present)
- [ ] Audit log schema:
  - `record_id` (UUID)
  - `tenant_id` (UUID)
  - `timestamp` (DateTime)
  - `actor` (object: {id, type})
  - `action` (string)
  - `frameworks_affected` (array)
  - `execution_trace` (JSON array)
  - `integrity_hash` (SHA-256 chain)
- [ ] Hash-chaining logic (each record links to prior via integrity_hash)
- [ ] Set up Kafka topics:
  - `gateway.traffic` — request/response events
  - `audit.events` — compliance actions
  - `agent.actions` — agent decisions
- [ ] Kafka producer in gateway (async, non-blocking)
- [ ] Kafka consumer → ClickHouse writer
- [ ] Audit log read API (paginated, tenant-scoped)
- [ ] Integrity verification endpoint (check hash chain)

#### Exit Criteria
✅ ClickHouse cluster running (single-node for dev)  
✅ Gateway publishes events to Kafka  
✅ Kafka consumer writes to ClickHouse  
✅ Hash chain verified: each record includes prior hash  
✅ Audit log readable via API (first 100 records)  
✅ Can verify hash integrity of a record  
✅ No gaps or tampering possible (append-only)  

#### Tech Stack Used
- ClickHouse, Kafka, Python Kafka client

---

### Phase 8: LangGraph Orchestrator Foundation 🧠
**Duration**: 2.5 weeks | **Hours**: 100  
**Owner**: Solo  
**Goal**: Agentic reasoning engine for compliance scanning.

#### Tasks
- [ ] Set up LangGraph Python project
- [ ] State machine design:
  - `GATHER_SCAN` — read cloud metadata (AWS/GCP)
  - `ANALYZE_COMPLIANCE` — check against GDPR/HIPAA/SOC 2
  - `GENERATE_PLAN` — propose fixes (Terraform diffs)
  - `AWAITING_APPROVAL` — human sign-off required
  - `EXECUTING_FIX` — apply approved changes
  - `COMPLETE` — log result
- [ ] Stub cloud connectors (return mock data for now)
- [ ] RAG setup:
  - Ingest GDPR, HIPAA, SOC 2 docs into vector DB (Chroma or Pinecone)
  - LangChain RAG chain for compliance querying
- [ ] LLM integration (OpenAI GPT-4 or similar for reasoning)
- [ ] Execution trace logging (every step recorded for audit)
- [ ] Unit tests for state transitions
- [ ] Local testing harness

#### Exit Criteria
✅ LangGraph orchestrator runs locally  
✅ State machine transitions work (GATHER → ANALYZE → PLAN)  
✅ RAG retrieves relevant compliance docs  
✅ Orchestrator can ask agent: "Is this GDPR compliant?"  
✅ Execution trace emitted to audit log  
✅ Mock cloud scan returns synthetic compliance gaps  
✅ All state transitions audited  

#### Tech Stack Used
- LangGraph, LangChain, OpenAI API, Chroma/Pinecone, Python

---

### Phase 9: Ephemeral Workers & Cloud Connectors ☁️
**Duration**: 2.3 weeks | **Hours**: 90  
**Owner**: Solo  
**Goal**: Short-lived worker processes that execute scans and remediations.

#### Tasks
- [ ] Worker framework:
  - Docker containers spun up per scan/remediation
  - Scoped, temporary credentials (AWS STS, GCP service account)
  - Auto-cleanup after max 15 min TTL
- [ ] AWS connector:
  - List IAM policies, security groups, bucket configs
  - Detect non-compliant settings (public buckets, overpermissioned roles)
  - Generate Terraform fixes
- [ ] GCP connector (similar to AWS)
- [ ] GitHub connector:
  - Scan repos for secrets (TruffleHog, git-secrets)
  - Check branch protection rules
- [ ] Worker → Orchestrator callback (status updates)
- [ ] Secret management:
  - Store provider credentials in PostgreSQL (envelope encrypted)
  - Generate scoped tokens, expire after use
- [ ] Error handling & retry logic
- [ ] Audit: log every worker action

#### Exit Criteria
✅ Worker Docker image builds  
✅ AWS connector scans S3 & IAM policies  
✅ Worker receives scoped credentials (not long-lived keys)  
✅ Worker reports findings back to orchestrator  
✅ Terraform plan diffs generated for fixes  
✅ Worker terminated after execution  
✅ All worker actions audited  

#### Tech Stack Used
- Docker, AWS SDK, GCP SDK, GitHub API, Terraform, Python

---

### Phase 10: HITL Approval Workflow & State Machine 👥
**Duration**: 2 weeks | **Hours**: 80  
**Owner**: Solo  
**Goal**: Human-in-the-loop controls for agent actions.

#### Tasks
- [ ] HITL state machine:
  - `READ_ONLY_SCAN` — agent scans, no risk
  - `PENDING_USER_APPROVAL` — agent proposes action, awaits human
  - `MFA_CHALLENGE` — human must pass MFA to approve
  - `EXECUTING` — approved action in progress
  - `COMPLETED` or `FAILED`
- [ ] Auto-expiry: proposed actions expire after 30 min if not approved
- [ ] MFA gate:
  - TOTP (Time-based One-Time Password) validation
  - TOTP backup codes for recovery
- [ ] Approval audit trail:
  - Who approved, when, MFA timestamp
  - Approval is non-transferable (bound to approver)
  - Single-use (can't re-approve same action)
- [ ] Database schema for approvals:
  - `pending_approvals` table (action_id, requester, approver, status, expires_at)
  - `approval_audit` (immutable log)
- [ ] State machine validation tests
- [ ] Expiry checker (background job to auto-expire stale approvals)

#### Exit Criteria
✅ Approval state machine implemented  
✅ Proposed action entered PENDING state  
✅ Action auto-expires after 30 min  
✅ MFA challenge required before execution  
✅ TOTP validation working (test with Google Authenticator)  
✅ Approval non-transferable & single-use  
✅ All approvals logged immutably  
✅ Tests verify state transitions  

#### Tech Stack Used
- PostgreSQL, Python, pyotp (TOTP library)

---

### Phase 11: Console Foundation (Next.js App Shell) 🖥️
**Duration**: 1.5 weeks | **Hours**: 60  
**Owner**: Solo  
**Goal**: Next.js admin console with authentication and tenant context.

#### Tasks
- [ ] Initialize Next.js 15 project
- [ ] Authentication:
  - Login page (email/password stub, wire to backend API key validation)
  - Session management (JWT or cookies)
  - Logout
- [ ] Tenant context middleware (inject tenant_id into all requests)
- [ ] Navigation shell:
  - Sidebar with menu items (Overview, Gateway, Policies, Agent, Frameworks, Audit, Settings)
  - User profile dropdown
  - Logout button
- [ ] Design system (Tailwind CSS + shadcn/ui components)
- [ ] Responsive layout (mobile-friendly)
- [ ] API client abstraction (fetch wrapper with error handling)
- [ ] Protected routes (require auth to access)
- [ ] Stub all menu pages (empty for now)

#### Exit Criteria
✅ Next.js dev server runs on `localhost:3000`  
✅ Login page functional (hardcode test user for now)  
✅ Session persists across page reloads  
✅ Sidebar navigation renders  
✅ All routes require auth (redirect to login if not)  
✅ Design system applied globally  
✅ Tenant context available in all pages  
✅ Logout clears session  

#### Tech Stack Used
- Next.js 15, TypeScript, Tailwind CSS, shadcn/ui

---

### Phase 12: Console UX — Dashboard, Config, Audit 📱
**Duration**: 2.5 weeks | **Hours**: 100  
**Owner**: Solo  
**Goal**: Core admin UX for managing gateway, policies, and viewing audit logs.

#### Tasks
- [ ] **Overview Dashboard**:
  - Live SOC 2 / GDPR / HIPAA readiness % (stub scoring for now)
  - Open approvals count
  - Redaction stats (# PII masked in last 24h)
  - Traffic KPIs (requests/sec, p99 latency)
- [ ] **Gateway Config UI**:
  - List configured routes (OpenAI, Anthropic, Cohere, Azure)
  - Add/edit route: provider, endpoint, model whitelist
  - Per-route redaction strategy picker (mask/hash/synthetic)
  - Live traffic inspector (last 20 requests, scrubbed)
- [ ] **Policy Editor**:
  - YAML editor with syntax highlighting
  - Validate policy before save
  - Version history (show diff between versions)
- [ ] **Audit Log Explorer**:
  - Paginated log viewer
  - Filter by action, date range, actor
  - Hash integrity badge (✓ verified or ⚠️ tampered)
  - Export as CSV/JSON
- [ ] **Settings > Tenant Admin**:
  - Users: add/remove, role assignment
  - API keys: generate, revoke, scope
  - MFA status per user
- [ ] Real-time updates (WebSocket or polling)

#### Exit Criteria
✅ Dashboard loads & displays metrics  
✅ Gateway config page lists routes  
✅ Can add new gateway route  
✅ Redaction strategy selector works  
✅ YAML policy editor validates syntax  
✅ Audit log shows last 50 entries  
✅ Hash integrity badge functional  
✅ Tenant users/roles manageable  
✅ API key lifecycle UI works (generate, copy, revoke)  

#### Tech Stack Used
- Next.js, React, TypeScript, Tailwind CSS, WebSocket (or SWR polling)

---

### Phase 13: Integration Testing & Smoke Suite 🧪
**Duration**: 1.5 weeks | **Hours**: 60  
**Owner**: Solo  
**Goal**: End-to-end tests verifying gateway → backend → console flow.

#### Tasks
- [ ] Integration test suite (pytest + requests for API, Playwright for UI)
- [ ] **Gateway → Backend Integration**:
  - Request flows through gateway, redaction applied, audit logged
  - Policy blocks disallowed traffic
  - Response proxied back correctly
- [ ] **Backend → Database Integration**:
  - Tenant isolation holds (cross-tenant read fails)
  - API key validation works
  - Policies applied per tenant
- [ ] **Agent → Orchestrator Integration**:
  - Scan initiated → findings returned
  - Approval requested → state transitions correctly
  - MFA validation required before execution
- [ ] **Console → Backend Integration**:
  - Login works, session persists
  - Dashboard metrics load
  - Gateway config CRUD works
  - Policy editor saves to backend
  - Audit log explorer displays records
- [ ] Smoke test suite (happy path only, runs ~5 min)
- [ ] Continuous integration: run tests on every commit

#### Exit Criteria
✅ Integration tests run successfully (end-to-end)  
✅ Smoke suite passes (basic flow works)  
✅ No cross-tenant data leaks in tests  
✅ Audit trail complete (all actions logged)  
✅ CI/CD runs tests automatically  
✅ Test coverage report generated  

#### Tech Stack Used
- pytest, requests, Playwright, GitHub Actions (or similar CI)

---

### Phase 14: Compliance Automation (SOC 2 / GDPR Scoring) 📜
**Duration**: 2 weeks | **Hours**: 80  
**Owner**: Solo  
**Goal**: Automated framework scoring and compliance evidence collection.

#### Tasks
- [ ] **Framework Mappings**:
  - SOC 2 Type II controls (70 controls across 5 trust service criteria)
  - GDPR articles (Articles 1–11 core, 12–49 data-subject rights, etc.)
  - HIPAA rules (administrative, physical, technical safeguards)
- [ ] **Evidence Collection**:
  - Gateway logs as evidence of traffic monitoring
  - HITL approvals as evidence of change control
  - Audit trail immutability as evidence of tamper-proofing
  - MFA logs as evidence of authentication
  - Redaction metrics as evidence of PII protection
- [ ] **Scoring Engine**:
  - Per-control: assessed, partially assessed, not assessed
  - Overall readiness % (green, yellow, red)
  - Drill-down: which logs/artifacts prove compliance
- [ ] **Evidence Export**:
  - PDF report: control assessments + linked audit records
  - Attachment: exported audit logs (signed)
- [ ] **Compliance Dashboard**:
  - Override & evidence tagging (admin can mark control as complete)
  - Remediation gaps (controls still pending fixes)
  - Timeline view (when controls met)

#### Exit Criteria
✅ SOC 2, GDPR, HIPAA controls mapped to product features  
✅ Readiness % calculated (e.g., 78% GDPR compliant)  
✅ Evidence linked to audit records  
✅ Export PDF generated successfully  
✅ Admin can tag evidence against controls  
✅ Compliance dashboard shows remediation gaps  
✅ All calculations audited  

#### Tech Stack Used
- Python (scoring logic), jinja2 (PDF templates), ClickHouse (evidence queries)

---

### Phase 15: Security Hardening & Production Readiness 🔒
**Duration**: 2.5 weeks | **Hours**: 100  
**Owner**: Solo  
**Goal**: Finalize security, performance, HA, and launch readiness.

#### Tasks
- [ ] **Security Hardening**:
  - Input validation & sanitization (all endpoints)
  - SQL injection prevention (parameterized queries everywhere)
  - XSS prevention (Content-Security-Policy headers)
  - CSRF protection
  - Rate limiting per tenant + per IP
  - WAF rules (if using cloud provider)
- [ ] **Secrets Management**:
  - Rotate KMS keys regularly
  - Never log secrets (audit scrubbing)
  - HashiCorp Vault integration (prod-grade key management)
- [ ] **Performance Optimization**:
  - Gateway latency profiling & tuning (target ≤ 50 ms)
  - Database query optimization (indexes, query plans)
  - Caching (Redis for hot data)
  - Load testing (simulate 100+ concurrent users)
- [ ] **High Availability**:
  - Multi-region deployment (primary + standby)
  - Database replication (cross-region)
  - Failover automation
  - Health checks & circuit breakers
- [ ] **Monitoring & Observability**:
  - Logs: centralized logging (ELK or CloudWatch)
  - Metrics: Prometheus + Grafana
  - Traces: distributed tracing (Jaeger)
  - Alerts: critical path alerts (gateway down, audit loss)
- [ ] **Documentation**:
  - Architecture diagrams
  - API reference (auto-generated from OpenAPI)
  - Deployment runbooks
  - Security guidelines
  - Troubleshooting guide
- [ ] **Testing**:
  - Penetration test (hire contractor or use automated scanners)
  - Chaos engineering (kill pods, simulate failures)
  - Red-team probes (prompt injection, data leaks)
- [ ] **Compliance Evidence Automation**:
  - SOC 2 control automation (collect evidence daily)
  - Audit log integrity checks (daily hash verification)
  - Change log for all configs

#### Exit Criteria
✅ All security checklist items addressed  
✅ No OWASP Top 10 vulnerabilities found  
✅ Gateway latency ≤ 50 ms measured under load  
✅ 99.9% uptime demonstrated (5-nines target for future)  
✅ Multi-region failover tested  
✅ All critical metrics monitored & alerted  
✅ Documentation complete & current  
✅ Penetration test passed (or minor fixes queued)  
✅ SOC 2 evidence collection automated  
✅ Ready for customer pilot  

#### Tech Stack Used
- Vault, Prometheus, Grafana, Jaeger, ELK/CloudWatch, Terraform (IaC)

---

## 🎯 Success Criteria (MVP Definition)

At the end of Phase 12, the product is **MVPable**. It can:

1. ✅ Intercept requests to LLM providers and redact PII in real time
2. ✅ Enforce company policies (block disallowed topics)
3. ✅ Scan cloud environments for compliance gaps (AWS/GCP)
4. ✅ Gate agent actions behind human approval + MFA
5. ✅ Record every action immutably (audit trail)
6. ✅ Display compliance readiness (SOC 2 / GDPR / HIPAA %)
7. ✅ Export verifiable compliance reports
8. ✅ Support multiple tenants with strict isolation
9. ✅ Provide a working admin console

Phase 13–15 hardens and prepares for production.

---

## 🔄 Dependencies & Sequencing

```
Phase 1: Dev Env
    ↓
Phase 2: Multi-tenant DB & Auth ← must complete before building anything else
    ├→ Phase 3: Gateway Skeleton
    │   ├→ Phase 4: Redaction
    │   └→ Phase 5: Policy Enforcement
    │       ↓
    ├→ Phase 6: Backend APIs
    │   ├→ Phase 7: Audit Log Storage
    │   ├→ Phase 8: LangGraph Orchestrator
    │   │   ├→ Phase 9: Ephemeral Workers
    │   │   └→ Phase 10: HITL Approval
    │   └→ Phase 14: Compliance Scoring
    │       ↓
    ├→ Phase 11: Console Foundation
    │   └→ Phase 12: Console UX
    │       ↓
Phase 13: Integration Testing
    ↓
Phase 15: Security Hardening
```

**Critical Path**: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 15  
**Parallel possible**: Phases 3–5 can overlap with 6–7 after Phase 2 is done.

---

## 📊 Effort Breakdown by Component

| Component | Hours | Phases |
|-----------|-------|--------|
| Foundation & Auth | 120 | 1–2 |
| Gateway (Proxy, Redaction, Policy) | 260 | 3–5 |
| Backend & Storage | 180 | 6–7 |
| Agent Engine & HITL | 270 | 8–10 |
| Console UI | 160 | 11–12 |
| Testing & Integration | 60 | 13 |
| Compliance Automation | 80 | 14 |
| Hardening & Prod Readiness | 100 | 15 |
| **Total** | **1,360** | |

---

## 📌 Weekly Cadence (Recommended)

- **2 weeks per phase minimum** (some may take 2.5 weeks)
- **Weekly sync with self**: review progress, adjust estimates, update blockers
- **Bi-weekly demos**: record video showing current state (even if only 70% complete)
- **Continuous small commits**: push daily to avoid losing work

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| Redaction latency exceeds 50 ms | High | Medium | Profile in Phase 4; use Go hot path; defer heavy NER to async |
| Streaming response fragmentation | High | Medium | Prototype chunk evaluation in Phase 4; test with real providers |
| Tenant isolation breach | Critical | Low | RLS + automated cross-tenant tests in Phase 2; pentest in Phase 15 |
| HITL approval bypass | Critical | Low | Single audited execution path; MFA required; server-side expiry enforcement |
| Audit log tampering | Critical | Low | Append-only ClickHouse; SHA-256 chaining; restricted write ACLs |
| Provider API drift | Medium | Medium | Contract tests in CI; adapter layer isolates changes |
| Scope creep | Medium | High | Use this 15-phase plan as a contract; defer features to Phase 2+ roadmap |

---

## 🚀 Next Steps (Immediate Actions)

1. **This Week (Start of Phase 1)**:
   - [ ] Clone repo locally
   - [ ] Review this plan with anyone else who needs context
   - [ ] Verify docker-compose.yml runs without errors
   - [ ] Set up `.env.local` & `.env.test` files
   - [ ] Create a GitHub Project board or Trello with phases as swimlanes

2. **Before Phase 2**:
   - [ ] Design PostgreSQL schema (use Phase 2 tasks as spec)
   - [ ] Set up Alembic for migrations
   - [ ] Create a tech spike for OIDC integration (research libraries)

3. **Throughout**:
   - [ ] Update this plan every 2 weeks based on learnings
   - [ ] Keep `/memories/repo/authclaw_project_analysis.md` in sync

---

**Document Version**: 1.0  
**Last Updated**: 2026-06-12  
**Owner**: Solo AI Engineer  
**Status**: Ready for Phase 1 kickoff
