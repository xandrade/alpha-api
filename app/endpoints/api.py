from datetime import datetime
from email import message
from ipaddress import ip_address
import random
import asyncio
from functools import wraps
import json
import secrets
import requests
import json

# script_dir = os.path.dirname(__file__)
# mymodule_dir = os.path.join(script_dir, "..", "user")
# sys.path.append(mymodule_dir)
from app.user.models import Friends, Users, YTVideos, YTVideosWatched, RefUrls
from app.data import ViewItem
from app.message import get_random_message
from app.youtube.tools import get_video_title
from quart.utils import run_sync
from quart import (
    Blueprint,
    jsonify,
    request,
    Response,
    websocket,
    abort,
    session,
    make_response,
    current_app,
    render_template,
)
from email_validator import validate_email, caching_resolver, EmailNotValidError
import pyotp
from loguru import logger
import humanize


api = Blueprint("api", __name__, url_prefix="/api", static_folder="../static")

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

# global variable for it
ip_address = None
ip_last_seen = None


clients = set()
requests_queue = asyncio.Queue()

"""
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
"""

from quart_auth import (
    AuthManager,
    Unauthorized,
    login_required,
)


@api.route("/test", methods=["GET"])
@login_required
async def test():
    return "ok"


from functools import wraps
from quart_auth import current_user


