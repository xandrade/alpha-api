from datetime import timedelta
import random
import asyncio
from functools import wraps
import json

from models import Friends
from data import ViewItem

from quart import Blueprint, jsonify, request, Response, websocket
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


def get_videos():

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
    return videos


@api.route("/gallery", methods=["GET"], defaults={"video_pairs": 3})
@api.route("/gallery/<int:video_pairs>", methods=["GET"], defaults={"video_pairs": 3})
async def gallery(video_pairs):

    html = ""

    if video_pairs < 1:
        video_pairs = 1

    videos = get_videos()

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


@api.websocket("/ws")
async def ws():
    while True:
        data = await websocket.receive_json()
        if data.get("type") == "subscribe":
            if requests_queue.empty():
                build_requests_queue()
            request = await requests_queue.get()
            await websocket.send_json(request.to_dict())


clients = set()
requests_queue = asyncio.Queue()


def build_requests_queue():
    global requests_queue
    videos = get_videos()
    for video in videos:
        html = f"""<iframe style='position: absolute; height: 100%; width: 100%; border: none' src='https://www.youtube.com/embed/{video}?&amp;autoplay=1&amp;controls=0&amp;mute=1&amp;loop=1&amp;playlist={video}' title='YouTube video player' frameborder='0' allow='autoplay; encrypted-media; picture-in-picture' allowfullscreen='' >"""
        html = f"https://www.youtube.com/watch?v={video}"
        item = ViewItem(html, duration=random.choice(range(30, 60)))
        requests_queue.put_nowait(item)


build_requests_queue()


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global clients
        queue = asyncio.Queue()
        clients.add(queue)
        try:
            return await func(queue, *args, **kwargs)
        finally:
            clients.remove(queue)

    return wrapper


@api.websocket("/api/v2/ws")
@collect_websocket
async def ws2():
    global requests_queue
    while True:
        data = await requests_queue.get()
        await websocket.send(data)


async def broadcast(message):
    for queue in clients:
        await queue.put(message)


@api.route("/client", methods=["GET"])
async def html():

    return """
    <!doctype html>
    <html>
    <head>
        <title>Alpha Video Pool - Client</title>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    </head>
    <body>
        <div id='yt'></div>
        <script type="text/javascript">
        
            function connect() {
                //var ws = new WebSocket('wss://' + document.domain + ':' + location.port + '/api/ws');
                var ws = new WebSocket('wss://meditationbooster.org/api/ws');
                
                ws.onopen = function() {
                    ws.send(JSON.stringify({
                        'type': 'subscribe',
                        'channel': 'views'}));
                };

                ws.onclose = function(e) {
                    console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
                    setTimeout(function() {
                    connect();
                    }, 5000);
                };

                ws.onerror = function(err) {
                    console.error('Socket encountered error: ', err.message, 'Closing socket');
                    ws.close();
                };

                ws.onmessage = function (event) {
                    console.log('Received: ' + event.data);
                    var data = JSON.parse(event.data);
                    console.log(data.video);
                    console.log(data.duration);
                    document.getElementById('yt').innerHTML = data.video;
                    openWin(data.video);
                    setInterval(closeWin, data.duration * 1000);
                };

                function nextVideo() {
                    ws.send(JSON.stringify({
                        'type': 'subscribe',
                        'channel': 'views'}));
                }
                

                function openWin(url) {
                    myWindow = window.open(url, "_blank", "width=500, height=350");
                }

                function closeWin() {
                    myWindow.close();
                    nextVideo();
                }

            };

            connect();

        </script>
    </body>
    </html>
    """
