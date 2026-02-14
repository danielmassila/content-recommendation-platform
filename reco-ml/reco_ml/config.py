import os


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def db_dsn() -> str:
    host = get_env("DB_HOST")
    port = get_env("DB_PORT", "5432")
    name = get_env("DB_NAME")
    user = get_env("DB_USER")
    password = get_env("DB_PASSWORD")

    return f"host={host} port={port} dbname={name} user={user} password={password}"
