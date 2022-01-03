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

from email_validator import validate_email
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


# ToDo: return abort(403) is returning an error


@auth.app_errorhandler(403)
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
            return jsonify({"message": "Missing email or password"}), 400

        user = await Users.filter(email=email).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        if not user.check_password(password):
            print("nothing")
            return abort(403)

        if user.active:
            auth = AuthUser(user.id)
            auth.email = user.email
            auth.is_admin = user.is_admin
            auth.username = user.username
            auth.full_name = user.full_name
            login_user(auth)
            return jsonify({"message": "Logged in successfully"})
        else:
            return jsonify({"message": "User is not active"}), 403

    else:
        return jsonify({"message": "Missing data"}), 400


@auth.route("/signup", methods=["POST"])
async def register():

    data = await request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not email or not password or not username or not first_name or not last_name:
        return jsonify({"message": "Missing data"}), 400

    if not validate_email(email):
        return jsonify({"message": "Invalid email"}), 400

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
                    "message": "Thank you for sign-in!",
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "User already exists",
                }
            ),
            400,
        )
