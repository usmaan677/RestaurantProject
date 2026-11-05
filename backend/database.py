import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import pymysql
from pymysql.connections import Connection


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        required = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise RuntimeError(
                "Missing database environment variable(s): " + ", ".join(missing)
            )

        try:
            port = int(os.getenv("DB_PORT", "3306"))
        except ValueError as exc:
            raise ValueError("DB_PORT must be an integer") from exc

        if not 1 <= port <= 65535:
            raise ValueError("DB_PORT must be between 1 and 65535")

        return cls(
            host=os.environ["DB_HOST"],
            port=port,
            name=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        )


def get_connection() -> Connection:
    settings = DatabaseSettings.from_env()
    return pymysql.connect(
        host=settings.host,
        port=settings.port,
        database=settings.name,
        user=settings.user,
        password=settings.password,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=5,
    )


@contextmanager
def connection_scope() -> Iterator[Connection]:
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
