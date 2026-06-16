"""
Phase 8: Compliance Workflow API Endpoints

Provides REST endpoints for managing LangGraph compliance workflows:
  POST /v1/workflows       - Start a new compliance workflow
  GET  /v1/workflows/{id}  - Get workflow status
  POST /v1/workflows/{id}/resume - Resume a paused workflow
  POST /v1/workflows/{id}/approve - Approve a workflow's remediation plan
  POST /v1/workflows/recover - Recover interrupted workflows
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_tenant_db, require_scopes
from app.db.models import PendingApproval, ComplianceWorkflow
from app.orchestrator.runner import ComplianceWorkflowRunner
from datetime import datetime, timezone

logger = logging.getLogger("api.workflows")
router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────────
# Request/Response schemas
# ──────────────────────────────────────────────────────────────────────────────


class WorkflowCreateRequest(BaseModel):
    framework: str = Field(..., description="Compliance framework: HIPAA, GDPR, SOC2")
    request_id: Optional[str] = Field(None, description="Optional request correlation ID")


class WorkflowResponse(BaseModel):
    workflow_id: str
    tenant_id: str
    framework: str
    current_state: str
    execution_status: str
    risk_score: Optional[float] = None
    findings: Optional[list] = None
    remediation_plan: Optional[list] = None
    approval_status: Optional[str] = None
    approval_id: Optional[str] = None
    execution_result: Optional[dict] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = 0
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


class RecoveryResponse(BaseModel):
    recovered: int
    results: list


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.post("", response_model=WorkflowResponse, status_code=201)
def create_workflow(
    body: WorkflowCreateRequest,
    request: Request,
    db: Session = Depends(get_tenant_db),
    _auth=require_scopes(["write"]),
):
    """Start a new compliance workflow."""
    tenant_id = str(request.state.tenant_id)
    framework = body.framework.upper()

    if framework not in ("HIPAA", "GDPR", "SOC2"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported framework: {framework}. Must be HIPAA, GDPR, or SOC2.",
        )

    try:
        runner = ComplianceWorkflowRunner(db)
        result = runner.start(
            tenant_id=tenant_id,
            framework=framework,
            request_id=body.request_id,
        )
        return WorkflowResponse(**result)
    except Exception as exc:
        logger.error("Failed to create workflow: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: str,
    request: Request,
    db: Session = Depends(get_tenant_db),
    _auth=require_scopes(["read"]),
):
    """Get workflow status by ID."""
    tenant_id = str(request.state.tenant_id)

    runner = ComplianceWorkflowRunner(db)
    result = runner.get_status(workflow_id, tenant_id)

    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowResponse(**result)


@router.post("/{workflow_id}/resume", response_model=WorkflowResponse)
def resume_workflow(
    workflow_id: str,
    request: Request,
    db: Session = Depends(get_tenant_db),
    _auth=require_scopes(["write"]),
):
    """Resume a paused workflow (typically after approval)."""
    tenant_id = str(request.state.tenant_id)

    try:
        runner = ComplianceWorkflowRunner(db)
        result = runner.resume(workflow_id, tenant_id)
        return WorkflowResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to resume workflow: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{workflow_id}/approve", response_model=WorkflowResponse)
def approve_workflow(
    workflow_id: str,
    request: Request,
    db: Session = Depends(get_tenant_db),
    _auth=require_scopes(["admin"]),
):
    """Approve a workflow's remediation plan and resume execution."""
    tenant_id = str(request.state.tenant_id)

    runner = ComplianceWorkflowRunner(db)
    status = runner.get_status(workflow_id, tenant_id)

    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if status.get("execution_status") != "PAUSED":
        raise HTTPException(
            status_code=400,
            detail=f"Workflow is not awaiting approval (status={status.get('execution_status')})",
        )

    # Update approval to APPROVED
    approval_id = status.get("approval_id")
    if approval_id:
        approval = db.query(PendingApproval).filter(
            PendingApproval.id == uuid.UUID(approval_id),
        ).first()
        if approval:
            approval.status = "APPROVED"
            approval.approver_id = request.state.user_id
            approval.approved_at = datetime.now(timezone.utc)
            
            # Synchronize workflow.approval_status
            wf = db.query(ComplianceWorkflow).filter(
                ComplianceWorkflow.workflow_id == workflow_id
            ).first()
            if wf:
                wf.approval_status = "APPROVED"
                
            db.commit()

    # Resume workflow
    try:
        result = runner.resume(workflow_id, tenant_id)
        return WorkflowResponse(**result)
    except Exception as exc:
        logger.error("Failed to approve/resume workflow: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recover", response_model=RecoveryResponse)
def recover_workflows(
    request: Request,
    db: Session = Depends(get_tenant_db),
    _auth=require_scopes(["admin"]),
):
    """Recover all interrupted workflows for the current tenant."""
    tenant_id = str(request.state.tenant_id)

    runner = ComplianceWorkflowRunner(db)
    results = runner.recover_interrupted(tenant_id)

    return RecoveryResponse(
        recovered=len([r for r in results if r["status"] == "recovered"]),
        results=results,
    )
