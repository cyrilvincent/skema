import datetime
import platform
import time
from fastapi import FastAPI, __version__, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from starlette.responses import JSONResponse

import config
from interfaces import GeoInputDTO
from fastapi.concurrency import run_in_threadpool
import logging
import logging.config
from charge_manager import ChargeManager
from web.back.auth_service import AuthService

is_prod = platform.system() != "Windows"
print(f"Starting FastAPI {__version__} on {platform.system()} on prod: {is_prod}")
if is_prod:
    logging.config.fileConfig("logging.ini", disable_existing_loggers=False)
else:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        datefmt='%y-%m-%d %H:%M:%S')
from commune_service import CommuneService
from apl_service import APLService
from sae_service import SAEService

logger = logging.getLogger(__name__)
logger.info(f"Starting FastAPI logger on prod: {is_prod}")
app = FastAPI(
    docs_url=None if is_prod else "/docs",
    redoc_url=None,
    openapi_url=None if is_prod else "/openapi.json",
)
cors = ["https://chaire-paas.com", "https://www.chaire-paas.com"]
if not is_prod:
    cors += ["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost", "https://localhost"]
logger.info(f"CORS: {cors}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors,
    allow_credentials=True,  # Normalement inutile tant qu'il n'y a pas JWT
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
if is_prod:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logging.error(f"Pydantic error: {request} {exc}")
        return JSONResponse(status_code=400, content={"detail": "Bad request"})

commune_service: CommuneService = CommuneService.factory()
apl_service: APLService = APLService.factory()
sae_service: SAEService = SAEService.factory()
charge_manager: ChargeManager = ChargeManager.factory()
auth_service = AuthService()

users: dict[str, dict[str, str]] = {
    "admin": {"hash": "$2b$12$uTgTW58M1/yXWsWEcwZp6edUe9EQycrdOJD5NMiBkP6CT9c2Urbwa", "role": "admin"}
}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@app.get("/")
def root():
    logger.info("Get /")
    return "ICIP"


@app.get("/versions")
def versions():
    logger.info("Get /versions")
    return {"icip": config.version, "back": config.web}


@app.get("/charge")
def charge():
    logger.info("Get /charge")
    return {"dt": str(datetime.datetime.now()),
            "charge_pc": charge_manager.charge_pc,
            "charge": charge_manager.charge,
            "req_min": charge_manager.req_min,
            "nb_req": len(charge_manager.mesures),
            "last_charge": charge_manager.last_charge}


@app.get("/sleep/{i}")
def sleep(i: float):
    logger.info(f"Get /sleep/{i}")
    start = charge_manager.start()
    time.sleep(i)
    charge_manager.stop(start)
    return charge()


@app.get("/find/{q}")
async def find(q: str):
    logger.info(f"Get /find/{q}")
    start = charge_manager.start()
    data = await run_in_threadpool(commune_service.find, q)
    duration = charge_manager.stop(start)
    log_charge("/find/", duration)
    return data


@app.post("/apl/iris")
async def apl_iris(dto: GeoInputDTO):
    logger.info(f"Get /apl/iris")
    start = charge_manager.start()
    data = await run_in_threadpool(apl_service.compute_iris,
                                   dto.code, dto.id, dto.time, dto.hc, dto.exp, dto.resolution, dto.apl_type == "APL_S")
    if len(data[1]["features"]) == 0:
        logger.warning(f"Get /apl/iris 404 {dto.code} {dto.id} {dto.time} {dto.hc} {dto.exp} {dto.resolution}")
        raise HTTPException(status_code=404, detail=f"Item not found {dto.code}")
    duration = charge_manager.stop(start)
    log_charge("/apl/iris", duration)
    return data


@app.post("/apl/commune")
async def apl_commune(dto: GeoInputDTO):
    logger.info(f"Get /apl/commune")
    start = charge_manager.start()
    data = await run_in_threadpool(apl_service.compute_commune,
                                   dto.code, dto.id, dto.time, dto.hc, dto.exp, dto.resolution, dto.apl_type == "APL_S")
    if len(data[1]["features"]) == 0:
        logger.warning(f"Get /apl/commune 404 {dto.code} {dto.id} {dto.time} {dto.hc} {dto.exp} {dto.resolution}")
        raise HTTPException(status_code=404, detail=f"Item not found {dto.code}")
    duration = charge_manager.stop(start)
    log_charge("/apl/commune", duration)
    return data


@app.post("/apl/iris/csv")
async def apl_iris_csv(dto: GeoInputDTO):
    logger.info(f"Get /apl/iris/csv")
    start = charge_manager.start()
    data = await run_in_threadpool(apl_service.compute_iris_csv,
                                   dto.code, dto.id, dto.time, dto.hc, dto.exp, dto.apl_type == "APL_S")
    duration = charge_manager.stop(start)
    log_charge("/apl/iris/csv", duration)
    return data.to_csv(index=False)


@app.post("/apl/commune/csv")
async def apl_commune_csv(dto: GeoInputDTO):
    logger.info(f"Get /apl/commune/csv")
    start = charge_manager.start()
    data = await run_in_threadpool(apl_service.compute_commune_csv,
                                   dto.code, dto.id, dto.time, dto.hc, dto.exp, dto.apl_type == "APL_S")
    duration = charge_manager.stop(start)
    log_charge("/apl/commune/csv", duration)
    return data.to_csv(index=False)


@app.post("/sae/iris")
async def sae_iris(dto: GeoInputDTO):
    logger.info(f"Get /sae/iris")
    start = charge_manager.start()
    data = await run_in_threadpool(sae_service.compute_sae_iris, dto.code, dto.id, dto.time, dto.hc, dto.resolution)
    if len(data[1]["features"]) == 0:
        logger.warning(f"Get /sae/iris 404 {dto.code} {dto.id} {dto.resolution}")
        raise HTTPException(status_code=404, detail=f"Item not found {dto.code}")
    duration = charge_manager.stop(start)
    log_charge("/sae/iris", duration)
    return data


@app.post("/sae/iris/csv")
async def sae_iris_csv(dto: GeoInputDTO):
    logger.info(f"Get /sae/iris/csv")
    start = charge_manager.start()
    data = await run_in_threadpool(sae_service.compute_sae_iris_csv, dto.code, dto.id, dto.time, dto.hc)
    duration = charge_manager.stop(start)
    log_charge("/sae/iris/csv", duration)
    return data.to_csv(index=False)


@app.post("/sae/commune")
async def sae_commune(dto: GeoInputDTO):
    logger.info(f"Get /sae/commune")
    start = charge_manager.start()
    data = await run_in_threadpool(sae_service.compute_sae_commune, dto.code, dto.id, dto.time, dto.hc, dto.resolution)
    if len(data[1]["features"]) == 0:
        logger.warning(f"Get /sae/commune 404 {dto.code} {dto.id} {dto.resolution}")
        raise HTTPException(status_code=404, detail=f"Item not found {dto.code}")
    duration = charge_manager.stop(start)
    log_charge("/sae/commune", duration)
    return data


@app.post("/sae/commune/csv")
async def sae_commune_csv(dto: GeoInputDTO):
    logger.info(f"Get /sae/commune/csv")
    start = charge_manager.start()
    data = await run_in_threadpool(sae_service.compute_sae_commune_csv, dto.code, dto.id, dto.time, dto.hc)
    duration = charge_manager.stop(start)
    log_charge("/sae/commune/csv", duration)
    return data.to_csv(index=False)


def log_charge(route: str, duration: float):
    s = f"Sending data from {route} in {int(duration)}s with charge {charge_manager.charge_pc}%"
    if charge_manager.charge_pc > charge_manager.error_alert:
        logger.error(s)
    elif charge_manager.charge_pc > charge_manager.warning_alert:
        logger.warning(s)
    else:
        logger.info(s)


def check_charge():
    ok = charge_manager.check_and_delay()
    if not ok:
        logger.error(f"To many charge {charge_manager.charge_pc}%")
        raise HTTPException(status_code=503, detail=f"To many charge {charge_manager.charge_pc}%")


if __name__ == '__main__':
    print(f"FastAPI version: {__version__}")
    import uvicorn
    uvicorn.run("api:app", workers=1, reload=False)
