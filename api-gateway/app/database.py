import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator


DB_USER = os.environ["GATEWAY_DB_USER"]
DB_PASS = os.environ["GATEWAY_DB_PASS"]
DB_HOST = os.environ["GATEWAY_DB_HOST"]
DB_PORT = os.environ["GATEWAY_DB_PORT"]
DB_NAME = os.environ["GATEWAY_DB_NAME"]


DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to create and clean up an AsyncSession.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()