import asyncio
import os
from dotenv import load_dotenv
import asyncpg


load_dotenv()

DB_HOST = os.getenv("USER_DB_HOST")
DB_NAME = os.getenv("USER_DB_NAME")
DB_USER = os.getenv("USER_DB_USER")
DB_PASS = os.getenv("USER_DB_PASS")
DB_PORT = os.getenv("USER_DB_PORT")

DATABASE_URL = f"postgres://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


async def create_table():
    """Create the necessary database table if it does not exist."""
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                push_token VARCHAR(150),
                preferences JSONB,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_table())