import os
import threading
import logging
import asyncio
import secrets
import loguru

from quart import Quart, redirect, url_for
from quart_auth import (
    AuthManager,
    Unauthorized,
    login_required,
)
from tortoise.contrib.quart import register_tortoise
from loguru import logger
import uvloop

from endpoints.api import api
from endpoints.authwall import authwall
from loader import load_enviroment

if threading.current_thread() is threading.main_thread():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
else:
    asyncio.set_event_loop(uvloop.new_event_loop())


def create_app():
    app = Quart(__name__)
    load_enviroment()
    for key in [
        "SECRET_KEY",
        "HOST",
        "PORT",
        "DATABASE_URL",
    ]:
        app.config[key] = os.environ[key]
    AuthManager(app)

    app.register_blueprint(api)
    app.register_blueprint(authwall)

    register_tortoise(
        app,
        db_url=os.getenv("DATABASE_URL"),
        modules={"models": ["models"]},
        generate_schemas=True,
    )

    return app


app = create_app()


@app.errorhandler(Unauthorized)
async def redirect_to_login(*_: Exception):
    return redirect(url_for("authwall.login"))


@app.before_websocket
def make_session_permanent():
    logger.info("@websocket.before_request <--")


if __name__ == "__main__":

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", 5000)

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        logging=True,
    )
