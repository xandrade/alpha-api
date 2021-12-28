from datetime import timedelta, datetime
import asyncio
from functools import wraps

from models import Friends, Users, Videos, WatchedVideos, RefUrls

from quart import (
    Blueprint,
    jsonify,
    request,
    Response,
    redirect,
    url_for,
    abort,
)
from quart_auth import AuthUser, login_user, logout_user, current_user, login_required

from email_validator import validate_email, caching_resolver, EmailNotValidError
import pyotp
from loguru import logger
from passlib.context import CryptContext


authwall = Blueprint("authwall", __name__, url_prefix="/authwall")

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
# f.seek(0)
# print(f.read())
# logger.info(f.read())
logger.info(printed)


# create CryptContext object
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=50000,
)


@authwall.app_errorhandler(403)
def forbidden():
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


@authwall.route("/", methods=["GET"])
@login_required
async def restricted_route():
    if await current_user.is_authenticated:
        return jsonify({"message": "You are logged in!"})
    else:
        return redirect(url_for("authwall.login"))


@authwall.route("/logout", methods=["GET"])
async def logout():
    logout_user()
    return redirect(url_for("authwall.login"))


@authwall.route("/login", methods=["GET"])
async def login_get():
    return "please login"


@authwall.route("/login", methods=["POST"])
async def login():

    data = await request.get_json()

    if data:
        email = data.get("email")
        password = data.get("pwd")

        if not email or not password:
            return jsonify({"message": "Missing email or password"}), 400

        user = await Users.filter(email=email).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        if not pwd_context.verify(password, user.password):
            return abort(403)

        if user.is_active:
            login_user(AuthUser(user.email))
            return jsonify({"message": "Logged in successfully"})
        else:
            return jsonify({"message": "User is not active"}), 403

    else:
        return jsonify({"message": "Missing data"}), 400


@authwall.route("/register", methods=["POST"])
async def register():

    data = await request.get_json()
    email = data.get("email")
    password = data.get("pwd")

    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400

    if not validate_email(email):
        return jsonify({"message": "Invalid email"}), 400

    resolver = caching_resolver(timeout=10)
    try:
        valid = validate_email(email, dns_resolver=resolver)
        email = valid.email
    except EmailNotValidError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid email",
                }
            ),
            400,
        )

    user = await Users.filter(email=email).first()
    if not user:
        user = await Users.create(
            email=email,
            password=pwd_context.hash(password),
        )

        return jsonify(
            {
                "status": "success",
                "message": "Thank you for sign-in!",
            },
            200,
        )
    else:
        return jsonify(
            {
                "status": "error",
                "message": "User already exists",
            },
            400,
        )
