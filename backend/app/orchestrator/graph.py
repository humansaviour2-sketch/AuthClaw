"""
Phase 8: LangGraph Compliance Orchestrator

Workflow states:
  GATHER_EVIDENCE → ANALYZE_COMPLIANCE → GENERATE_REMEDIATION_PLAN
  → AWAITING_APPROVAL → EXECUTE_REMEDIATION → VERIFY_RESULTS → COMPLETE

All state transitions emit audit events through the existing Kafka pipeline.
Workflow state is persisted to PostgreSQL for crash recovery.
"""

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional, TypedDict

from langgraph.graph import StateGraph, END
from app.orchestrator.worker import EphemeralWorker

logger = logging.getLogger("orchestrator")


# ──────────────────────────────────────────────────────────────────────────────
# Workflow States
# ──────────────────────────────────────────────────────────────────────────────


class WorkflowState(str, Enum):
    GATHER_EVIDENCE = "GATHER_EVIDENCE"
    ANALYZE_COMPLIANCE = "ANALYZE_COMPLIANCE"
    GENERATE_REMEDIATION_PLAN = "GENERATE_REMEDIATION_PLAN"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTE_REMEDIATION = "EXECUTE_REMEDIATION"
    VERIFY_RESULTS = "VERIFY_RESULTS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ExecutionStatus(str, Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ──────────────────────────────────────────────────────────────────────────────
# Graph State Schema
# ──────────────────────────────────────────────────────────────────────────────


class ComplianceState(TypedDict, total=False):
    """LangGraph state schema for the compliance workflow."""
    workflow_id: str
    tenant_id: str
    request_id: str
    framework: str  # GDPR, HIPAA, SOC2
    current_state: str
    findings: list[dict]
    risk_score: float
    remediation_plan: list[dict]
    approval_status: str
    approval_id: str
    execution_status: str
    execution_result: dict
    error_message: str
    retry_count: int
    started_at: str
    updated_at: str
    completed_at: str
    # Callbacks injected by the runner
    _emit_audit: Any  # callable(workflow_id, tenant_id, request_id, transition, action, status)
    _persist_state: Any  # callable(state) -> None
    _create_approval: Any  # callable(tenant_id, workflow_id, plan) -> approval_id
    _check_approval: Any  # callable(approval_id) -> status string


# ──────────────────────────────────────────────────────────────────────────────
# Node Implementations
# ──────────────────────────────────────────────────────────────────────────────


