from pydantic import BaseModel


class GeoInputDTO(BaseModel):
    code: str
    id: int
    bor: str
    time: int
    exp: float
    hc: str


