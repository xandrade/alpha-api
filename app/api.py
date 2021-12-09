from typing import final
from models import Friends

from quart import Blueprint, jsonify, request
from email_validator import validate_email, caching_resolver, EmailNotValidError

import asyncio


api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/", methods=["GET"])
async def list_all():
    friends = await Friends.all()
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
        return jsonify(
            {"status": "error", "message": "Uh Oh! Something went wrong"}, 400
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
