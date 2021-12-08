from typing import final
from models import Friends

from quart import Blueprint, jsonify, request
from email_validator import validate_email, caching_resolver, EmailNotValidError
import rsa

import asyncio


PUBLICKEY, PRIVATEKEY = rsa.newkeys(512)


api = Blueprint("api", __name__, url_prefix="/api")


def encrypt(message):
    return rsa.encrypt(message.encode(), PUBLICKEY)


def decrypt(encMessage):
    return rsa.decrypt(encMessage, PRIVATEKEY).decode()


@api.route("/", methods=["GET"])
async def list_all():
    friends = await asyncio.gather(Friends.all())
    return jsonify(
        {
            "friend": [str(items) for friend in friends for items in friend],
        }
    )


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
        return {"status": "error", "message": "Email address is invalid"}, 400

    friend = await Friends.create(name=name, email=email)
    str(friend)
    return jsonify(
        {
            "status": "success",
            "message": "Thanks for subscribing to our Friend list",
        }, 200
    )
