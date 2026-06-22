# AuthClaw Gateway Service 🚪

The AuthClaw Gateway is a high-performance Go-based reverse proxy that intercepts and routes requests to LLM providers (OpenAI, Anthropic, Cohere, Azure OpenAI) under strict multi-tenant isolation, logging audit events for security and compliance.

## 🏗️ Architecture

- **Auth Middleware**: Extracts API keys from the `Authorization: Bearer <key>` header, hashes it with SHA-256, validates it against the control plane PostgreSQL database, and injects the resolved `tenant_id` into the request context.
- **Payload Normalization**: The adapter layer parses and normalizes provider-specific payloads (like OpenAI chat completions or Anthropic messages) into a generic structure to prepare for security audits and redactions.
- **Dynamic Routing**: Re-writes request headers and URLs to proxy the requests transparently to downstream endpoints.
- **Audit Logging**: Emits traffic events (including latency, prompt metrics, and status code) to stdout as a stub for the Kafka backbone.

---

## 🚀 Running Locally

### 1. Prerequisites
- Go 1.21+
- PostgreSQL database (running from root `docker-compose.yml`)

### 2. Start the Gateway
Ensure the database is running (`docker-compose up -d` in the project root). Then, start the gateway:

```bash
cd gateway
go run .
```

The gateway will start and listen on `http://localhost:8080`.

---

## 🧪 Testing

Run the full Go suite, which includes unit tests for health checks, payload extraction/re-serialization, database authentication checks, dynamic proxy routing, and payload fidelity contract checks:

```bash
cd gateway
go test -v
```

---

## 📡 Local curl Verification

To test the gateway locally:

### 1. Create a Test API Key (via Database)
Ensure you have created a tenant, a user, and a valid API key in PostgreSQL. You can verify this by running:
```sql
SELECT key_hash FROM api_keys;
```

### 2. Make a request
Run a curl command pointing to the local gateway (which will authenticate and proxy requests to target providers):

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer <your_authclaw_api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, gateway!"}
    ]
  }'
```
