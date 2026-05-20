from logging.handlers import TimedRotatingFileHandler
import sys
import logging
import os


def config(stdout=False):
    env = os.environ['CHAIRE_PAAS'] if "CHAIRE_PAAS" in os.environ else "dev"
    print(f"CHAIRE_PAAS {env} on {sys.platform}")
    is_prod = env == "prod"
    print(f"Create logging config prod=={is_prod}")
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        datefmt='%y-%m-%d %H:%M:%S')
    if not stdout and is_prod:
        handler = TimedRotatingFileHandler(
            filename="logs/app.log",
            when="midnight",
            interval=1,  # toutes les 24h
            backupCount=10,
            encoding="utf-8",
        )
        handler.suffix = "%Y-%m-%d"
        logging.getLogger().addHandler(handler)
        # logging.getLogger("uvicorn.error").addHandler(handler)
        # logging.getLogger("uvicorn.access").addHandler(handler)





