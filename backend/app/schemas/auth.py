from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos de vida del access token


class UserMe(BaseModel):
    id: int
    username: str
    role: str
    tenant_id: int
    tenant_name: str
    allow_multi_device: bool
