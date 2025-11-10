import asyncio
import os
from dotenv import load_dotenv
import asyncpg


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def create_tables():
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id UUID PRIMARY KEY,
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
    asyncio.run(create_tables())