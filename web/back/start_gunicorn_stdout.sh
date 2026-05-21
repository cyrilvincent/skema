#!/bin/bash
source /home/cyrilvincent/venv/bin/activate
gunicorn api:app -k uvicorn.workers.UvicornWorker --bind unix:/tmp/gunicorn.sock --workers 5 --timeout 300 --keep-alive 5 --log-level info

# pkill gunicorn
