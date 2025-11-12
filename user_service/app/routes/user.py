import json
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
import bcrypt

from app.services.auth import get_current_user, generate_token
from app.database.connection import get_db
from app.models.user import create_user, get_user, update_user, logger
from app.schema.user import (
    UserUpdate,
    UserResponse,
    UserLogin,
    UserRequest,
    UserPreference,
    GenericResponse
)

user_router = APIRouter(prefix='/users', tags=["user"])


@user_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    description="Sign up a new user using name, email, password, and preferences.",
    response_model_exclude_none=True
)
async def create_user_route(
    user: UserRequest,
    conn: asyncpg.Connection = Depends(get_db)
):
    """
    Create a new user account.

    Validates user input, checks for existing users, hashes the password,
    and stores the new user record in the database.

    Args:
        user (UserRequest): User signup request body.
        conn (asyncpg.Connection): Database connection dependency.

    Returns:
        GenericResponse: A response containing user details upon success.

    Raises:
        HTTPException:
            - 400 if required fields are missing or user exists.
            - 500 if any internal error occurs.
    """
    try:
        if not all([user.name, user.email, user.password, user.preferences]):
            raise HTTPException(
                status_code=400,
                detail="name, email, preferences, and password are required fields"
            )

        existing = await get_user(conn, email=user.email)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )

        user_record = await create_user(conn, user)

        return GenericResponse(
            success=True,
            message="User created successfully",
            data=UserResponse(
                user_id=user_record['user_id'],
                name=user_record['name'],
                email=user_record['email'],
                push_token=user.push_token,
                preferences=user.preferences,
                created_at=user_record['created_at']
            ).model_dump(exclude_none=True),
            error=None,
            meta=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Exception in create_user_route: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@user_router.post(
    '/login',
    status_code=status.HTTP_200_OK,
    description="Authenticate a user using email and password, returning an access token.",
    response_model_exclude_none=True
)
async def login(
    user: UserLogin,
    conn: asyncpg.Connection = Depends(get_db)
):
    """
    Log in a user and return an access token.

    Verifies email and password, generates a JWT for valid users.

    Args:
        user (UserLogin): Login credentials (email, password).
        conn (asyncpg.Connection): Database connection dependency.

    Returns:
        GenericResponse: Authenticated user details including access token.

    Raises:
        HTTPException:
            - 404 if user not found.
            - 401 if invalid credentials.
            - 500 if any internal error occurs.
    """
    try:
        existing = await get_user(conn, email=user.email)
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")

        if not bcrypt.checkpw(user.password.encode(), existing['password'].encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        preferences_data = existing["preferences"]
        if isinstance(preferences_data, str):
            preferences_data = json.loads(preferences_data)

        return GenericResponse(
            success=True,
            message="User logged in successfully",
            data=UserResponse(
                user_id=existing['user_id'],
                name=existing['name'],
                email=existing['email'],
                push_token=existing['push_token'],
                preferences=UserPreference(**preferences_data),
                access_token=generate_token({
                    "user_id": existing['user_id'],
                    "name": existing['name'],
                    "email": existing['email']
                }),
                created_at=existing['created_at']
            ).model_dump(exclude_none=True),
            error=None,
            meta=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Exception in login route: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@user_router.get(
    '/{user_id}',
    status_code=status.HTTP_200_OK,
    description="Fetch user details by user ID (requires authentication).",
    response_model_exclude_none=True
)
async def get_user_route(
    user_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Retrieve a user's profile by their ID.

    Args:
        user_id (str): ID of the user to fetch.
        conn (asyncpg.Connection): Database connection dependency.
        current_user (dict): Authenticated user information.

    Returns:
        GenericResponse: User details if found.

    Raises:
        HTTPException:
            - 401 if not authenticated.
            - 404 if user not found.
            - 500 if internal error occurs.
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user_record = await get_user(conn, user_id=user_id)
        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        preferences_data = user_record["preferences"]
        if isinstance(preferences_data, str):
            preferences_data = json.loads(preferences_data)

        return GenericResponse(
            success=True,
            message="User retrieved successfully",
            data=UserResponse(
                user_id=user_record['user_id'],
                name=user_record['name'],
                email=user_record['email'],
                push_token=user_record['push_token'],
                preferences=UserPreference(**preferences_data),
                created_at=user_record['created_at']
            ).model_dump(exclude_none=True),
            error=None,
            meta=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Exception in get_user_route: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@user_router.put(
    '/{user_id}',
    response_model=GenericResponse,
    status_code=status.HTTP_200_OK,
    description="Update user profile by user ID (only the authenticated user can update their own profile).",
    response_model_exclude_none=True
)
async def update_user_route(
    user_id: str,
    data: UserUpdate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Update user details for the given user ID.

    Only the authenticated user can update their own profile.

    Args:
        user_id (str): ID of the user to update.
        data (UserUpdate): Updated user information.
        conn (asyncpg.Connection): Database connection dependency.
        current_user (dict): Authenticated user.

    Returns:
        GenericResponse: Updated user record.

    Raises:
        HTTPException:
            - 401 if not authenticated.
            - 403 if attempting to update another user's profile.
            - 404 if user not found.
            - 500 if any internal error occurs.
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        if current_user['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden: You can only update your own profile")

        user_record = await update_user(conn, user_id, data)
        if not user_record:
            raise HTTPException(status_code=404, detail="User not found")

        preferences_data = user_record["preferences"]
        if isinstance(preferences_data, str):
            preferences_data = json.loads(preferences_data)

        return GenericResponse(
            success=True,
            message="User updated successfully",
            data=UserResponse(
                user_id=user_record['user_id'],
                name=user_record['name'],
                email=user_record['email'],
                push_token=user_record['push_token'],
                preferences=UserPreference(**preferences_data),
                created_at=user_record['created_at']
            ).model_dump(exclude_none=True),
            error=None,
            meta=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Exception in update_user_route: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e
