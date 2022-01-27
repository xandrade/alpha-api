DATABASE_URL = "sqlite://./db/db.sqlite3"

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "alpha": {
            "models": [
                "app.user.models",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
