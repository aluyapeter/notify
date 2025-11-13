from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from dotenv import load_dotenv

from app.routes.user import user_router
from app.database.db_schema import create_table, DATABASE_URL
from app.models.user import logger

load_dotenv()

app = FastAPI(
    title="User Service API",
    description="Handles user signup, authentication, and profile management.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_connection: asyncpg.Connection | None = None


@app.on_event("startup")
async def startup_event():
    """
    Create DB connection and tables on app startup.
    """
    global db_connection
    try:
        db_connection = await asyncpg.connect(DATABASE_URL)
        logger.info("Database connected successfully.")
        await create_table()
        logger.info("Tables created or verified successfully.")
    except Exception as e:
        logger.error("Startup error: %s", e, exc_info=True)
        raise


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Pings the database to ensure service is healthy.
    """
    global db_connection
    try:
        await db_connection.execute("SELECT 1;")
        return {"status": "ok"}
    except Exception as e:
        logger.error("Health check failed: %s", e, exc_info=True)
        return {"status": "unhealthy"}


app.include_router(user_router)
