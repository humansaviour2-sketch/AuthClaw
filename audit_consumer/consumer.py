"""
consumer.py — Kafka consumer that reads gateway.traffic and audit.events topics,
computes hash-chained integrity hashes, and writes records to ClickHouse.

Hardening (Phase 7):
  - Consumer group: authclaw-audit-consumer (env KAFKA_GROUP_ID)
  - Dead-letter queue: audit.deadletter — published on any processing failure
  - request_id: extracted from payload and stored in ClickHouse
"""

import json
import logging
import os
import redis
import signal
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer

from clickhouse_writer import get_client, get_prior_hash, insert_audit_event
from hash_chain import GENESIS_HASH, compute_integrity_hash, standardize_uuid, standardize_timestamp

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("audit_consumer")

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
KAFKA_TOPICS = ["gateway.traffic", "audit.events"]
# Consumer group — all replicas of this service share offset progress.
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "authclaw-audit-consumer")
KAFKA_DLQ_TOPIC = os.getenv("KAFKA_DLQ_TOPIC", "audit.deadletter")

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "authclaw")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "authclaw")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "authclaw")

REDIS_HOST = os.getenv("REDIS_HOST")
if not REDIS_HOST:
    if CLICKHOUSE_HOST == "clickhouse":
        REDIS_HOST = "redis"
    else:
        REDIS_HOST = "localhost"
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

logger.info("Initializing Redis tail-hash cache at %s:%s", REDIS_HOST, REDIS_PORT)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


# ──────────────────────────────────────────────────────────────────────────────
# Graceful shutdown
# ──────────────────────────────────────────────────────────────────────────────

_running = True


def _handle_signal(signum, _frame):
    global _running
    logger.info("Received signal %s — shutting down", signum)
    _running = False


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

# ──────────────────────────────────────────────────────────────────────────────
# DLQ publisher
# ──────────────────────────────────────────────────────────────────────────────


