from datetime import timedelta
import random

from quart.wrappers import response

from models import Friends

from quart import Blueprint, jsonify, request, Response, make_response
from quart_cors import cors, route_cors
from email_validator import validate_email, caching_resolver, EmailNotValidError
import pyotp
from loguru import logger


api = Blueprint("api", __name__, url_prefix="/api")

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


@api.app_errorhandler(403)
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


@api.route("/", methods=["GET"])
@route_cors(allow_origin="https://meditationbooster.org/")
async def list_all():

    totp = pyotp.TOTP(secret)
    if request.args.get("code") == totp.now():

        friends = await Friends.all()
        return jsonify(
            {
                "friend": [str(items) for friend in friends for items in friend],
            }
        )
    else:
        return (
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
            403,
        )  # HTTP Status 403 Forbidden


@api.route("/friend", methods=["POST"])
async def add_friend():

    data = await request.get_json()
    name = data.get("name")
    email = data.get("email")

    resolver = caching_resolver(timeout=10)
    try:
        valid = validate_email(email, dns_resolver=resolver)
        email = valid.email
    except EmailNotValidError as e:
        return jsonify(
            {
                "status": "error",
                "message": "Uh Oh! Something went wrong",
            },
            400,
        )

    friend = await Friends.create(name=name, email=email)
    str(friend)
    return jsonify(
        {
            "status": "success",
            "message": "Thank you for subscribing to our Friend list!",
        },
        200,
    )


@api.route("/ref", methods=["GET"])
async def ref():
    url = request.args.get("url")
    logger.info(url)

    return f"""
    <head>
    <meta http-equiv="refresh" content="5; URL={url}" />
    </head>
    <body>
    <p>If you are not redirected in five seconds, <a href="{url}">click here</a>.</p>
    </body>
    """


@api.route("/gallery", methods=["GET"], defaults={"video_pairs": 3})
@api.route("/gallery/<int:video_pairs>", methods=["GET"], defaults={"video_pairs": 3})
async def gallery(video_pairs):

    html = ""

    if video_pairs < 1:
        video_pairs = 1

    videos = [
        "pAVk0tLJvA0",
        "QMyahx3soiM",
        "ffC08UqcFw0",
        "IeXppHVrsug",
        "EvLcyB9VNrU",
        "gXRGI0NE-7E",
        "wxGyA9mGRK8",
        "-fukPEXrQas",
        "8fGe2sidmGg",
        "1JmBBX8KOOQ",
        "kvza7Y2_FNk",
        "-xEzBOO337A",
        "HtVBWnQNaGE",
        "EGGM94l1fKU",
        "FB12t1_LHWI",
        "r92LBThuBmc",
        "7ZEdnyHQ_No",
        "ahaI1xRKYYk",
        "ERFin10XwDw",
        "Te7k0T_hkkI",
        "mwthQLYEcNk",
        "KmcjB_Fdxm0",
        "CTgbZ8tOu2c",
        "96r-OdsZcgE",
        "3Slh4cICQDs",
        "_Lssqh8m7oE",
        "-gk1Lc6hE2Y",
        "lPRo4B36AaA",
        "bdl7GgI7egY",
        "n3PUlsd5tlc",
        "Wmug-C65tGI",
        "PvXZBcLuTPs",
        "QMyahx3soiM",
        "GnuHsc1S5vY",
    ]

    random_video = random.sample(videos, video_pairs * 2)

    for i in range(video_pairs):
        left, right = random_video[i * 2], random_video[i * 2 + 1]
        _html = f"""
                <article class="from-left">
					<iframe width="100%" height="350" src="https://www.youtube.com/embed/{left}?controls=0"
						title="YouTube video player" frameborder="0"
						allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>
				</article>
				<article class="from-right">
					<iframe width="100%" height="350"
						src="https://www.youtube.com/embed/{right}?controls=0&autoplay=0"
						title="YouTube video player" frameborder="0"
						allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>
				</article>
        """
        html += _html

    return html, 200
