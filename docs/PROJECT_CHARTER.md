# PROJECT CHARTER: Notify: A Distributed Notification System

**Project:** Distributed Notification System
**Date:** 9 November 2025
**Distribution:** Saint, Adeneey_Dev, Cipher, Ehiz.aza

## 1. 🎯 Project Goal

To build a scalable, fault-tolerant notification system composed of five (5) microservices. This system will process requests asynchronously via a message queue (RabbitMQ) and be capable of handling email and push notifications.

This is a polyglot project. You can write your service in any language you choose (Python, Go, Node.js, PHP, etc.). Because of this, our success depends 100% on a non-negotiable set of rules for communication and operation.

**Our guiding principle: Contracts are King.**

## 2. 🏛️ Core Technical Principles (The "Law")

If you violate these principles, you will break the system for everyone.

* **Contracts First:** Before a single line of code is written, we will define the API and message contracts. These are documented in Section 7. If you need a change, you must propose it to the team and get approval before implementing it.
* **Docker is Mandatory:** Your service must run in a Docker container. There are no exceptions. This is the only way we can guarantee a service works regardless of its language. You are responsible for writing and maintaining your service's Dockerfile.
* **JSON is Our Lingua Franca:** All communication must be in JSON.
    * All REST API request/response bodies.
    * All RabbitMQ message payloads.
* **No Shared Databases:** Each service must own its own database. You are forbidden from directly connecting to another service's database. This is the cardinal sin of microservices.
* **Expose a `/health` Endpoint:** Every service must have a `GET /health` endpoint that returns a 200 OK if it's healthy. This is non-negotiable for system monitoring.
* **Use the Shared Response Format:** All API responses must conform to the standard format defined in Section 7.

## 3. 🗺️ System Architecture

This is the high-level map. The detailed "Contract" is in Section 7.

1.  **Client:** Sends a `POST` request to the API Gateway.
2.  **API Gateway:** Validates the request, fetches user data (Sync), then publishes a message to RabbitMQ (Async) and returns a `202 Accepted` response.
3.  **User Service:** Manages user data. Exposes a REST API.
4.  **Template Service:** Manages templates. Exposes a REST API.
5.  **RabbitMQ:** Receives messages and routes them to the correct queue.
6.  **Email Service:** Consumes from `email.queue`, fetches a template (Sync), and sends an email.
7.  **Push Service:** Consumes from `push.queue` and sends a push notification.

(You will add the diagram you created in Module 0 here.)

## 4. 🧑‍💻 Service Ownership & Team Roles

We will use a single GitHub repository (monorepo) to make management of Docker and contracts easier. Each service will live in its own top-level directory.

The team is split by service ownership. You are the CEO of your service. You are responsible for:
* Choosing the language/framework.
* Writing the code.
* Writing the Dockerfile.
* Writing all tests for your service.
* Adhering to the agreed-upon contracts.

### Service Assignments:
* **Owner 1 (Saint):** API Gateway Service
* **Owner 2 (Team Member 2):** User Service
* **Owner 3 (Team Member 3):** Template Service
* **Owner 4 (Team Member 4):** Email Service + Push Service

(Note: The Email and Push services are both consumer-workers. Their logic is similar, making them a good pair for one owner.)

## 5. 🛠️ GitHub & Collaboration Workflow

We will follow a strict, professional Git workflow.

### Repo Structure
Our single repository will look like this:
```
/distributed-notification-system
├── .github/workflows/         # CI/CD workflows
├── /api-gateway/
│   ├── Dockerfile
│   └── (service code...)
├── /user-service/
│   ├── Dockerfile
│   └── (service code...)
├── /template-service/
│   ├── Dockerfile
│   └── (service code...)
├── /email-service/
│   ├── Dockerfile
│   └── (service code...)
├── /push-service/
│   ├── Dockerfile
│   └── (service code...)
├── /docs/
│   ├── openapi.yml            # THE API LAW
│   ├── message_schemas.json   # THE MESSAGE LAW
│   └── PROJECT_CHARTER.md     # This file
├── .dockerignore
├── .gitignore
├── docker-compose.yml         # Runs the *entire* system
└── README.md
```

### Git & PR Workflow
* **`main` Branch:** This branch is LOCKED. It represents production. Nobody pushes directly to `main`.
* **`develop` Branch:** This is our integration branch. All work is merged here first.
* **Feature Branches:** All new work must be on a feature branch.
    * **Naming:** `[your-name]/[service-name]/[feature-description]`
    * **Example:** `dave/user-service/add-preferences-endpoint`

