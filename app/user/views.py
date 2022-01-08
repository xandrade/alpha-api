from copy import Error
from datetime import timedelta, datetime
import asyncio
from functools import wraps
from unicodedata import name

from .models import Friends, Users, Videos, WatchedVideos, RefUrls

from quart import (
    Blueprint,
    jsonify,
    request,
    Response,
    redirect,
    url_for,
    abort,
    render_template,
    make_response,
)
from quart_auth import AuthUser, login_user, logout_user, current_user, login_required

from email_validator import (
    validate_email,
    caching_resolver,
    EmailNotValidError,
    EmailSyntaxError,
    EmailUndeliverableError,
)
import pyotp
from loguru import logger


auth = Blueprint("auth", __name__, url_prefix="/auth", static_folder="../static")

secret = pyotp.random_base32()

uri = pyotp.totp.TOTP(secret).provisioning_uri(
    name="Antonio", issuer_name="api.meditationbooster.org"
)
logger.info(uri)

import io
import qrcode

qr = qrcode.QRCode()
qr.add_data(uri)
f = io.StringIO()
qr.print_ascii(out=f)
printed = f.getvalue()
logger.info(printed)


@auth.route("/")
@auth.route("/home")
@auth.route("/a")
@login_required
async def members():
    """List members."""
    # return await render_template("users/members.html")
    return jsonify({"message": f"Hello, World! {datetime.utcnow().isoformat()}"}), 200


@auth.route("/logout", methods=["GET"])
async def logout():
    logout_user()
    return redirect(
        url_for("auth.login"),
    )


@auth.route("/logon", methods=["GET"])
async def login_get():
    return "please login"


@auth.route("/logon", methods=["POST"])
async def login():

    print(request)

    data = await request.get_json()

    print(data)

    if data:
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return (
                jsonify(
                    {"status": "unsuccess", "message": "Missing email or password."}
                ),
                400,
            )

        user = await Users.filter(email=email).first()
        if not user:
            return (
                jsonify(
                    {
                        "status": "unsuccess",
                        "message": "User is not registered.",
                    }
                ),
                404,
            )

        if not user.check_password(password):
            return (
                jsonify(
                    {
                        "status": "unsuccess",
                        "message": "The server could not verify that you are authorized to access the URL requested. You either supplied the wrong credentials (e.g. a bad password), or your browser doesn't understand how to supply the credentials required.",
                    }
                ),
                403,
            )

        if user.active:
            auth = AuthUser(user.id)
            auth.email = user.email
            auth.is_admin = user.is_admin
            auth.username = user.username
            auth.full_name = user.full_name
            login_user(auth)
            return jsonify(
                {
                    "status": "success",
                    "message": "Logged in successfully.",
                }
            )
        else:
            return (
                jsonify({"status": "unsuccess", "message": "User is not active."}),
                403,
            )

    else:
        return (
            jsonify(
                {
                    "status": "unsuccess",
                    "message": "The server could not verify that you are authorized to access the URL requested. You either supplied the wrong credentials (e.g. a bad password), or your browser doesn't understand how to supply the credentials required.",
                }
            ),
            400,
        )


@auth.route("/signup", methods=["POST"])
async def register():

    data = await request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not email or not password or not username or not first_name or not last_name:
        return jsonify({"status": "unsuccess", "message": "Missing data."}), 400

    message = None
    try:
        resolver = caching_resolver(timeout=10)
        valid = validate_email(email, dns_resolver=resolver)
        email = valid.email
    except EmailNotValidError as e:
        message = jsonify({"status": "unsuccess", "message": e.args[0]}), 400
    except EmailSyntaxError as e:
        message = jsonify({"status": "unsuccess", "message": e.args[0]}), 400
    except EmailUndeliverableError as e:
        message = jsonify({"status": "unsuccess", "message": e.args[0]}), 412
    except Error as e:
        message = jsonify({"status": "unsuccess", "message": e.args[0]}), 422
    finally:
        if message:
            return message

    user = await Users.filter(email=email).first()
    if not user:
        user = await Users.create(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        user.password = password
        await user.save()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Thank you for sign-in!.",
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "unsuccess",
                    "message": "User already exists.",
                }
            ),
            400,
        )
