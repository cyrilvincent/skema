from logging.handlers import TimedRotatingFileHandler
import sys
import logging


def config(stdout=False):
    print("Create logging config")
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        datefmt='%y-%m-%d %H:%M:%S')
    if not stdout and sys.platform != "win32":
        handler = TimedRotatingFileHandler(
            filename="logs/app.log",
            when="midnight",
            interval=1,  # toutes les 24h
            backupCount=10,
            encoding="utf-8",
        )
        handler.suffix = "%Y-%m-%d"
        logger = logging.getLogger()
        logger.addHandler(handler)

