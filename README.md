# AuthClaw — AI Governance & Compliance Platform

> Automated safety checkpoint for enterprise AI usage. Stops data leaks, enforces policies, enables compliance.

## 🚀 Quick Start (Phase 1: Dev Environment Setup)

### Prerequisites
- **Docker** 20.10+ and **Docker Compose** v2.0+
- **PostgreSQL** client (psql) — optional but recommended
- **Python** 3.11+ — for backend development
- **Node.js** 18+ — for frontend development
- **Go** 1.21+ — for gateway development

### 1️⃣ Verify Installation
```bash
# Check Docker
docker --version
docker-compose --version

# You should see:
# Docker version 29.5.3 or higher
# Docker Compose version v2.0 or higher
```

### 2️⃣ Start Local Services
```bash
# Navigate to project root
cd 0_AuthClaw

# Start all services (postgres, redis, opa, presidio)
docker-compose up -d

# Verify all services running
docker ps --filter "name=authclaw"

# Expected output:
# ✅ authclaw-postgres   (port 5432)
# ✅ authclaw-redis      (port 6379)
# ✅ authclaw-opa        (port 8181)
# ✅ authclaw-presidio   (port 3000)
```

### 3️⃣ Configure Environment
```bash
# Create local environment file
cp .env.local.example .env.local  # or manually create from template

# Update with your credentials (if needed)
# Default dev credentials are pre-filled
```

### 4️⃣ Verify Services Are Healthy
```bash
# PostgreSQL
psql -h localhost -U authclaw -d authclaw -c "SELECT version();"
# If psql not available, use: docker-compose exec postgres psql -U authclaw -d authclaw -c "SELECT version();"

# Redis
docker-compose exec redis redis-cli ping
# Response: PONG

# OPA (Policy Engine)
curl -s http://localhost:8181/health
# Response: {"result": true} or similar

# Presidio (PII Detection)
curl -s http://localhost:3000/health
# Response: Should respond with 200 OK
```

### 5️⃣ View Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f opa
docker-compose logs -f presidio
docker-compose logs -f redis
```

### 6️⃣ Stop Services
```bash
# Stop all containers (keep volumes)
docker-compose stop

# Stop and remove containers (but keep data)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

---

## 📁 Project Structure

```
0_AuthClaw/
├── docker-compose.yml          # Service orchestration
├── .env.local                  # Local environment config
├── IMPLEMENTATION_PLAN.md       # 15-phase delivery roadmap
│
├── backend/                    # FastAPI control plane (Phase 6)
│   ├── app/
│   ├── models/
│   ├── schemas/
│   ├── routes/
│   └── requirements.txt
│
├── gateway/                    # Go/Rust reverse proxy (Phase 3)
│   ├── main.go
│   ├── proxy.go
│   ├── redaction.go
│   └── go.mod
│
├── console/                    # Next.js admin UI (Phase 11)
│   ├── app/
│   ├── components/
│   ├── pages/
│   └── package.json
│
├── infra/                      # Infrastructure & policies
│   ├── opa/                    # OPA policy files
│   │   └── authclaw.rego
│   ├── postgres/               # Database initialization
│   │   └── schema.sql
│   └── postegres/              # (Typo in original - will be cleaned)
│
└── Project_Info/               # Documentation & specs
    ├── AuthClaw_Project_Plan.pdf
    └── AuthClaw_Board_Briefing_updated.pdf
```

---

## 🔧 Development Workflows

### Running Individual Services

**PostgreSQL CLI**
```bash
docker-compose exec postgres psql -U authclaw -d authclaw
# Then run SQL queries:
# SELECT * FROM information_schema.tables WHERE table_schema='public';
```

**Accessing OPA Playground**
```
http://localhost:8181/play
```

**Presidio API (Entity Detection)**
```bash
curl -X POST http://localhost:3000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My name is John Doe and my SSN is 123-45-6789",
    "language": "en"
  }'
```

**Redis CLI**
```bash
docker-compose exec redis redis-cli
# Then use Redis commands
```

---

## 🧪 Phase 1 Verification Checklist

