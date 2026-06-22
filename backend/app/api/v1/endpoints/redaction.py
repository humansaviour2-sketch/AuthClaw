from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.models import RedactionToken
from app.schemas.models import RedactionTokenMapResponse
from app.core.auth import get_tenant_db, require_scopes
from app.core.crypto import decrypt_deterministic

router = APIRouter()


@router.get("/{id}/tokenization-map", response_model=List[RedactionTokenMapResponse], dependencies=[require_scopes(["read"])])
def get_tokenization_map(
    id: UUID,
    request: Request,
    db: Session = Depends(get_tenant_db)
):
    """Retrieve tokenization mapping for the tenant, decrypting original values dynamically"""
    tenant_id = request.state.tenant_id

    # Strict check to verify request context tenant matches URL parameter tenant
    if str(id) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cross-tenant access is not allowed"
        )

    tokens = db.query(RedactionToken).filter(RedactionToken.tenant_id == tenant_id).all()

    response = []
    for t in tokens:
        try:
            decrypted = decrypt_deterministic(t.original_value)
        except Exception as dec_err:
            print(f"[WARN] Failed to decrypt token value for mapping ID {t.id}: {dec_err}")
            decrypted = "[Decryption Failed]"

        response.append(
            RedactionTokenMapResponse(
                id=t.id,
                token_value=t.token_value,
                token_hash=t.token_hash,
                original_value=decrypted,
                strategy=t.strategy,
                created_at=t.created_at
            )
        )

    return response
