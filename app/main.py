# template https://github.com/jamescurtin/demo-cookiecutter-flask/blob/master/my_flask_app/app.py

import os
import threading
import logging
import asyncio
import secrets
import loguru
import sys

from quart_auth import AuthUser

from quart import (
    Quart,
    redirect,
    url_for,
    render_template,
    Response,
    jsonify,
    make_response,
)
from quart_auth import (
    AuthManager,
    Unauthorized,
    login_required,
)
from tortoise.contrib.quart import register_tortoise
from loguru import logger
import uvloop
from .extensions import bcrypt, auth_manager

from app.endpoints.api import api
from app.user.views import auth
from app.loader import load_enviroment
from app.user.models import User


if threading.current_thread() is threading.main_thread():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
else:
    asyncio.set_event_loop(uvloop.new_event_loop())


def create_app():
    app = Quart(__name__.split(".")[0])
    load_enviroment()
    for key in [
        "SECRET_KEY",
        "HOST",
        "PORT",
        "DATABASE_URL",
        "BCRYPT_LOG_ROUNDS",
        "CACHE_TYPE",
        "QUART_ENV",
    ]:
        app.config[key] = os.environ[key]
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    configure_logger(app)
    return app


def register_extensions(app):
    """Register extensions."""
    bcrypt.init_app(app)
    auth_manager.init_app(app)
    auth_manager.user_class = User
    register_tortoise(
        app,
        db_url=os.getenv("DATABASE_URL"),
        modules={"models": ["app.user.models"]},
        generate_schemas=True,
    )
    return None


def register_blueprints(app):
    """Register blueprints."""
    app.register_blueprint(api)
    app.register_blueprint(auth)


def register_errorhandlers(app):
    """Register error handlers."""

    async def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        return await render_template(f"{error_code}.html"), error_code

    for errcode in [
        401,
    ]:  # 404, 500
        app.errorhandler(errcode)(render_error)
    return None

    """
    @app.errorhandler(Unauthorized)
    async def redirect_to_login(*_: Exception):
        return redirect(url_for("authwall.login"))
    """


def configure_logger(app):
    """Configure loggers."""
    handler = logging.StreamHandler(sys.stdout)
    if not app.logger.handlers:
        app.logger.addHandler(handler)


app = create_app()

# prevent cached responses
@app.after_request
async def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, max-age=0"
    return r


@app.errorhandler(405)
@app.errorhandler(403)
# @app.errorhandler(401)
async def forbidden():
    return Response(
        jsonify(
            {
                "error": {
                    "code": 403,
                    "message": "The request is missing a valid API key.",
                    "errors": [
                        {
                            "message": "The request is missing a valid API key.",
                            "domain": "global",
                            "reason": "forbidden",
                        }
                    ],
                    "status": "PERMISSION_DENIED",
                }
            }
        ),
        status=403,  # HTTP Status 403 Forbidden
        headers={"WWW-Authenticate": "Basic realm='Login Required'"},
    )


@app.before_websocket
def make_session_permanent():
    logger.info("@websocket.before_request <--")


def main():
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", 5000)

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        logging=True,
    )


if __name__ == "__main__":
    main()
