"""Admin authentication data models and schemas."""

from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class AdminLoginRequest(BaseModel):
    """Schema for admin login request."""

    username: str = Field(..., description="Admin username")
    password: SecretStr = Field(..., description="Admin password")


class AdminTokenResponse(BaseModel):
    """Schema for admin authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str = Field(..., description="Subject (admin identifier)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
