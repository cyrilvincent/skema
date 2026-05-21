#!/bin/bash
source /home/cyrilvincent/venv/bin/activate
gunicorn api:app -k uvicorn.workers.UvicornWorker --bind unix:/tmp/gunicorn.sock --workers5 --timeout 300 --keep-alive 5 --log-level info

# ps aux | grep gunicorn
# kill -2 pid
