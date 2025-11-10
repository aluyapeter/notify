import os
from dotenv import load_dotenv
import asyncpg
import logging

load_dotenv()

logger = logging.getLogger(__name__)

DB_HOST = os.getenv("USER_DB_HOST")
DB_NAME = os.getenv("USER_DB_NAME")
DB_USER = os.getenv("USER_DB_USER")
DB_PASS = os.getenv("USER_DB_PASS")
DB_PORT = os.getenv("USER_DB_PORT")

DATABASE_URL = f"postgres://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def get_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()