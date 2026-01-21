from fastapi import FastAPI, __version__
from fastapi.middleware.cors import CORSMiddleware
import config
from web.back.commune_service import CommuneService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # ou ["*"] pour tout autoriser (moins sécurisé)
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Autorise tous les headers
)

commune_service = CommuneService()


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
    print(__version__)
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) # Passer en SSL + enlever reload en prod