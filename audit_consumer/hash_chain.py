"""
hash_chain.py — SHA-256 hash chaining for immutable audit records.

Each audit record includes:
  - prior_hash: the integrity_hash of the immediately preceding record for this tenant
  - integrity_hash: SHA256(canonical_json + prior_hash)

The chain starts with prior_hash = "GENESIS" for the first record per tenant.
"""

import hashlib
import json
from typing import Any


GENESIS_HASH = "GENESIS"


import uuid
from datetime import datetime, timezone

def standardize_uuid(val: Any) -> str:
    if not val:
        return ""
    try:
        return str(uuid.UUID(str(val)))
    except ValueError:
        return str(val)

def standardize_timestamp(ts: Any) -> str:
    if isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    elif isinstance(ts, str):
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    elif isinstance(ts, datetime):
        dt = ts
    else:
        dt = datetime.now(tz=timezone.utc)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    
    ms = dt.microsecond // 1000
    return f"{dt.strftime('%Y-%m-%dT%H:%M:%S')}.{ms:03d}Z"

def canonical_json(record: dict[str, Any]) -> str:
    """Return a deterministic JSON representation of the record (excluding chain fields)."""
    record_id = standardize_uuid(record.get("record_id"))
    tenant_id = standardize_uuid(record.get("tenant_id"))
    timestamp_str = standardize_timestamp(record.get("timestamp"))
    
    clean = {
        "record_id": record_id,
        "tenant_id": tenant_id,
        "timestamp": timestamp_str,
        "actor_id": str(record.get("actor_id", "")),
        "actor_type": str(record.get("actor_type", "")),
        "action": str(record.get("action", "")),
        "policy_id": str(record.get("policy_id", "")),
        "provider": str(record.get("provider", "")),
        "model": str(record.get("model", "")),
        "reason": str(record.get("reason", "")),
        "prompt_count": int(record.get("prompt_count", 0)),
        "request_size": int(record.get("request_size", 0)),
        "response_status": int(record.get("response_status", 0)),
        "duration_ms": int(record.get("duration_ms", 0)),
        "frameworks_affected": sorted(list(record.get("frameworks_affected") or [])),
        "execution_trace": str(record.get("execution_trace", "[]")),
        "request_id": str(record.get("request_id", "")),
    }
    return json.dumps(clean, sort_keys=True, separators=(",", ":"))


def compute_integrity_hash(record: dict[str, Any], prior_hash: str) -> str:
    """Compute SHA-256(canonical_json + prior_hash)."""
    data = canonical_json(record) + prior_hash
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def verify_chain(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Verify the hash chain across a list of records ordered by (tenant_id, timestamp, record_id).

    Returns a list of dicts with fields:
      record_id, tenant_id, valid (bool), expected_hash, actual_hash
    """
    results = []
    prior_by_tenant: dict[str, str] = {}

    for record in records:
        tenant_id = record.get("tenant_id", "")
        prior_hash = prior_by_tenant.get(tenant_id, GENESIS_HASH)

        expected = compute_integrity_hash(record, prior_hash)
        actual = record.get("integrity_hash", "")

        results.append(
            {
                "record_id": record.get("record_id", ""),
                "tenant_id": tenant_id,
                "valid": expected == actual,
                "expected_hash": expected,
                "actual_hash": actual,
            }
        )
        # Advance prior hash regardless of validity (continue checking downstream).
        prior_by_tenant[tenant_id] = actual or expected

    return results
