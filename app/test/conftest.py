import datetime as dt
import os

import pytest
from tortoise.contrib import test
import asyncio
import uvloop

from app.main import create_app
from tortoise.contrib.test import finalizer, initializer


@pytest.fixture
@pytest.mark.asyncio
async def app():
    app = create_app()
    return app


@pytest.fixture()
def event_loop(client):
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop._selector = 1
    yield loop


@pytest.fixture()
def client(app, event_loop):
    db_url = os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")
    event_loop._selector = 1
    initializer(["app.user.models"], db_url=db_url, app_label="models", loop=event_loop)
    yield app.test_client()
    finalizer()
