from fastapi import FastAPI, __version__
from fastapi.middleware.cors import CORSMiddleware
import config
from commune_service import CommuneService

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # ou ["*"] pour tout autoriser (moins sécurisé)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

commune_service: CommuneService = CommuneService.factory()


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


if __name__ == '__main__':
    print(f"FastAPI version: {__version__}")
    import uvicorn
    uvicorn.run("api:app", reload=False) # Passer en SSL + enlever reload en prod