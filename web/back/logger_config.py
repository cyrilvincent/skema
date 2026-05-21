from logging.handlers import TimedRotatingFileHandler
import sys
import logging
import os


def config(stdout=False):
    env = os.environ.get("CHAIRE_PAAS", "dev")
    is_prod = env == "prod"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt='%y-%m-%d %H:%M:%S'
    )

    if not stdout and is_prod:
        handler = TimedRotatingFileHandler(
            filename="logs/app.log",
            when="midnight",
            interval=1,
            backupCount=10,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)
    else:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    for name in [
        "uvicorn", "uvicorn.error", "uvicorn.access",
        "gunicorn", "gunicorn.error", "gunicorn.access"
    ]:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = False






