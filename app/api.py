from datetime import timedelta
from datetime import datetime
import random
import asyncio
from functools import wraps
import json
from typing import AsyncContextManager

from models import Friends
from data import ViewItem

from quart import Blueprint, jsonify, request, Response, websocket, abort, session, make_response
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
        #"saJUAhmjGoA", # SOS Life
        "L1mPYhHs7Io&list=UUSHVrCpsFXdnxC34qUj7nOp5w", # SOS Life
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


clients = set()
requests_queue = asyncio.Queue()


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global clients
        logger.info(clients)
        # asyncio.wait(20)

        for header in websocket.headers:
            if 'Sec-Websocket-Key' in header:
                sec_id = header[1]
                break

        websocket.alpha = {
            "status": "registered",
            "total_played": 0,
            "connectedon": datetime.now(),
            "updatedon": datetime.now(),
            "remote_addr": websocket.remote_addr,
            #"session_id": websocket.cookies.get("session"),
            "sec_id": sec_id,
            #"extra": {item[0]: item[1] for item in websocket.headers._list},
            "last_request": None,
        }
        clients.add(websocket._get_current_object())
        try:
            return await func(*args, **kwargs)
        finally:
            clients.remove(websocket._get_current_object())

    return wrapper


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        
        token = websocket.cookies.get("X-Authorization")
        # session_id = websocket.cookies.get("session")
        
        if token == 'R3YKZFKBVi2':
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
    await websocket.send(json.dumps(message))


async def send_message_to_all(message):
    for client in clients:
        await send_message(client, message)
        client.alpha["last_request"] = message


# playing next video
async def get_next_video():
    if requests_queue.empty():
        build_requests_queue()
    message = await requests_queue.get()
    message = message.to_dict()
    message['request'] = 'play'
    return message


@api.websocket("/ws")
@login_required
@collect_websocket
async def ws():
    while True:
        try:

            #  logger.debug(websocket.headers.get(["Origin"]))
            #logger.error(websocket._get_current_object())
            data = await websocket.receive_json()

            if data.get("status") == "completed":
                websocket.alpha["status"] = "completed"
                websocket.alpha["total_played"] += 1
                websocket.alpha["updatedon"] = datetime.now()
            
            elif data.get("ping") == "pong":
                # websocket.close()
                websocket.alpha["updatedon"] = datetime.now()

            elif data.get("status") == "playing":
                websocket.alpha["status"] = "playing"
                websocket.alpha["updatedon"] = datetime.now()

            elif data.get("status") == "terminated":
                websocket.alpha["status"] = "terminated"
                websocket.alpha["updatedon"] = datetime.now()

            elif data.get("status") == "available":
                websocket.alpha["status"] = "available"
                websocket.alpha["updatedon"] = datetime.now()

                #message = await get_next_video()
                #websocket.alpha["last_request"] = message
                #await websocket.send_json(message)

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
async def vm():
    # return await render_template("dashboard.html", clients=clients)
    clients_dict = [{item:client.alpha} for item, client in enumerate(clients, 1)]
    return jsonify({"clients": clients_dict, "queue": requests_queue.qsize()})


@api.route("/client/<action>", methods=["GET"], defaults={'sec_id': 'ALL'})
@api.route("/client/<action>/<sec_id>", methods=["GET"])
async def client_actions(action, sec_id):
    

    if action == 'reload': message = {"request": "reload"}
    elif action == 'kill': message = {"request": "kill"}
    elif action == 'ping': message = {"request": "ping"}
    elif action == 'stop': message = {"request": "stop"}
    elif action == 'play': message =  await get_next_video()
    else:
        logger.error(f"Invalid action: {action}")
        abort(400)

    if str(sec_id).upper() == 'ALL':
        await send_message_to_all(message)
    else:
        client = await get_websocket_from_session(sec_id)
        if client:
            if action == 'play':
                message =  await get_next_video()
            await send_message(client, message)
            client.alpha["last_request"] = message
    return jsonify({"status": "success"})


