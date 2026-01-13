from fastapi import FastAPI, __version__
from fastapi.middleware.cors import CORSMiddleware
import config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # ou ["*"] pour tout autoriser (moins sécurisé)
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Autorise tous les headers
)


@app.get("/")
async def root():
    print("ICIP")
    return "ICIP"


@app.get("/versions")
async def version():
    return {"icip": config.version, "back": config.web}

if __name__ == '__main__':
    print(__version__)
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000)