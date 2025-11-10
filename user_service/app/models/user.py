import asyncpg
import json
import uuid
import logging
import bcrypt
from user_service.app.schema.user import UserRequest, UserUpdate

logger = logging.getLogger()


async def create_user(conn: asyncpg.Connection, user: UserRequest):
    """
    This function inserts user into the db using the pydantic UserRequest class of
    ..schema.user hashing password and generating uuid for user_id.

    :param conn: asyncpg.Connection
    :param user:  UserRequest(BaseModel)
    :return: dict: (user_id, created_at)
    """
    try:
        user_id = str(uuid.uuid4())
        hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()

        query = """
            INSERT INTO users (user_id, name, email, push_token, preferences, password)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING user_id, name, email, created_at
        """

        details = await conn.fetchrow(
            query,
            user_id,
            user.name,
            user.email,
            user.push_token,
            json.dumps(user.preferences.dict()),
            hashed
        )

        return dict(details) if details else None

    except Exception as e:
        logger.exception(f"Exception occurred in create_user: {e}")
        return None


async def get_user(conn: asyncpg.Connection, user_id: str):
    """
    this function gets the instance of the user from the db and returns it as a dict
    :param conn: asyncpg.Connection
    :param user_id: str
    :return: user: Dict
    """
    try:
        query = """
            SELECT * FROM users WHERE user_id = $1
        """
        record = asyncpg.Record
        user = await conn.fetchrow(query, user_id)

        return dict(user) if user else None
    except Exception as e:
        logger.error(f"exception occurred in get user: {e}", exc_info=True)


async def update_user(conn: asyncpg.Connection, user_id: str, data: UserUpdate):
    """
    this function updates the user giving room for updating either single or multiple fields

    :param conn: asyncpg.Connection
    :param user_id: str
    :param data:  UserUpdate(BaseModel)
    :return: Dict: user(updated instance)
    """
    try:
        fields = []
        values = []

        if data.name:
            fields.append("name = ${}".format(len(values) + 1))
            values.append(data.name)

        if data.push_token:
            fields.append("push_token = ${}".format(len(values) + 1))
            values.append(data.push_token)

        if data.preferences:
            fields.append("preferences = ${}".format(len(values) + 1))
            values.append(json.dumps(data.preferences.dict()))

        if data.password:
            hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
            fields.append("password = ${}".format(len(values) + 1))
            values.append(hashed)

        if not fields:
            return {"success": False, "message": "No valid fields to update"}

        values.append(user_id)
        query = f"""
            UPDATE users
            SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ${len(values)}
            RETURNING user_id, name, email, push_token, preferences, created_at, updated_at
        """

        result = await conn.fetchrow(query, *values)
        if result:
            return result
        else:
            return None

    except Exception as e:
        logger.exception(f"Error updating user: {e}")
        return {"success": False, "message": "An error occurred while updating user"}

