# Notify: A Distributed Notification System

This project is a scalable, fault-tolerant notification system built with a polyglot microservice architecture. It processes requests asynchronously via RabbitMQ and handles both email and push notifications.

> **Project "Law"**: All team members **must** read the [**Project Charter**](./docs/PROJECT_CHARTER.md) before writing any code. This document contains the non-negotiable rules for our architecture, contracts, and workflow.

## 🏛️ System Architecture

The system is composed of five core services, a message broker, and two databases, all running in Docker containers.

### Services
* **API Gateway:** The single entry point for all client requests. (Owner: Team Member 1)
* **User Service:** Manages user data and notification preferences. (Owner: Team Member 2)
* **Template Service:** Manages and renders notification templates. (Owner: Team Member 3)
* **Email Service:** A worker that consumes from the email queue and sends emails. (Owner: Team Member 4)
* **Push Service:** A worker that consumes from the push queue and sends push notifications. (Owner: Team Member 4)

## 🚀 Getting Started

Follow these steps to build and run the entire system locally.

### Prerequisites

* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone the Repository

```bash
git clone [https://github.com/aluyapeter/notify](https://github.com/aluyapeter/notify)
cd notify
```

### 2. Set Up Environment Variables

Copy the example environment file. **This is a mandatory step** for the services to connect correctly.

```bash
cp .env.example .env
```

Now, open the `.env` file and fill in any missing secrets (like `MAILGUN_API_KEY` or `FCM_SERVER_KEY`).

### 3. Build and Run the System

This single command will build all service images, start all containers, and connect the network.

```bash
docker-compose up --build
```

To run in detached mode (in the background):
```bash
docker-compose up --build -d
```

### 4. Verify the System is Running

**Test 1: Check Container Health**
In a new terminal, check that `rabbitmq` and `redis` are running and healthy.
```bash
docker-compose ps
```
You should see both services listed with `State` as `Up` (or `running`) and `Health` as `healthy`.

**Test 2: Check RabbitMQ Dashboard**
* Open your browser and go to: **[http://localhost:15672](http://localhost:15672)**
* Log in with:
    * **Username:** `guest`
    * **Password:** `guest`

If you can log in and see the dashboard, the infrastructure is working.

## 📜 Project Contracts (The "Law")

This project's stability depends on all services obeying a strict set of contracts. **Do not deviate from these.**

* **Full Project Brief:** The complete project charter, principles, and workflow rules.
    * **Location:** [`/docs/PROJECT_CHARTER.md`](./docs/PROJECT_CHARTER.md)
* **API Contracts:** All REST API definitions are formally documented in the OpenAPI specification.
    * **Location:** [`/docs/openapi.yml`](./docs/openapi.yml)
* **Message Contracts:** All RabbitMQ message payloads are formally defined as JSON Schemas.
    * **Location:** [`/docs/message_schemas.json`](./docs/message_schemas.json)

## 🛠️ Service Directory

| Service | Directory | Owner | Port |
| :--- | :--- | :--- | :--- |
| **API Gateway** | [`/api-gateway/`](./api-gateway/) | Team Member 1 | `8000` |
| **User Service** | [`/user-service/`](./user-service/) | Team Member 2 | `8001` |
| **Template Service**| [`/template-service/`](./template-service/) | Team Member 3 | `8002` |
| **Email Service** | [`/email-service/`](./email-service/) | Team Member 4 | `8003` |
| **Push Service** | [`/push-service/`](./push-service/) | Team Member 4 | `8004` |

## 🧪 Running Tests

To run tests for a specific service, use `docker-compose exec`:

```bash
# Example for a Python service using pytest
docker-compose exec user-service pytest

# Example for a Go service
docker-compose exec user-service go test ./...
```