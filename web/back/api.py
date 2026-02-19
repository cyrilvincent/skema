import asyncio

from fastapi import FastAPI, __version__, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import config
from commune_service import CommuneService
from apl_service import APLService
from interfaces import GeoInputDTO
from fastapi.concurrency import run_in_threadpool
from sae_service import SAEService

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
sae_service: SAEService = SAEService.factory()


@app.get("/")
def root():
    print("Get /")
    return "ICIP"


@app.get("/versions")
def versions():
    print("Get /versions")
    return {"icip": config.version, "back": config.web}


@app.get("/find/{q}")
async def find(q: str):
    print(f"Get /find/{q}")
    data = await run_in_threadpool(commune_service.find, q)
    return data


@app.post("/apl/iris")
async def apl_iris(dto: GeoInputDTO):
    print(f"Get /apl/iris")
    data = await run_in_threadpool(apl_service.compute_iris,
                                   dto.code, dto.id, dto.time, dto.hc, dto.exp, dto.resolution)
    if len(data[1]["features"]) == 0:
        raise HTTPException(status_code=404, detail=f"Item not found {dto.code}")
    return data


@app.post("/apl/commune")
async def apl_commune(dto: GeoInputDTO):
    print(f"Get /apl/commune")
    data = await run_in_threadpool(apl_service.compute_commune,
                                   dto.code, dto.id, dto.time, dto.hc, dto.exp, dto.resolution)
    if len(data[1]["features"]) == 0:
        raise HTTPException(status_code=404, detail=f"Item not found {dto.code}")
    return data


@app.post("/apl/iris/csv")
async def apl_iris_csv(dto: GeoInputDTO):
    print(f"Get /apl/iris/csv")
    data = await run_in_threadpool(apl_service.compute_iris_csv, dto.code, dto.id, dto.time, dto.hc, dto.exp)
    return data.to_csv(index=False)


@app.post("/apl/commune/csv")
async def apl_commune_csv(dto: GeoInputDTO):
    print(f"Get /apl/commune/csv")
    data = await run_in_threadpool(apl_service.compute_commune_csv, dto.code, dto.id, dto.time, dto.hc, dto.exp)
    return data.to_csv(index=False)


@app.post("/sae/iris")
async def sae_iris(dto: GeoInputDTO):
    print(f"Get /sae/iris")
    data = await run_in_threadpool(sae_service.compute_sae_iris, dto.code, dto.id, dto.time, dto.hc, dto.resolution)
    if len(data[1]["features"]) == 0:
        raise HTTPException(status_code=404, detail=f"Item not found {dto.code}")
    return data


@app.post("/sae/iris/csv")
async def sae_iris_csv(dto: GeoInputDTO):
    print(f"Get /sae/iris/csv")
    data = await run_in_threadpool(sae_service.compute_sae_iris_csv, dto.code, dto.id, dto.time, dto.hc)
    return data.to_csv(index=False)

if __name__ == '__main__':
    print(f"FastAPI version: {__version__}")
    import uvicorn
    uvicorn.run("api:app", workers=1, reload=False)