def login_required_ext(only_admin=False):
    def login_required(func):
        """A decorator to restrict route access to authenticated users and admins"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not await current_user.is_authenticated:
                raise Unauthorized()
            elif only_admin and not await current_user.is_admin:
                raise Unauthorized()
            else:
                return await current_app.ensure_async(func)(*args, **kwargs)

        return wrapper

    return login_required


@api.route("/", methods=["GET"])
@login_required_ext(only_admin=True)
async def list_all():

    totp = pyotp.TOTP(secret)
    if request.args.get("code") == totp.now():

        friends = await Friends.all()
        users = await Users.all()
        yt_videos = await YTVideos.all()
        yt_videos_watched = await YTVideosWatched.all()
        refurls = await RefUrls.all()

        return jsonify(
            {
                "friends": [str(items) for friend in friends for items in friend],
                "users": [str(items) for user in users for items in user],
                "yt_videos": [str(items) for video in yt_videos for items in video],
                "watchedvideos": [
                    str(items)
                    for watchedvideo in yt_videos_watched
                    for items in watchedvideo
                ],
                "refurls": [str(items) for refurl in refurls for items in refurl],
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
        return (jsonify(
            {
                "status": "error",
                "message": "Uh Oh! Something went wrong",
            }),
            400)

    friend = await Friends.create(given_name=name, email=email)

    return (jsonify(
        {
            "status": "success",
            "message": "Thank you for subscribing to our Friend list!",
        }),
        200,
    )


@api.route("/ref", methods=["GET"])
# @login_required_ext(only_admin=False)
async def ref():
    url = request.args.get("url")
    logger.info(url)

    return f"""
    <head>
        <meta http-equiv=content-type content="text/html; charset=utf-8"
        <meta name=referrer content=never>
        <meta name=robots content="noindex, nofollow">
        <meta http-equiv=refresh content="5; URL={url!r}">
        <link rel="stylesheet" href="../assets/css/main.css">
    </head>
    <body>
    <section id="redirect" class="main style3 secondary">
		<div class="content">
			<header>
				<h2>Within a few seconds, you are being redirected to:</h2>
			</header>
            <div class="box">
                <p><a href="{url}">{url}</a></p>
            </div>
            <div style="width: 100px; justify-content: center; display: inline-flex;">
            <svg version="1.1" id="L4" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 100 100" enable-background="new 0 0 0 0" xml:space="preserve">
                <circle fill="#000" stroke="none" cx="6" cy="50" r="6">
                    <animate attributeName="opacity" dur="1s" values="0;1;0" repeatCount="indefinite" begin="0.1"></animate>    
                </circle>
                <circle fill="#000" stroke="none" cx="26" cy="50" r="6">
                    <animate attributeName="opacity" dur="1s" values="0;1;0" repeatCount="indefinite" begin="0.2"></animate>       
                </circle>
                <circle fill="#000" stroke="none" cx="46" cy="50" r="6">
                    <animate attributeName="opacity" dur="1s" values="0;1;0" repeatCount="indefinite" begin="0.3"></animate>     
                </circle>
                <circle fill="#000" stroke="none" cx="66" cy="50" r="6">
                    <animate attributeName="opacity" dur="1s" values="0;1;0" repeatCount="indefinite" begin="0.4"></animate>     
                </circle>
                <circle fill="#000" stroke="none" cx="86" cy="50" r="6">
                    <animate attributeName="opacity" dur="1s" values="0;1;0" repeatCount="indefinite" begin="0.5"></animate>     
                </circle>
            </svg>
            </div>
		</div>
	</section>
    </body>
    """


def get_videos():

    videos = [
        # "saJUAhmjGoA", # SOS Life
        # "L1mPYhHs7Io&list=UUSHVrCpsFXdnxC34qUj7nOp5w",  # SOS Life
        "rL7yMKkHAdI",  # 13-Jan-2022 203 views -> 13-Jan-2022 396 views
        # "DelrwCeXkvg",  # Pavel 3705 14-Jan-2022 3:41pm -> 3,803 views 15-Jan-2022 2:33pm, 3
        "KOysJXrPTtw",
        "FaIvDpyBNDY",
        "-yHJZqoKyrI",
        "_ifWAxhJjoA",
        "-FJq8X9YXr4",
        "IUOxW9a7Ds4",
        "01GTELF_PII",
        "GQeY_P-zxPQ",
        "456VApmr8Q0",
    ]
    return videos


@api.route("/gallery", methods=["GET"], defaults={"video_pairs": 3})
@api.route("/gallery/<int:video_pairs>", methods=["GET"], defaults={"video_pairs": 3})
async def gallery(video_pairs):

    html = ""

    if video_pairs < 1:
        video_pairs = 1

    videos = get_videos()

    # ToDo: Check if videos list is less than video_pairs*2
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


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global clients

        remote_addr = None
        for header in websocket.headers:
            if "X-Real-Ip" in header:
                remote_addr = header[1]
                break
        else:
            if not remote_addr:
                remote_addr = websocket.remote_addr

        # URL to send the request to
        request_url = "https://geolocation-db.com/jsonp/" + remote_addr
        # Send request and decode the result
        response = requests.get(request_url)
        result = response.content.decode()
        # Clean the returned string so it just contains the dictionary data for the IP address
        result = result.split("(")[1].strip(")")
        # Convert this data into a dictionary
        result = json.loads(result)
        print(result["country_name"])

        # ToDo - check if secrets.token_urlsafe is unique

        websocket.alpha = {
            "status": "registered",
            "total_played": 0,
            "watched_seconds": 0,
            "connectedon": datetime.now(),
            "updatedon": datetime.now(),
            "remote_addr": remote_addr,
            "sec_id": secrets.token_urlsafe(16),
            # "extra": {item[0]: item[1] for item in websocket.headers._list},
            "last_request": None,
            "country": result["country_name"],
            "browser": None,
        }
        clients.add(websocket._get_current_object())
        logger.info(websocket.alpha)

        try:
            return await func(*args, **kwargs)

        except Exception as e:
            logger.error(f"In collect_websocket. Error: {e}")

        finally:

            clients.discard(websocket._get_current_object())
            logger.info(f"{len(clients)} clients connected")

    return wrapper


def _login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):

        token = websocket.cookies.get("X-Authorization")
        # session_id = websocket.cookies.get("session")

        if token == "R3YKZFKBVi2":
            websocket.authenticated = True
            return await func(*args, **kwargs)
        else:
            logger.info(f"Unauthorized access from {websocket.remote_addr}")
            abort(401)

    return wrapper


async def get_websocket_from_session(id):
    for client in clients:
        if client.alpha.get("sec_id") == id:
            return client
    return None


async def send_message(websocket, message):
    global clients

    try:
        await websocket.send(json.dumps(message))
    except Exception as e:
        logger.error(f"In send_message. Error: {e}")
        clients.discard(websocket)
        logger.info(f"{len(clients)} clients connected")
        return

    websocket.alpha["last_request"] = message
    if message == {"request": "kill"}:
        clients.discard(websocket)


async def send_message_to_all(message):
    global clients
    _clients = clients.copy()
    for i, client in enumerate(_clients):
        await send_message(client, message)
        client.alpha["last_request"] = message


"""
async def send_message(websocket, message):
    global clients
    try:
        await websocket.send(json.dumps(message))
        websocket.alpha["last_request"] = message
    except Exception as e:
        logger.error(f"In send_message. Error: {e}")
        if websocket in clients:
            clients.discard(websocket)
            logger.info((f"{websocket} disconnected"))
            logger.info(f"{len(clients)} clients connected")
    finally:
        pass


