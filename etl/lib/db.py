import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    name: str


def load_db_config() -> DbConfig:
    return DbConfig(
        host=os.getenv("MONITOR_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("MONITOR_DB_PORT", "3306")),
        user=os.getenv("MONITOR_DB_USER", "monitor"),
        password=os.getenv("MONITOR_DB_PASSWORD", "monitor"),
        name=os.getenv("MONITOR_DB_NAME", "monitor"),
    )
