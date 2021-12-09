import os
import threading
import logging
import asyncio

from quart import Quart

from tortoise.contrib.quart import register_tortoise


import uvloop


if threading.current_thread() is threading.main_thread():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
else:
    asyncio.set_event_loop(uvloop.new_event_loop())


logging.basicConfig(level=logging.DEBUG)


app = Quart(__name__)


from api import api

app.register_blueprint(api)


register_tortoise(
    app,
    db_url="sqlite://./db/db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
)


if __name__ == "__main__":

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", 5000)

    app.run(
        host=HOST,
        port=PORT,
    )
