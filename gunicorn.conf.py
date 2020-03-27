import multiprocessing
import os

LOGGING_INI = os.getenv("LOGGING_INI")
ENVIRONMENT = os.getenv("ENVIRONMENT") or "development"

bind = "0.0.0.0:3000"

debug = ENVIRONMENT == "development"
reload = debug

logconfig = LOGGING_INI
errorlog = "-"
loglevel = "INFO"

worker_class = "gevent"

if (ENVIRONMENT == "production"):
    workers = multiprocessing.cpu_count() * 2 + 1
