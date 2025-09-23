# db/connection.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Generator
import contextlib # FIX: ADD THIS IMPORT

from config import DB_CONNECTION_PARAMS # Correct absolute import

@contextlib.contextmanager # FIX: ADD THIS DECORATOR
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Establishes and yields a synchronous database connection.
    Ensures the connection is closed after use.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONNECTION_PARAMS)
        yield conn
    finally:
        if conn:
            conn.close()

@contextlib.contextmanager # FIX: ADD THIS DECORATOR
def get_db_cursor(conn: psycopg2.extensions.connection) -> Generator[RealDictCursor, None, None]:
    """
    Yields a database cursor from an existing connection.
    Ensures the cursor is closed after use.
    """
    cur = None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        yield cur
    finally:
        if cur:
            cur.close()
