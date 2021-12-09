import os
import logging
import threading
import asyncio

from quart import Quart
from tortoise.contrib.quart import register_tortoise
import uvicorn
import uvloop


from api import api


if threading.current_thread() is threading.main_thread():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
else:
    asyncio.set_event_loop(uvloop.new_event_loop())

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Quart(__name__)

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
)


app.register_blueprint(api)


if __name__ == "__main__":

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", 5000)
    DB_URL = os.getenv("DB_URL", "sqlite://db.sqlite3")

    app.config["DB_URL"] = DB_URL


    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        proxy_headers=True,
        loop="asyncio",
        #timeout_keep_alive=0,
        log_level="trace",
        #reload=True
    )