def gather_evidence(state: ComplianceState) -> ComplianceState:
    """GATHER_EVIDENCE: Collect compliance evidence for the target framework."""
    logger.info("[%s] Gathering evidence for %s", state["workflow_id"], state["framework"])
    
    framework = state["framework"]
    
    worker = EphemeralWorker(
        tenant_id=state["tenant_id"],
        workflow_id=state["workflow_id"],
        request_id=state.get("request_id", ""),
        emit_audit_fn=state.get("_emit_audit"),
    )
    
    findings = []
    # Query each mock cloud connector via the ephemeral worker
    for provider in ["aws", "azure", "gcp"]:
        try:
            prov_findings = worker.run_scan(provider, framework)
            findings.extend(prov_findings)
        except Exception as e:
            logger.error("Failed scan for provider %s: %s", provider, e)
    
    emit = state.get("_emit_audit")
    if emit:
        emit(state["workflow_id"], state["tenant_id"], state.get("request_id", ""),
             "GATHER_EVIDENCE→ANALYZE_COMPLIANCE", "gather_evidence", "completed")
    
    persist = state.get("_persist_state")
    new_state = {
        **state,
        "findings": findings,
        "current_state": WorkflowState.ANALYZE_COMPLIANCE.value,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if persist:
        persist(new_state)
    return new_state


def analyze_compliance(state: ComplianceState) -> ComplianceState:
    """ANALYZE_COMPLIANCE: Score findings and determine risk level."""
    logger.info("[%s] Analyzing compliance for %s", state["workflow_id"], state["framework"])
    
    findings = state.get("findings", [])
    non_compliant = [f for f in findings if f.get("status") == "non_compliant"]
    total = len(findings) if findings else 1
    
    # Risk score: 0.0 (fully compliant) to 1.0 (fully non-compliant)
    risk_score = round(len(non_compliant) / total, 2) if total > 0 else 0.0
    
    emit = state.get("_emit_audit")
    if emit:
        emit(state["workflow_id"], state["tenant_id"], state.get("request_id", ""),
             "ANALYZE_COMPLIANCE→GENERATE_REMEDIATION_PLAN", "analyze_compliance", "completed")
    
    persist = state.get("_persist_state")
    new_state = {
        **state,
        "risk_score": risk_score,
        "current_state": WorkflowState.GENERATE_REMEDIATION_PLAN.value,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if persist:
        persist(new_state)
    return new_state


def generate_remediation_plan(state: ComplianceState) -> ComplianceState:
    """GENERATE_REMEDIATION_PLAN: Create remediation actions for non-compliant findings."""
    logger.info("[%s] Generating remediation plan", state["workflow_id"])
    
    findings = state.get("findings", [])
    non_compliant = [f for f in findings if f.get("status") == "non_compliant"]
    
    # Stubbed plan generation — in production this would call an LLM
    # via the AuthClaw gateway (Gemini 2.5 Flash-Lite through the proxy).
    plan = []
    for finding in non_compliant:
        plan.append({
            "finding_control": finding["control"],
            "action": f"Remediate: {finding['description']}",
            "priority": "high" if state.get("risk_score", 0) > 0.5 else "medium",
            "estimated_effort": "2 hours",
            "steps": [f"Review {finding['control']}", "Apply fix", "Verify compliance"],
        })
    
    # Scans execute without immediate approval, completing the scan stage
    next_state = WorkflowState.COMPLETE.value
    
    emit = state.get("_emit_audit")
    if emit:
        emit(state["workflow_id"], state["tenant_id"], state.get("request_id", ""),
             "GENERATE_REMEDIATION_PLAN→COMPLETE", "generate_plan", "completed")
    
    persist = state.get("_persist_state")
    new_state = {
        **state,
        "remediation_plan": plan,
        "current_state": next_state,
        "execution_status": ExecutionStatus.COMPLETED.value,
        "completed_at": datetime.now(tz=timezone.utc).isoformat(),
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if persist:
        persist(new_state)
    return new_state


def awaiting_approval(state: ComplianceState) -> ComplianceState:
    """AWAITING_APPROVAL: Create or check a HITL approval request."""
    logger.info("[%s] Awaiting approval", state["workflow_id"])
    
    approval_id = state.get("approval_id")
    
    if not approval_id:
        # First entry: create the approval request
        create_fn = state.get("_create_approval")
        if create_fn:
            approval_id = create_fn(
                state["tenant_id"],
                state["workflow_id"],
                state.get("remediation_plan", []),
            )
        else:
            # No approval function — auto-approve for testing
            approval_id = str(uuid.uuid4())
        
        emit = state.get("_emit_audit")
        if emit:
            emit(state["workflow_id"], state["tenant_id"], state.get("request_id", ""),
                 "AWAITING_APPROVAL", "create_approval", "pending")
        
        persist = state.get("_persist_state")
        new_state = {
            **state,
            "approval_id": approval_id,
            "approval_status": "PENDING",
            "execution_status": ExecutionStatus.PAUSED.value,
            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        if persist:
            persist(new_state)
        return new_state
    
    # Subsequent entry: check approval status
    check_fn = state.get("_check_approval")
    status = "PENDING"
    if check_fn:
        status = check_fn(approval_id)
    
    if status == "APPROVED":
        next_state = WorkflowState.EXECUTE_REMEDIATION.value
        exec_status = ExecutionStatus.RUNNING.value
    elif status == "REJECTED":
        next_state = WorkflowState.COMPLETE.value
        exec_status = ExecutionStatus.COMPLETED.value
    elif status == "EXPIRED":
        next_state = WorkflowState.COMPLETE.value
        exec_status = ExecutionStatus.COMPLETED.value
    else:  # PENDING — stay paused
        return {**state, "approval_status": status,
                "execution_status": ExecutionStatus.PAUSED.value,
                "updated_at": datetime.now(tz=timezone.utc).isoformat()}
    
    emit = state.get("_emit_audit")
    if emit:
        emit(state["workflow_id"], state["tenant_id"], state.get("request_id", ""),
             f"AWAITING_APPROVAL→{next_state}", "approval_resolved", status.lower())
    
    persist = state.get("_persist_state")
    new_state = {
        **state,
        "approval_status": status,
        "current_state": next_state,
        "execution_status": exec_status,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if persist:
        persist(new_state)
    return new_state


def execute_remediation(state: ComplianceState) -> ComplianceState:
    """EXECUTE_REMEDIATION: Apply the approved remediation plan."""
    logger.info("[%s] Executing remediation", state["workflow_id"])
    
    plan = state.get("remediation_plan", [])
    
    worker = EphemeralWorker(
        tenant_id=state["tenant_id"],
        workflow_id=state["workflow_id"],
        request_id=state.get("request_id", ""),
        emit_audit_fn=state.get("_emit_audit"),
    )
    
    details = []
    actions_successful = 0
    actions_failed = 0
    
    for action in plan:
        control = action.get("finding_control", "")
        # Map control to provider
        provider = None
        control_lower = control.lower()
        if "aws" in control_lower or "164.312(a)" in control_lower or "art.25" in control_lower:
            provider = "aws"
        elif "azure" in control_lower or "164.312(e)" in control_lower or "art.32" in control_lower:
            provider = "azure"
        elif "gcp" in control_lower or "164.312(d)" in control_lower or "art.30" in control_lower:
            provider = "gcp"
        
        if provider:
            try:
                res = worker.run_remediation(provider, control)
                details.append(res)
                actions_successful += 1
            except Exception as e:
                details.append({
                    "connector": provider.upper(),
                    "control": control,
                    "status": "failed",
                    "details": str(e)
                })
                actions_failed += 1
        else:
            details.append({
                "connector": "unknown",
                "control": control,
                "status": "failed",
                "details": f"Unknown provider for control {control}"
            })
            actions_failed += 1
            
    result = {
        "actions_executed": len(plan),
        "actions_successful": actions_successful,
        "actions_failed": actions_failed,
        "details": details,
    }
    
    emit = state.get("_emit_audit")
    if emit:
        emit(state["workflow_id"], state["tenant_id"], state.get("request_id", ""),
             "EXECUTE_REMEDIATION→VERIFY_RESULTS", "execute_remediation", "completed")
    
    persist = state.get("_persist_state")
    new_state = {
        **state,
        "execution_result": result,
        "current_state": WorkflowState.VERIFY_RESULTS.value,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if persist:
        persist(new_state)
    return new_state


def verify_results(state: ComplianceState) -> ComplianceState:
    """VERIFY_RESULTS: Verify that remediation was successful."""
    logger.info("[%s] Verifying results", state["workflow_id"])
    
    result = state.get("execution_result", {})
    failed = result.get("actions_failed", 0)
    
    if failed > 0:
        # Retry logic
        retry_count = state.get("retry_count", 0)
        if retry_count < 3:
            emit = state.get("_emit_audit")
            if emit:
                emit(state["workflow_id"], state["tenant_id"], state.get("request_id", ""),
                     "VERIFY_RESULTS→EXECUTE_REMEDIATION", "verify_results", "retry")
            persist = state.get("_persist_state")
            new_state = {
                **state,
                "current_state": WorkflowState.EXECUTE_REMEDIATION.value,
                "retry_count": retry_count + 1,
                "updated_at": datetime.now(tz=timezone.utc).isoformat(),
            }
            if persist:
                persist(new_state)
            return new_state
        # Max retries exceeded
        emit = state.get("_emit_audit")
        if emit:
            emit(state["workflow_id"], state["tenant_id"], state.get("request_id", ""),
                 "VERIFY_RESULTS→FAILED", "verify_results", "max_retries_exceeded")
        persist = state.get("_persist_state")
        new_state = {
            **state,
            "current_state": WorkflowState.FAILED.value,
            "execution_status": ExecutionStatus.FAILED.value,
            "error_message": "Max retries exceeded during verification",
            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        if persist:
            persist(new_state)
        return new_state
    
    emit = state.get("_emit_audit")
    if emit:
        emit(state["workflow_id"], state["tenant_id"], state.get("request_id", ""),
             "VERIFY_RESULTS→COMPLETE", "verify_results", "passed")
    
    persist = state.get("_persist_state")
    now = datetime.now(tz=timezone.utc).isoformat()
    new_state = {
        **state,
        "current_state": WorkflowState.COMPLETE.value,
        "execution_status": ExecutionStatus.COMPLETED.value,
        "updated_at": now,
        "completed_at": now,
    }
    if persist:
        persist(new_state)
    return new_state


# ──────────────────────────────────────────────────────────────────────────────
# Routing logic
# ──────────────────────────────────────────────────────────────────────────────


def route_after_plan(state: ComplianceState) -> str:
    """Route after GENERATE_REMEDIATION_PLAN based on whether a plan exists."""
    if state.get("current_state") == WorkflowState.COMPLETE.value:
        return END
    return "awaiting_approval"


def route_after_approval(state: ComplianceState) -> str:
    """Route after AWAITING_APPROVAL based on approval status."""
    status = state.get("approval_status", "PENDING")
    if status == "APPROVED":
        return "execute_remediation"
    if status in ("REJECTED", "EXPIRED"):
        return END
    # PENDING — workflow pauses here
    return END  # Will be resumed later


def route_after_verify(state: ComplianceState) -> str:
    """Route after VERIFY_RESULTS — retry or complete."""
    cs = state.get("current_state", "")
    if cs == WorkflowState.EXECUTE_REMEDIATION.value:
        return "execute_remediation"  # retry
    if cs == WorkflowState.FAILED.value:
        return END
    return END  # COMPLETE


# ──────────────────────────────────────────────────────────────────────────────
# Build the graph
# ──────────────────────────────────────────────────────────────────────────────


def build_compliance_graph() -> StateGraph:
    """Build and compile the LangGraph compliance workflow."""
    graph = StateGraph(ComplianceState)

    # Add nodes
    graph.add_node("gather_evidence", gather_evidence)
    graph.add_node("analyze_compliance", analyze_compliance)
    graph.add_node("generate_remediation_plan", generate_remediation_plan)
    graph.add_node("awaiting_approval", awaiting_approval)
    graph.add_node("execute_remediation", execute_remediation)
    graph.add_node("verify_results", verify_results)

    # Set entry point
    graph.set_entry_point("gather_evidence")

    # Edges
    graph.add_edge("gather_evidence", "analyze_compliance")
    graph.add_edge("analyze_compliance", "generate_remediation_plan")
    graph.add_conditional_edges("generate_remediation_plan", route_after_plan,
                                {"awaiting_approval": "awaiting_approval", END: END})
    graph.add_conditional_edges("awaiting_approval", route_after_approval,
                                {"execute_remediation": "execute_remediation", END: END})
    graph.add_edge("execute_remediation", "verify_results")
    graph.add_conditional_edges("verify_results", route_after_verify,
                                {"execute_remediation": "execute_remediation", END: END})

    return graph.compile()
