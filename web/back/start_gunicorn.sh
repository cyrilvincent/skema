#!/bin/bash
source /home/cyrilvincent/venv/bin/activate
gunicorn api:app -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000 --workers 5 --timeout 300 --keep-alive 5 --log-level info