@api.route("/dashboard", methods=["GET"])
async def dashboard():
    # return await render_template("dashboard.html", clients=clients)
    clients_list = [client.alpha for client in clients]
    c = []


    icons = [{'play': '''<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"></path><polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"></polygon></svg>''',
              'stop': '''<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><circle cx="12" cy="12" r="10"></circle><rect x="9" y="9" width="6" height="6"></rect></svg>''',
              'reload': '''<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>''',
              'kill': '''<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="18" y1="8" x2="23" y2="13"></line><line x1="23" y1="8" x2="18" y2="13"></line></svg>''',
              'ping': '''<svg viewBox="0 0 24 24" width="24" height="24" stroke="#000000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>''',

            }]


    # ToDo - add icons

    for id, client in enumerate(clients_list, 1):
        client['#'] = id
        client['status'] = client['status'].capitalize()
        client['commands'] = f'''
        <a href=https://meditationbooster.org/api/client/play/{client.get("sec_id")} onclick="return false;">||play||</a> 
        <a href=https://meditationbooster.org/api/client/stop/{client.get("sec_id")} onclick="return false;">||stop||</a> 
        <a href=https://meditationbooster.org/api/client/reload/{client.get("sec_id")} onclick="return false;">||reload||</a> 
        <a href=https://meditationbooster.org/api/client/ping/{client.get("sec_id")} onclick="return false;">||ping||</a>
        '''
        c.append(client)

    import json2html

    input = {
            "name": "json2html",
            "description": "Converts JSON to HTML tabular representation"
    }
    
    table = json2html.json2html.convert(json=c, table_attributes="id=\"info-table\" class=\"table table-bordered table-hover\"")

    table = table.replace('||play||', icons[0]['play'])
    table = table.replace('||stop||', icons[0]['stop'])
    table = table.replace('||reload||', icons[0]['reload'])
    table = table.replace('||kill||', icons[0]['kill'])
    table = table.replace('||ping||', icons[0]['ping'])

    table = table.replace('&lt;', '<')
    table = table.replace('&gt;', '>')
    table = table.replace('&amp;', '&')
    #table = table.replace('&quot;', '"')
    #table = table.replace('&#39;', "'")
    #table = table.replace('&#x2F;', '/')


    html = f"""
    <html>
    <head>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
    </head>
    <body> {table}
    </body>
    </html>
    """

    return html


@api.route("/client", methods=["GET"])
async def html():

    # session['X-Authorization'] = 'R3YKZFKBVi2'

    html = """
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
        
            var windowObjectReference = null
            var timer1 = null
            var timer2 = null


            function connect() {

                //var url = 'ws://' + document.domain + ':' + location.port + '/api/ws'
                var url = 'wss://meditationbooster.org/api/ws'

                var ws = new WebSocket(url);
                
                ws.debug = true;

                ws.onopen = function() {
                    $('#val').text('Connected to server, waiting for command...');
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
                    windowObjectReference.close();
                    clearTimeout(window.timer1);
                    clearTimeout(window.timer2);
                    $('#val').text('Disconected from server. Retrying in 5 seconds...');
                };
                
                ws.onerror = function(err) {
                    console.error('Socket encountered error: ', err.message, 'Closing socket');
                    $('#val').text('Error detected. Retrying in 5 seconds...');
                    ws.close();
                };

                ws.onmessage = function (event) {
                    console.log('Received: ' + event.data);
                    var data = JSON.parse(event.data);
                    var request = data.request;
                    
                    if (request == "reload") {
                        window.location.reload();
                    }
                    if (request == "stop") {
                        clearTimeout(window.timer1);
                        clearTimeout(window.timer2);
                        windowObjectReference.close();
                        $('#val').text('Stopped from server');
                        ws.send(JSON.stringify({'status': 'available'}));
                    }
                    else if (request == "ping") {
                        console.log('ping');
                        ws.send(JSON.stringify({'ping': 'pong'}));
                    }
                    else if (request == "kill") {
                        clearTimeout(window.timer1);
                        clearTimeout(window.timer2);
                        windowObjectReference.close();
                        window.open("", '_self').window.close();
                        setTimeout (window.close, 5000);
                        window.close();
                        setTimeout(() => {window.close();}, 2000);
                        setTimeout(() => {window.close();}, 4000);
                    }
                    else if (request == "play") {
                        
                        console.log(data.video);
                        console.log(data.duration);
                        document.getElementById('yt').innerHTML = data.video;
                        openRequestedPopup(data.video, 'Client');
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
                };

                function nextVideo() {
                    console.log('Requesting for next video');
                    ws.send(JSON.stringify({'status': 'available'}));
                }

                function openRequestedPopup(url, windowName) {
                    if(windowObjectReference == null || windowObjectReference.closed) {
                        windowObjectReference = window.open(url, windowName, "popup, width=500, height=350, rel=noreferrer, toolbar=0, status=0,");
                    } else {
                        windowObjectReference.focus();
                    };
                };

                function closeWin() {
                    console.log('Closing window');
                    windowObjectReference.close();
                    console.log('Closed window');
                    ws.send(JSON.stringify({'status': 'completed'}));
                    nextVideo();
                };

                window.onbeforeunload = function(event) {
                    windowObjectReference.close();
                    ws.send(JSON.stringify({'status': 'terminated'}));
                };

                window.addEventListener('beforeunload', function (e) {
                    // the absence of a returnValue property on the event will guarantee the browser unload happens
                    delete e['returnValue'];
                    windowObjectReference.close();
                    ws.send(JSON.stringify({'status': 'terminated'}));
                });

            };

            connect();

        </script>
    </body>
    </html>
    """

    response = await make_response(html)
    response.set_cookie("X-Authorization", "R3YKZFKBVi2")
    return response

