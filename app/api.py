from datetime import timedelta
from datetime import datetime
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
        "saJUAhmjGoA", # SOS Life
        "IUOxW9a7Ds4",
        "01GTELF_PII",
        "GQeY_P-zxPQ",
        "1tgMryiUx58",
        "GnuHsc1S5vY",
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
    ]
    return videos[:5]  # last 5 videos


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


def uniqueid():
    seed = random.getrandbits(32)
    while True:
        yield seed
        seed += 1


clients = set()
requests_queue = asyncio.Queue()


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global clients
        logger.info(clients)
        websocket.alpha = {
            "status": "registered",
            "total_played": 0,
            "connectedon": datetime.now(),
            "updatedon": datetime.now(),
            "extra": {item[0]: item[1] for item in websocket.headers._list},
            "play_info": None,
        }
        clients.add(websocket._get_current_object())
        try:
            return await func(*args, **kwargs)
        finally:
            clients.remove(websocket._get_current_object())

    return wrapper


@api.websocket("/ws")
@collect_websocket
async def ws():
    while True:
        try:
            #  logger.debug(websocket.headers.get(["Origin"]))
            logger.error(websocket._get_current_object())
            data = await websocket.receive_json()

            if data.get("status") == "completed":
                websocket.alpha["status"] = "completed"
                websocket.alpha["total_played"] += 1
                websocket.alpha["updatedon"] = datetime.now()

            elif data.get("status") == "playing":
                websocket.alpha["status"] = "playing"
                websocket.alpha["updatedon"] = datetime.now()

            elif data.get("status") == "available":
                websocket.alpha["status"] = "available"
                websocket.alpha["updatedon"] = datetime.now()

                # playing next video
                if requests_queue.empty():
                    build_requests_queue()
                request = await requests_queue.get()
                request = request.to_dict()
                websocket.alpha["play_info"] = request
                await websocket.send_json(request)

        except asyncio.CancelledError:
            print(f"Client disconnected. Client data: {websocket.alpha}")
            raise


def build_requests_queue():
    global requests_queue
    videos = get_videos()
    for video in videos:
        html = f"""<iframe style='position: absolute; height: 100%; width: 100%; border: none' src='https://www.youtube.com/embed/{video}?&amp;autoplay=1&amp;controls=0&amp;mute=1&amp;loop=1&amp;playlist={video}' title='YouTube video player' frameborder='0' allow='autoplay; encrypted-media; picture-in-picture' allowfullscreen='' >"""

        refs = [
            "https://meditationbooster.org/api/ref?url=",
            "https://dropref.com/?",
            "https://dereferer.me/?",
            "",
        ]
        ref = random.choice(refs)

        html = f"{ref}https://www.youtube.com/watch?v={video}"
        item = ViewItem(html, duration=random.choice(range(35, 60 * 2)))
        requests_queue.put_nowait(item)


build_requests_queue()


async def broadcast(message):
    for queue in clients:
        await queue.put(message)


@api.route("/vm", methods=["GET"])
async def dashboard():
    # return await render_template("dashboard.html", clients=clients)
    clients_dict = [client.alpha for client in clients]
    return jsonify({"clients": clients_dict, "queue": requests_queue.qsize()})


@api.route("/dashboard", methods=["GET"])
async def dashboard():
    # return await render_template("dashboard.html", clients=clients)
    clients_dict = [client.alpha for client in clients]

    import json2html

    input = {
            "name": "json2html",
            "description": "Converts JSON to HTML tabular representation"
    }
    
    return json2html.convert(json = clients_dict, table_attributes="id=\"info-table\" class=\"table table-bordered table-hover\"")


@api.route("/client", methods=["GET"])
async def html():

    return """
    <!doctype html>
    <html>
    <head>
        <title>Alpha - Client</title>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    </head>
    <body>
        <progress max="100" min="0" value="100" width="100%";></progress>
        <div id="val"></div>
        <div id='yt'></div>
        <script type="text/javascript">
        
            var myWindow = null
            var timer1 = null
            var timer2 = null


            function connect() {
                //var ws = new WebSocket('ws://' + document.domain + ':' + location.port + '/api/ws');
                var ws = new WebSocket('wss://meditationbooster.org/api/ws');
                
                ws.debug = true;

                ws.onopen = function() {
                    console.log('Socket connection established');
                    ws.send(JSON.stringify({'status': 'available'}));
                };

                ws.onclose = function(e) {
                    if (event.wasClean) {
                        console.log(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
                    } else {
                            console.log('[close] Connection died');
                    }
                    ws = null
                    setTimeout(connect, 5000)
                    window.myWindow.close();
                    clearTimeout(window.timer1);
                    clearTimeout(window.timer2);
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
                    timer1 = setTimeout(closeWin, data.duration * 1000);
                    
                    var interval = 1, //How much to increase the progressbar per frame
                    updatesPerSecond = data.duration*1000/60, //Set the nr of updates per second (fps)
                    progress =  $('progress'),
                    animator = function(){
                        progress.val(progress.val()+interval);
                        $('#val').text(progress.val());
                        if ( progress.val()+interval < progress.attr('max')){
                        setTimeout(animator, updatesPerSecond);
                        } else { 
                            $('#val').text('Done');
                            progress.val(progress.attr('max'));
                        }
                    },
                    reverse = function(){
                        progress.val(progress.val() - interval);
                        $('#val').text(progress.val());
                        if ( progress.val() - interval > progress.attr('min')){
                        setTimeout(reverse, updatesPerSecond);
                        } else { 
                            $('#val').text('Done');
                            progress.val(progress.attr('min'));
                        }
                    }
                    progress.val(data.duration);
                    timer2 = setTimeout(reverse, updatesPerSecond);

                    ws.send(JSON.stringify({'status': 'playing'}));

                };

                function nextVideo() {
                    console.log('Requesting for next video');
                    ws.send(JSON.stringify({'status': 'available'}));
                }
                

                function openWin(url) {
                    window.myWindow = window.open(url, "_blank", "width=500, height=350");
                }

                function closeWin() {
                    console.log('Closing window');
                    window.myWindow.close();
                    console.log('Closed window');
                    ws.send(JSON.stringify({'status': 'completed'}));
                    nextVideo();
                }

            };

            connect();

        </script>
    </body>
    </html>
    """
