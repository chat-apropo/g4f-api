import asyncio
import logging

from hypercorn.asyncio import serve
from hypercorn.config import Config

from backend import app
from backend.settings import settings

if __name__ == "__main__":
    config = Config()
    config.bind = [f"{settings.HOST}:{settings.PORT}"]
    config.use_reloader = settings.RELOAD
    config.worker_class = "asyncio"
    config.keep_alive_timeout = 30
    config.workers = 1
    config.access_log_format = "%(R)s %(s)s %(st)s %(D)s %({Header}o)s"
    config.accesslog = logging.getLogger("main")
    config.loglevel = "INFO" if not settings.DEBUG else "DEBUG"

    logging.getLogger("main").setLevel(config.loglevel)

    asyncio.run(serve(app, config))
