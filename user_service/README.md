# User Service

The **User Service** handles user registration, authentication, and preference management for the notification system.  
It's built with **FastAPI**, **PostgreSQL**, and **JWT authentication**, and is designed to run as a microservice in a containerized environment.

---

## Features

- User registration and login  
- Secure password hashing with **bcrypt**  
- JWT-based authentication and authorization  
- User preference storage and retrieval  
- Health check endpoint for monitoring  
- Dockerized for easy deployment

---

## Tech Stack

- **Framework:** FastAPI  
- **Database:** PostgreSQL  
- **Auth:** JWT (JSON Web Tokens)  
- **Containerization:** Docker, Docker Compose  
- **Environment Management:** python-dotenv  

---

## Project Structure

```
user-service/
├── app/
│   ├── routes/
│   │   └── user.py              # User-related API routes
│   ├── services/
│   │   └── auth.py              # JWT generation and verification
│   ├── models/
│   │   └── user.py              # User model & logging setup
│   ├── schema/
│   │   └── user.py              # Pydantic schemas
│   └── __init__.py
├── .env                         # Environment variables
├── Dockerfile                   # Docker image definition
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## Environment Variables

Create a `.env` file in the root directory:

```bash
DATABASE_URL=postgres://postgres:password@user-db:5432/postgres
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
```

---

## Running with Docker

### 1. Build and Start Containers

```bash
docker-compose up --build
```

### 2. Check the service

```bash
http://localhost:8000/health
```

Expected response:

```json
{"status": "ok"}
```

### 3. API Docs

Visit:

```bash
http://localhost:8000/docs
```

Interactive Swagger UI will appear for testing endpoints.

---

## Authentication Flow

### Register

**POST** `/users/`

Request body:

```json
{
  "success": true,
  "message": "user signed up successfully",
  "user" : {
    "name": "cipher",
    "email": "cipher@example.com",
    "password": "securepassword",
    "preferences": {}
  }
}
```

Response: `201 Created`

### Login

**POST** `/users/login`

Request body:

```json
{
  "email": "cipher@example.com",
  "password": "securepassword"
}
```

Response:

```json
{
  "success": true,
  "message": "User logged in successfully",
  "user": {
    "user_id": "uuid",
    "name": "cipher",
    "email": "cipher@example.com",
    "token": "<jwt_token>",
    "preferences": {},
    "created_at": "2025-11-11T00:00:00"
  }
}
```

### Protected Routes

Add the token to headers:

```
Authorization: Bearer <jwt_token>
```

---

## Example Request (using Python requests)

```python
import requests

# Register
register_url = "http://localhost:8000/users/"
register_data = {
    "name": "cipher",
    "email": "cipher@example.com",
    "password": "securepassword",
    "preferences": {}
}
response = requests.post(register_url, json=register_data)
print(response.json())

# Login
login_url = "http://localhost:8000/users/login"
login_data = {
    "email": "cipher@example.com",
    "password": "securepassword"
}
response = requests.post(login_url, json=login_data)
print(response.json())
```

---

## Health Check

Endpoint:

```bash
GET /health
```

Response:

```json
{"status": "ok"}
```

---

## Development Notes

- To rebuild containers after making changes:

  ```bash
  docker-compose up --build
  ```

- Use `docker logs user-service-1` to check logs.

- Consider using PostgreSQL JSONB column for preferences to avoid manual `json.loads()`.

- All imports use absolute paths (e.g., `from app.services.auth import ...`)

---

## Author

Cipher