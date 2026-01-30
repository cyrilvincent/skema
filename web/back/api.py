from fastapi import FastAPI, __version__, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import config
from commune_service import CommuneService
from apl_service import APLService
from interfaces import GeoInputDTO
import numpy as np


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

commune_service: CommuneService = CommuneService.factory()
apl_service: APLService = APLService.factory()


@app.get("/")
async def root():
    print("Get /")
    return "ICIP"


@app.get("/versions")
async def versions():
    print("Get /versions")
    return {"icip": config.version, "back": config.web}


@app.get("/find/{q}")
async def find(q: str):
    print(f"Get /find/{q}")
    return commune_service.find(q)


@app.post("/apl/iris")
async def apl_iris(dto: GeoInputDTO):
    print(f"Get /apl/iris")
    data = apl_service.compute(dto.code, dto.id, dto.time, dto.hc, dto.exp, dto.resolution)
    if len(data[1]["features"]) == 0:
        raise HTTPException(status_code=404, detail=f"Item not found {dto.code}")
    debug = data[0]["years"][2020]["pop"]
    return data


if __name__ == '__main__':
    print(f"FastAPI version: {__version__}")
    import uvicorn
    uvicorn.run("api:app", reload=False)