async def send_message_to_all(message):
    global clients
    for i, client in enumerate(clients):
        try:
            await send_message(client, message)
            client.alpha["last_request"] = message
        finally:
            pass

"""


# playing next video
async def get_next_video():
    if requests_queue.empty():
        build_requests_queue()
    message = await requests_queue.get()
    message = message.to_dict()
    message["request"] = "play"
    message["video_title"] = await run_sync(get_video_title)(message["video_id"])
    return message


# Purge client if they don't reply back to PING from server

connected_websockets = set()


def collect_websocket2(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global connected_websockets
        queue = asyncio.Queue()
        connected_websockets.add(queue)
        try:
            return await func(queue, *args, **kwargs)
        finally:
            connected_websockets.remove(queue)

    return wrapper


@api.websocket("/dashboard")
@collect_websocket2
async def ws2(queue):
    while True:
        data = await queue.get()
        await websocket.send(json.dumps(data))


async def broadcast(message):
    for queue in connected_websockets:
        await queue.put(message)


@api.route("/dashboard/<message>")
async def test2(message):
    await broadcast(message)
    return "message sent"


@api.websocket("/ws")
# @login_required
@collect_websocket
async def ws():
    global clients
    while True:

        # message = await websocket.recv()
        data = await websocket.receive_json()

        if data.get("status") == "ping":
            # websocket.alpha["status"] = "completed"
            # websocket.alpha["total_played"] += 1
            # websocket.alpha["updatedon"] = datetime.now() ToDo: do we need an updateon for PING/PONG?
            logger.debug(
                f'Is YT window closed? {data.get("windowClosed")}, How many objects are created? {data.get("windowLength")}'
            )
            if not data.get("windowClosed") and 0 < data.get("windowLength") > 1:
                websocket.alpha["watched_seconds"] = (
                    websocket.alpha["watched_seconds"] + 15
                )

            await websocket.send(json.dumps({"request": "pong"}))

        if data.get("status") == "completed":
            websocket.alpha["status"] = "completed"
            websocket.alpha["total_played"] += 1
            websocket.alpha["updatedon"] = datetime.now()

        if data.get("status") == "stopped":
            websocket.alpha["status"] = "stopped"
            websocket.alpha["updatedon"] = datetime.now()

        elif data.get("status") == "pong":
            # websocket.close()
            websocket.alpha["updatedon"] = datetime.now()

        elif data.get("status") == "playing":
            websocket.alpha["status"] = "playing"
            websocket.alpha["updatedon"] = datetime.now()

        elif data.get("status") == "terminated":
            websocket.alpha["status"] = "terminated"
            websocket.alpha["updatedon"] = datetime.now()

            # global clients
            # clients.discard(websocket._get_current_object())
            # await websocket.close(
            #    code=1000, reason="Conection terminated from client"
            # )

        elif data.get("status") == "available":
            websocket.alpha["updatedon"] = datetime.now()
            websocket.alpha["status"] = "available"
            websocket.alpha["browser"] = {
                "name": data.get("browser_name"),
                "version": data.get("browser_version"),
                "platform": data.get("browser_platform"),
                "language": data.get("browser_language"),
            }

            await client_actions("play", websocket.alpha["sec_id"])


def build_requests_queue():
    global requests_queue
    videos = get_videos()
    for video in videos:
        html = f"""<iframe style='position: absolute; height: 100%; width: 100%; border: none' src='https://www.youtube.com/embed/{video}?&amp;autoplay=1&amp;controls=0&amp;mute=1&amp;loop=1&amp;playlist={video}' title='YouTube video player' frameborder='0' allow='autoplay; encrypted-media; picture-in-picture' allowfullscreen='' >"""

        refs = [
            "https://meditationbooster.org/api/ref?url=",
            "https://dropref.com/?",
            "https://dereferer.me/?",
            # "https://l.facebook.com/l.php?dev=facebook&fbclid=IwAR2kH70YB6qe3tY9GPwdi8myCJwhYJbXTrltEhVWC_VCRnqdE_Zc8mBi3S8&h=AT1EzB_qaiZUk45Gw21IYzWtXuxSEOP7UnwRI2v-HWiK_PJhIy5lTzzyo74VJApuYvj7NCKOt1L3K90vGDHusNiskvD_sxRSzSN8k5xb_22TKd4Q0EH1FRrJf5r8oPSujg1WFI763TsVd8VCBg&__tn__=-UK-R&c[0]=AT02FdIeLab5VQEV5XsyDGpXuPXqk9mGYPePpMYqdDo-zwXpdkdO1RFmJ1G4tmEmp2g6u7xc9AXOvgiyraZGqHqO0jN6qVEYX9FJyM8zcKHs-gY8MWkKbFsZmr__EieuBpEs&u="
            # "https://l.instagram.com/?v=GQeY_P-zxPQ&e=ATNS_Ti8mG04Nyg9DHBunTsbw865ONNUeG-6bLSvs7ln8BGXpyjwI2BqgcZphYxiBdI9eRkzcGspXeQLSyD1H7G6EH1Ky5YgTl1i&s=1&u="
            # "",
        ]
        ref = random.choice(refs)

        video_url = f"https://www.youtube.com/watch?v={video}"
        item = ViewItem(
            video_id=video,
            video_url=video_url,
            redirect_url=ref,
            duration=random.choice(range(60, 60 * 5)),
            # duration=20,
        )
        requests_queue.put_nowait(item)


build_requests_queue()


@api.route("/vm", methods=["GET"])
async def vm():
    # return await render_template("dashboard.html", clients=clients)
    clients_dict = [{item: client.alpha} for item, client in enumerate(clients, 1)]
    return jsonify({"clients": clients_dict, "queue": requests_queue.qsize()})


@api.route("/client/<action>", methods=["GET"], defaults={"sec_id": "ALL"})
@api.route("/client/<action>/<sec_id>", methods=["GET"])
# @login_required
async def client_actions(action, sec_id):

    if action == "reload":
        message = {"request": "reload"}
    elif action == "kill":
        message = {"request": "kill"}
    elif action == "ping":
        message = {"request": "ping"}
    elif action == "stop":
        message = {"request": "stop"}
    elif action == "play":
        message = await get_next_video()
    else:
        logger.error(f"Invalid action: {action}")
        abort(400)

    if str(sec_id).upper() == "ALL":
        await send_message_to_all(message)
    else:
        client = await get_websocket_from_session(sec_id)
        if client:
            if action == "play":
                message = await get_next_video()
            await send_message(client, message)
            client.alpha["last_request"] = message
    return jsonify({"status": "success"}), 200


@api.route("/dashboard", methods=["GET"])
# @login_required
async def dashboard():
    # return await render_template("dashboard.html", clients=clients)
    clients_list = [client.alpha for client in clients]
    c = []

    icons = [
        {
            "play": """<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"></path><polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"></polygon></svg>""",
            "stop": """<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><circle cx="12" cy="12" r="10"></circle><rect x="9" y="9" width="6" height="6"></rect></svg>""",
            "reload": """<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>""",
            "kill": """<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="18" y1="8" x2="23" y2="13"></line><line x1="23" y1="8" x2="18" y2="13"></line></svg>""",
            "ping": """<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>""",
        }
    ]

    # ToDo - add icons

    try:
        for id, client in enumerate(clients_list, 1):

            client["diff"] = humanize.precisedelta(
                datetime.now() - client["updatedon"], minimum_unit="milliseconds"
            )
            client["#"] = id
            client["status"] = client["status"].capitalize()
            client[
                "commands"
            ] = f"""
            <a name=play id={client.get("sec_id")}>||play||</a> 
            <a name=stop id={client.get("sec_id")}>||stop||</a> 
            <a name=reload id={client.get("sec_id")}>||reload||</a> 
            <a name=ping id={client.get("sec_id")}>||ping||</a>
            <a name=kill id={client.get("sec_id")}>||kill||</a>
            """
            c.append(client)
    except Exception as e:
        logger.error(f"Error: {e}")
        abort(500)

    import json2html

    input = {
        "name": "json2html",
        "description": "Converts JSON to HTML tabular representation",
    }

    table = json2html.json2html.convert(
        json=c,
        table_attributes='id="info-table" class="table table-bordered table-hover"',
    )

    table = table.replace("||play||", icons[0]["play"])
    table = table.replace("||stop||", icons[0]["stop"])
    table = table.replace("||reload||", icons[0]["reload"])
    table = table.replace("||kill||", icons[0]["kill"])
    table = table.replace("||ping||", icons[0]["ping"])

    table = table.replace("&lt;", "<")
    table = table.replace("&gt;", ">")
    table = table.replace("&amp;", "&")
    # table = table.replace('&quot;', '"')
    # table = table.replace('&#39;', "'")
    # table = table.replace('&#x2F;', '/')

    html = f"""
    <html>
    <head>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js" integrity="sha256-/xUj+3OJU5yExlq6GSYGSHk7tPXikynS7ogEvDej/m4=" crossorigin="anonymous"></script>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
    </head>
    <body> {table}
    </body>
    ||script||
    </html>
    """

    script = """
    <script type="text/javascript">
        
        function refresh() {    
            setTimeout(function () {
                location.reload()
            }, 100);
        }

        $("[name=play]").each(function() {
            $( this ).click(function(){
                $.get("/api/client/play/" + this.id, function(data, status){
                    alert("Status: " + status);
                    refresh();
                });
            });
        });

        $("[name=stop]").each(function() {
            $( this ).click(function(){
                $.get("/api/client/stop/" + this.id, function(data, status){
                    alert("Status: " + status);
                    refresh();
                });
            });
        });

        $("[name=ping]").each(function() {
            $( this ).click(function(){
                $.get("/api/client/ping/" + this.id, function(data, status){
                    alert("Status: " + status);
                    refresh();
                });
            });
        });

        $("[name=reload]").each(function() {
            $( this ).click(function(){
                $.get("/api/client/reload/" + this.id, function(data, status){
                    alert("Status: " + status);
                    refresh();
                });
            });
        });
        
        $("[name=kill]").each(function() {
            $( this ).click(function(){
                $.get("/api/client/kill/" + this.id, function(data, status){
                    alert("Status: " + status);
                    refresh();
                });
            });
        });

    </script>
    <script type="text/javascript">
        
            var timer1

            function connect() {

                var url = '||wsocket||://' + document.domain + ':' + location.port + '/api/dashboard'
                var ws = new WebSocket(url);
                ws.debug = true;

                ws.onopen = function() {
                    //$('#val').text('Connected to server, waiting for command...');
                    console.log('Socket connection established');
                    //ws.send(JSON.stringify({'status': 'available'}));

                };https://meditationbooster.org/api/client?c=youlikehits.com
                
                ws.onclose = function(event) {
                    //$('#val').text('Disconected from server. Retrying in 5 seconds...');
                    console.log('Socket connection closed, retrying in 5 seconds...');
                    window.setTimeout(connect, 5000)
                };
                
                ws.onerror = function(err) {
                    console.error('Socket encountered error: ', err.message, 'Closing socket');
                    ws.close();
                };

                ws.onmessage = function (event) {
                    console.log('Received: ' + event.data);
                    var data = JSON.parse(event.data);
                    console.log(data)
                };
            };

            // connect();

        </script>
    """
    html = html.replace("||script||", script)

    from app.main import _app as app

    if app.config["QUART_ENV"] == "DEVELOPMENT":
        html = html.replace("||wsocket||", "ws")
    else:
        html = html.replace("||wsocket||", "wss")

    return html


@api.route("/client", methods=["GET"])
async def html():

    logger.debug(request.full_path)

    from app.main import _app as app

    wsocket = "wss"
    if app.config["QUART_ENV"] == "DEVELOPMENT":
        wsocket = "ws"
    return (
        await render_template(
            "client.html", message=get_random_message(), wsocket=wsocket
        ),
        200,
    )


@api.route("/ip", methods=["POST"])
async def set_ip():

    global ip_address, ip_last_seen

    data = await request.get_json()
    ip_address = data.get("ip")
    ip_last_seen = datetime.now()

    return (jsonify(
        {
            "status": "success",
            "message": f"IP address set to {ip_address} at {ip_last_seen}",
        }),
        200
    )


@api.route("/ip", methods=["GET"])
async def get_ip():

    global ip_address, ip_last_seen

    return (jsonify(
        {
            "status": "success",
            "ip": {
                "address": ip_address,
                "last_seen": ip_last_seen,
            },
        }),
        200
    )
