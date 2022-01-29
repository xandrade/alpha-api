"""
python" -m app.migrate_schemes
"""

import os

from app.loader import load_enviroment
from tortoise import run_async


async def do_migratation():
    from aerich import Command

    DATABASE_URL = os.getenv("DATABASE_URL")

    TORTOISE_ORM = {
        "connections": {"default": DATABASE_URL},
        "apps": {
            "models": {
                "models": ["app.user.models", "aerich.models"],
                "default_connection": "default",
            },
        },
    }

    # Tortoise.init_models(TORTOISE_ORM, "models")
    # await Tortoise.generate_schemas()

    command = Command(tortoise_config=TORTOISE_ORM)
    await command.init()
    await command.migrate("--name add_test2")
    await command.upgrade()


if __name__ == "__main__":
    load_enviroment()
    run_async(do_migratation())
