import os
import threading
import logging
import asyncio
import secrets

from quart import Quart, session
from quart_cors import cors, route_cors
from tortoise.contrib.quart import register_tortoise
from loguru import logger

import uvloop


if threading.current_thread() is threading.main_thread():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
else:
    asyncio.set_event_loop(uvloop.new_event_loop())


#logging.basicConfig(level=logging.DEBUG)


app = Quart(__name__)
app._logger = logger

app.secret_key = secrets.token_urlsafe(16)

from api import api

app.register_blueprint(api)
api = cors(api)

#@app.before_request
#def make_session_permanent():
#    session.permanent = True


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
