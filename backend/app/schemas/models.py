"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class TenantCreate(BaseModel):
    """Schema for creating a tenant"""
    name: str = Field(..., min_length=1, max_length=255)
    tier: str = Field(default="starter", pattern="^(starter|pro|enterprise)$")


class TenantResponse(BaseModel):
    """Schema for tenant response"""
    id: UUID
    name: str
    tier: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="viewer", pattern="^(admin|operator|viewer)$")


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    email: str
    role: str
    mfa_enabled: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    """Schema for creating an API key"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: List[str] = Field(default=["read"], min_items=1)


class APIKeyResponse(BaseModel):
    """Schema for API key response (doesn't include the actual key)"""
    id: UUID
    name: str
    scopes: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PolicyCreate(BaseModel):
    """Schema for creating a policy"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    policy_yaml: str = Field(..., min_length=10)


class PolicyResponse(BaseModel):
    """Schema for policy response"""
    id: UUID
    name: str
    version: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PolicyDetailResponse(BaseModel):
    """Schema for detailed policy response with yaml"""
    id: UUID
    name: str
    description: Optional[str] = None
    policy_yaml: str
    version: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True



class GatewayConfigCreate(BaseModel):
    """Schema for gateway configuration"""
    name: str = Field(..., min_length=1, max_length=255)
    provider: str = Field(..., pattern="^(openai|anthropic|cohere|azure_openai)$")
    endpoint: str = Field(..., min_length=1, max_length=512)
    model_whitelist: Optional[List[str]] = None
    redaction_strategy: str = Field(default="mask", pattern="^(mask|hash|synthetic)$")


class GatewayConfigResponse(BaseModel):
    """Schema for gateway config response"""
    id: UUID
    name: str
    provider: str
    endpoint: str
    redaction_strategy: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RedactionTokenMapResponse(BaseModel):
    """Schema for redaction token mapping response"""
    id: UUID
    token_value: str
    token_hash: str
    original_value: str
    strategy: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogMetadataResponse(BaseModel):
    """Schema for audit log metadata response"""
    id: UUID
    record_id: UUID
    actor_id: Optional[UUID] = None
    action: str
    frameworks_affected: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    status_code: int
    error_type: Optional[str] = None
