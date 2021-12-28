from dotenv import load_dotenv, find_dotenv


def load_enviroment() -> None:
    """Load enviroment variables from .env file."""

    path = find_dotenv()
    if path:
        load_dotenv(path)


if __name__ == "__main__":
    load_enviroment()
