import uuid
import pytest
from app.orchestrator.graph import (
    WorkflowState,
    ExecutionStatus,
    gather_evidence,
    analyze_compliance,
    generate_remediation_plan,
    awaiting_approval,
    execute_remediation,
    verify_results,
)
from app.orchestrator.worker import EphemeralWorker


def test_phase9_e2e_worker_connectors_and_callbacks():
    """
    Step 8: Verification test for Phase 9.
    Validates EphemeralWorker lifecycle, connectors, callbacks, and audit events.
    """
    # 1. Setup test state with tracking lists
    workflow_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    request_id = "req-test-phase9"

    audit_events = []
    callback_events = []

    def test_emit_audit(wf_id, t_id, req_id, transition, action, status):
        audit_events.append({
            "workflow_id": wf_id,
            "tenant_id": t_id,
            "request_id": req_id,
            "transition": transition,
            "action": action,
            "status": status,
        })

    def test_callback(provider, action, status, details):
        callback_events.append({
            "provider": provider,
            "action": action,
            "status": status,
            "details": details,
        })

    state = {
        "workflow_id": workflow_id,
        "tenant_id": tenant_id,
        "request_id": request_id,
        "framework": "HIPAA",
        "current_state": WorkflowState.GATHER_EVIDENCE.value,
        "findings": [],
        "risk_score": 0.0,
        "remediation_plan": [],
        "approval_status": "",
        "approval_id": "",
        "execution_status": ExecutionStatus.RUNNING.value,
        "execution_result": {},
        "error_message": "",
        "retry_count": 0,
        "started_at": "2026-06-16T00:00:00Z",
        "updated_at": "2026-06-16T00:00:00Z",
        "completed_at": "",
        "_emit_audit": test_emit_audit,
        "_persist_state": lambda s: None,
        "_create_approval": lambda t, w, p: "appr-123",
        "_check_approval": lambda a: "APPROVED",
    }

    # 2. Verify worker instantiation and direct helper execution
    worker = EphemeralWorker(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        request_id=request_id,
        emit_audit_fn=test_emit_audit,
        callback_fn=test_callback,
    )

    # 2a. Run scan via worker directly
    scan_results = worker.run_scan("aws", "HIPAA")
    assert len(scan_results) == 1
    assert scan_results[0]["control"] == "164.312(a)(1)"
    assert scan_results[0]["status"] == "non_compliant"

    # Verify callbacks & audits from direct run
    assert any(c["provider"] == "aws" and c["action"] == "scan" and c["status"] == "running" for c in callback_events)
    assert any(c["provider"] == "aws" and c["action"] == "scan" and c["status"] == "completed" for c in callback_events)
    assert any(a["transition"] == "WORKER_START_SCAN:AWS" for a in audit_events)
    assert any(a["transition"] == "WORKER_COMPLETE_SCAN:AWS" for a in audit_events)

    # 2b. Run remediation via worker directly
    remedy_result = worker.run_remediation("aws", "164.312(a)(1)")
    assert remedy_result["status"] == "success"
    assert remedy_result["control"] == "164.312(a)(1)"

    assert any(c["provider"] == "aws" and c["action"] == "remediate" and c["status"] == "running" for c in callback_events)
    assert any(c["provider"] == "aws" and c["action"] == "remediate" and c["status"] == "completed" for c in callback_events)
    assert any(a["transition"] == "WORKER_START_REMEDIATION:AWS" for a in audit_events)
    assert any(a["transition"] == "WORKER_COMPLETE_REMEDIATION:AWS" for a in audit_events)

    # Clear lists for clean graph execution checks
    audit_events.clear()
    callback_events.clear()

    # 3. Verify workflow nodes integration
    # GATHER_EVIDENCE node uses EphemeralWorker to scan AWS, Azure, GCP
    # Temporarily override worker inside node using state callback
    state["_emit_audit"] = test_emit_audit

    state = gather_evidence(state)
    assert state["current_state"] == WorkflowState.ANALYZE_COMPLIANCE.value
    assert len(state["findings"]) == 3  # AWS, Azure, GCP mock connector findings

    # Verify worker emitted start/complete scan audit events for AWS, Azure, GCP
    providers = ["AWS", "AZURE", "GCP"]
    for prov in providers:
        assert any(a["transition"] == f"WORKER_START_SCAN:{prov}" for a in audit_events)
        assert any(a["transition"] == f"WORKER_COMPLETE_SCAN:{prov}" for a in audit_events)

    # ANALYZE_COMPLIANCE
    state = analyze_compliance(state)
    assert state["risk_score"] == 1.0

    # GENERATE_REMEDIATION_PLAN
    state = generate_remediation_plan(state)
    assert len(state["remediation_plan"]) == 3

    # AWAITING_APPROVAL
    state = awaiting_approval(state)  # creates approval
    state = awaiting_approval(state)  # resolves approval

    # EXECUTE_REMEDIATION
    audit_events.clear()
    state = execute_remediation(state)
    assert state["current_state"] == WorkflowState.VERIFY_RESULTS.value
    assert state["execution_result"]["actions_executed"] == 3
    assert state["execution_result"]["actions_successful"] == 3

    # Verify worker emitted start/complete remediation audit events for AWS, Azure, GCP
    for prov in providers:
        assert any(a["transition"] == f"WORKER_START_REMEDIATION:{prov}" for a in audit_events)
        assert any(a["transition"] == f"WORKER_COMPLETE_REMEDIATION:{prov}" for a in audit_events)
