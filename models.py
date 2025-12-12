from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# Request/Response Models
class OrganizationCreate(BaseModel):
    """Request model for creating organization"""
    organization_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)


class OrganizationUpdate(BaseModel):
    """Request model for updating organization"""
    organization_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)


class OrganizationDelete(BaseModel):
    """Request model for deleting organization"""
    organization_name: str


class AdminLogin(BaseModel):
    """Request model for admin login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Response model for login"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    admin_id: str
    organization_id: str
    email: str
