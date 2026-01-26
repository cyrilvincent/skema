from fastapi import FastAPI, __version__
from fastapi.middleware.cors import CORSMiddleware
import config
from commune_service import CommuneService
from apl_service import APLService
from interfaces import GeoInputDTO

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # ou ["*"] pour tout autoriser (moins sécurisé)
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
    return apl_service.compute(dto.code, dto.id, dto.time, dto.hc, dto.exp)


if __name__ == '__main__':
    print(f"FastAPI version: {__version__}")
    import uvicorn
    uvicorn.run("api:app", reload=False) # Passer en SSL + enlever reload en prod