"""Database module."""
from app.db.mongodb import (
    connect_to_mongo,
    close_mongo_connection,
    get_database,
    init_db_indexes,
    db_client,
)

__all__ = [
    "connect_to_mongo",
    "close_mongo_connection",
    "get_database",
    "init_db_indexes",
    "db_client",
]