def _make_dlq_producer() -> KafkaProducer:
    """Create a synchronous Kafka producer for DLQ writes."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else b"",
        acks=1,
    )


def publish_to_dlq(
    producer: KafkaProducer,
    original_payload: dict,
    error_reason: str,
) -> None:
    """
    Publish a failed message to audit.deadletter.

    Envelope schema:
      original_payload  — the raw dict that failed processing
      error_reason      — human-readable exception/description
      failed_at         — ISO-8601 UTC timestamp
      tenant_id         — extracted from payload if available
      request_id        — extracted from payload if available
    """
    tenant_id = original_payload.get("tenant_id", "")
    request_id = original_payload.get("request_id", "")

    envelope = {
        "original_payload": original_payload,
        "error_reason": error_reason,
        "failed_at": datetime.now(tz=timezone.utc).isoformat(),
        "tenant_id": tenant_id,
        "request_id": request_id,
    }

    try:
        future = producer.send(
            KAFKA_DLQ_TOPIC,
            key=tenant_id or None,
            value=envelope,
        )
        future.get(timeout=5)  # synchronous confirm for reliability
        logger.warning(
            "[DLQ] Published failed event to %s (tenant=%s reason=%s)",
            KAFKA_DLQ_TOPIC,
            tenant_id,
            error_reason,
        )
    except Exception as dlq_exc:  # noqa: BLE001
        # DLQ publish itself failed — log and continue; never swallow original error silently.
        logger.error(
            "[DLQ] Failed to publish to %s: %s (original reason: %s)",
            KAFKA_DLQ_TOPIC,
            dlq_exc,
            error_reason,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Message normalisation
# ──────────────────────────────────────────────────────────────────────────────


def _parse_timestamp(raw) -> datetime:
    """Parse ISO-8601 or epoch timestamp into a UTC-aware datetime."""
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw, tz=timezone.utc)
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(tz=timezone.utc)


def normalise_event(payload: dict) -> dict:
    """
    Map a raw Kafka message payload (AuditEvent from Go gateway) to the
    ClickHouse row schema, including request_id.
    """
    return {
        "record_id": payload.get("id") or str(uuid.uuid4()),
        "tenant_id": payload.get("tenant_id", ""),
        "timestamp": _parse_timestamp(payload.get("timestamp")),
        "actor_id": payload.get("actor_id", "gateway"),
        "actor_type": payload.get("actor_type", "system"),
        "action": payload.get("action", ""),
        "policy_id": payload.get("policy_id", ""),
        "provider": payload.get("provider", ""),
        "model": payload.get("model", ""),
        "reason": payload.get("reason", ""),
        "prompt_count": int(payload.get("prompt_count", 0)),
        "request_size": int(payload.get("request_size", 0)),
        "response_status": int(payload.get("response_status", 0)),
        "duration_ms": int(payload.get("duration_ms", 0)),
        "frameworks_affected": payload.get("frameworks_affected") or [],
        "execution_trace": json.dumps(payload.get("execution_trace") or []),
        "request_id": payload.get("request_id", ""),
        "prior_hash": "",     # filled in by _process_message
        "integrity_hash": "", # filled in by _process_message
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main loop
# ──────────────────────────────────────────────────────────────────────────────


def main():
    logger.info(
        "Connecting to Kafka brokers=%s topics=%s group=%s",
        KAFKA_BROKERS,
        KAFKA_TOPICS,
        KAFKA_GROUP_ID,
    )
    consumer = KafkaConsumer(
        *KAFKA_TOPICS,
        bootstrap_servers=KAFKA_BROKERS,
        group_id=KAFKA_GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    dlq_producer = _make_dlq_producer()

    logger.info(
        "Connecting to ClickHouse host=%s port=%s db=%s",
        CLICKHOUSE_HOST,
        CLICKHOUSE_PORT,
        CLICKHOUSE_DB,
    )
    ch_client = get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        database=CLICKHOUSE_DB,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
    )

    logger.info(
        "Audit consumer started — group=%s DLQ=%s",
        KAFKA_GROUP_ID,
        KAFKA_DLQ_TOPIC,
    )

    while _running:
        # Poll with a 1-second timeout so SIGTERM is handled promptly.
        records = consumer.poll(timeout_ms=1000)
        for _tp, messages in records.items():
            for message in messages:
                try:
                    _process_message(ch_client, message.value)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to process message: %s", exc)
                    publish_to_dlq(dlq_producer, message.value or {}, str(exc))

    logger.info("Audit consumer stopped")
    dlq_producer.flush()
    dlq_producer.close()
    consumer.close()


def _process_message(ch_client, payload: dict) -> None:
    """Normalise, chain-hash, and insert a single audit event."""
    row = normalise_event(payload)
    row["record_id"] = standardize_uuid(row["record_id"])
    row["tenant_id"] = standardize_uuid(row["tenant_id"])
    row["timestamp"] = standardize_timestamp(row["timestamp"])
    tenant_id = row["tenant_id"]

    if not tenant_id:
        logger.warning("Skipping event with empty tenant_id: %s", payload.get("id"))
        return

    # Check Redis cache first to avoid ClickHouse consistency issues
    redis_key = f"audit_chain:{tenant_id}"
    prior_hash = None
    try:
        prior_hash = redis_client.get(redis_key)
    except Exception as redis_exc:
        logger.warning("Redis lookup failed, falling back to ClickHouse: %s", redis_exc)

    # Fallback to ClickHouse if cache miss or Redis error
    if not prior_hash:
        prior_hash = get_prior_hash(ch_client, tenant_id)
        logger.debug("Cache miss for tenant %s. Fetched prior_hash from ClickHouse: %s", tenant_id, prior_hash)

    row["prior_hash"] = prior_hash

    # Compute integrity hash over data fields + prior hash.
    row["integrity_hash"] = compute_integrity_hash(row, prior_hash)

    insert_audit_event(ch_client, row)

    # Update Redis cache with the new tail hash
    try:
        redis_client.set(redis_key, row["integrity_hash"])
    except Exception as redis_exc:
        logger.warning("Failed to update Redis cache: %s", redis_exc)

    logger.info(
        "Audit event persisted: record_id=%s tenant=%s action=%s request_id=%s integrity=%s prior=%s",
        row["record_id"],
        tenant_id,
        row["action"],
        row.get("request_id", ""),
        row["integrity_hash"],
        row["prior_hash"],
    )


if __name__ == "__main__":
    main()