### The Pull Request (PR) Process
1.  Pull the latest `develop` branch.
2.  Create your feature branch from `develop`: `git checkout -b your-name/service/feature-name develop`
3.  Do your work. Write your code, Dockerfile, and tests.
4.  Run the entire system locally with `docker-compose up --build` to ensure you broke nothing.
5.  Push your feature branch: `git push origin your-name/service/feature-name`
6.  Open a Pull Request (PR) on GitHub, merging from `your-feature-branch -> develop`.
7.  In the PR description, explain what you did and how to test it.
8.  You must get at least one (1) approval from another team member.
9.  Once approved (and if CI/CD passes), you can merge your PR into `develop`.

## 6. 🔑 Common Configuration & Variables

We will use a `.env.example` file at the project root for all shared and service-specific environment variables. Each developer will copy this to their own `.env` file (which is in `.gitignore`).

**`/.env.example`**
```ini
# --- SHARED VARIABLES ---
# All services must use these to connect to shared tools
RABBITMQ_HOST=rabbitmq
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
REDIS_HOST=redis

# --- SERVICE PORTS ---
# (So we don't have conflicts)
GATEWAY_PORT=8000
USER_SERVICE_PORT=8001
TEMPLATE_SERVICE_PORT=8002
EMAIL_SERVICE_PORT=8003
PUSH_SERVICE_PORT=8004

# --- SERVICE-SPECIFIC VARS ---
# User Service
USER_DB_HOST=user-db
USER_DB_NAME=user_db
USER_DB_USER=user
USER_DB_PASS=password

# Template Service
TEMPLATE_DB_HOST=template-db
TEMPLATE_DB_NAME=template_db
TEMPLATE_DB_USER=user
TEMPLATE_DB_PASS=password

# Email Service
MAILGUN_API_KEY=your_key_here

# Push Service
FCM_SERVER_KEY=your_key_here
```

## 7. 📜 The Contracts (The "Dictionary")

This is the most important section. This is our law.

### 7.1. Standard API Response Format
All API responses must use this JSON structure.
```json
{
  "success": true,
  "message": "User retrieved successfully",
  "data": {
    "user_id": "uuid-1234",
    "email": "user@example.com",
    "preferences": { "email": true, "push": false }
  },
  "error": null,
  "meta": null
}
```
* **`success` (boolean):** `true` for 2xx responses, `false` for 4xx/5xx.
* **`message` (string):** Human-readable summary.
* **`data` (object | array | null):** The payload.
* **`error` (string | null):** Error code or message (e.g., `VALIDATION_ERROR`).
* **`meta` (object | null):** Use for pagination data.

### 7.2. API Contracts (OpenAPI)
These will be formally defined in `docs/openapi.yml`.

| Service | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| API Gateway | `/notifications` | `POST` | The main entry point to send a notification. |
| User Service | `/users/{user_id}` | `GET` | Get a single user's details and preferences. |
| User Service | `/users` | `POST` | Create a new user. |
| Template Service | `/templates/{template_name}` | `GET` | Get the content of a specific template. |
| All Services | `/health` | `GET` | Returns `{"status": "ok"}` if healthy. |

### 7.3. Message Queue Contracts (JSON)
These are the exact JSON payloads to be published to RabbitMQ.

**Exchange:** `notifications.direct`

**1. Email Message**
* **Routing Key:** `email`
* **Queue:** `email.queue`
* **Payload Schema:**
    ```json
    {
      "request_id": "string (uuid)",
      "user_id": "string",
      "to_email": "string (email)",
      "subject": "string",
      "body_html": "string (html content)",
      "template_variables": {
        "name": "string",
        "order_id": "string",
        "..." : "..."
      }
    }
    ```

**2. Push Message**
* **Routing Key:** `push`
* **Queue:** `push.queue`
* **Payload Schema:**
    ```json
    {
      "request_id": "string (uuid)",
      "user_id": "string",
      "push_token": "string",
      "title": "string",
      "body": "string",
      "image_url": "string (optional)",
      "link_url": "string (optional)"
    }
    ```

**3. Failed Message (Dead-Letter)**
* **Routing Key:** `failed`
* **Queue:** `failed.queue`
* **Payload Schema:**
    ```json
    {
      "failed_service": "string (email or push)",
      "error_message": "string",
      "timestamp": "string (ISO-8601)",
      "original_message": {
        "..." // The full, original JSON payload
      }
    }
    ```

## 8. 🚀 Local Development (Getting Started)

1.  **Clone the Repo:**
    `git clone [repo-url] distributed-notification-system`
    `cd distributed-notification-system`
2.  **Copy the Env File:**
    `cp .env.example .env`
3.  **Fill in Secrets:** Open `.env` and add any real API keys (e.g., Mailgun).
4.  **Agree on Contracts:** As a team, finalise `docs/openapi.yml` and `docs/message_schemas.json`.
5.  **Build Your Service:** Go to your service directory (e.g., `/user-service`). Write your code. Add your `Dockerfile`.
6.  **Add to Docker Compose:** Add your new service and its database (if any) to the root `docker-compose.yml` file.
7.  **Run Everything:** From the root directory, run:
    `docker-compose up --build`