#!/bin/bash
source /home/cyrilvincent/venv/bin/activate
gunicorn api:app -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000 --workers 1 --timeout 300 --keep-alive 5 --log-level info --log-config logging.ini

# gunicorn api:app -k uvicorn.workers.UvicornWorker --bind unix:/tmp/gunicorn.sock --workers 5 --timeout 300 --keep-alive 5 --log-level info --log-config logging.ini
#--error-logfile logs/gunicorn-error.log --access-logfile logs/gunicorn-access.log

# gunicorn api:app -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000 --workers 5 --timeout 300 --keep-alive 5 --log-level info

# ps aux | grep gunicorn
# kill -2 pid
