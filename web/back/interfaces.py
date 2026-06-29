from pydantic import BaseModel


class GeoInputDTO(BaseModel):
    code: str
    id: int
    bor: str
    time: int
    exp: float
    hc: str
    resolution: str
    apl_type: str


class GeoInput2DTO(BaseModel):
    codes: list[str]
    id: int
    bor: str
    time: int
    exp: float
    hc: str
    resolution: str
    apl_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