Use this checklist to confirm Phase 1 is complete:

- [ ] Docker & Docker Compose installed and verified
- [ ] `docker-compose up -d` brings all 5 services online (postgres, redis, opa, presidio)
- [ ] PostgreSQL responds to connection (can run SELECT queries)
- [ ] OPA /health endpoint responds (HTTP 200)
- [ ] Presidio /health endpoint responds (HTTP 200)
- [ ] `.env.local` template created in project root
- [ ] Can view all service logs with `docker-compose logs -f`
- [ ] Services can be stopped with `docker-compose stop` and restarted with `docker-compose up -d`

---

## 🚨 Troubleshooting

### **Docker daemon not running**
```bash
# Windows: Start Docker Desktop from Start menu
# Linux/Mac: systemctl start docker
```

### **Port already in use**
```bash
# Find what's using the port (e.g., 5432)
netstat -ano | findstr :5432  # Windows
lsof -i :5432                  # Linux/Mac

# Kill the process or change docker-compose.yml port mapping
```

### **PostgreSQL connection refused**
```bash
# Wait a few seconds for postgres to start
# View logs: docker-compose logs postgres

# Force recreate:
docker-compose down && docker-compose up -d postgres
```

### **OPA not responding**
```bash
# Check logs
docker-compose logs opa

# Restart OPA
docker-compose restart opa

# The /policies mount may need time to initialize
```

### **Out of disk space**
```bash
# Clean up Docker volumes and images
docker system prune -a

# Or just the authclaw volumes
docker-compose down -v
docker-compose up -d
```

---

## 📊 Service Ports & URLs

| Service    | Port | URL                      | Purpose |
|-----------|------|--------------------------|---------|
| PostgreSQL | 5432 | postgresql://localhost   | Database |
| Redis     | 6379 | redis://localhost:6379   | Caching & sessions |
| OPA       | 8181 | http://localhost:8181    | Policy engine & playground |
| Presidio  | 3000 | http://localhost:3000    | PII/PHI detection |
| Backend   | 8000 | http://localhost:8000    | FastAPI control plane (Phase 6) |
| Gateway   | 8080 | http://localhost:8080    | LLM proxy (Phase 3) |
| Frontend  | 3000 | http://localhost:3000    | Next.js console (Phase 11) |
| ClickHouse| 8123 | http://localhost:8123    | Immutable audit logs (Phase 7) |
| Kafka     | 9092 | localhost:9092           | Event backbone (Phase 7) |

**Note**: Some ports overlap in the planning phase (Presidio & Frontend both port 3000). This will be resolved in Phase 3.

---

## 🔐 Security Notes (Dev Only)

⚠️ **These credentials are for LOCAL DEVELOPMENT ONLY**

```
- PostgreSQL User: authclaw
- PostgreSQL Pass: authclaw
- Database: authclaw
- KMS Keys: Stub (local-dev-key-id)
- Secrets: Plain text in .env.local
```

**For production**, use:
- HashiCorp Vault for secrets
- AWS KMS / Azure Key Vault for encryption keys
- Strong password generation
- Multi-factor authentication
- Encrypted environment files

---

## 📚 Next Steps

After Phase 1 is complete:

1. **Phase 2**: Design PostgreSQL schema with multi-tenant isolation
2. **Phase 3**: Build gateway reverse proxy in Go
3. **Phase 4**: Integrate Presidio redaction engine
4. **...continue through Phase 15**

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the full 15-phase roadmap.

---

## 🤝 Contributing

- All code changes go through review before merge
- Run tests before committing: `pytest` (backend), `npm test` (frontend)
- Commit messages follow: `type(scope): description`
  - Example: `feat(gateway): add OpenAI proxy adapter`
  - Example: `fix(database): tenant isolation bug`

---

## 📞 Support

- Check logs: `docker-compose logs -f [service]`
- Review IMPLEMENTATION_PLAN.md for current phase details
- Open an issue with service name and error logs

---

**Document Version**: 1.0  
**Phase**: 1 (Dev Environment & Infra Validation)  
**Last Updated**: 2026-06-12  
**Status**: ✅ Ready for use
