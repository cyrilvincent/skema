from logging.handlers import TimedRotatingFileHandler
import sys
import logging
import os


def config(stdout=False):
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        datefmt='%y-%m-%d %H:%M:%S')






