# Distributed Notification System

This project is a scalable, fault-tolerant notification system built with a polyglot microservice architecture.

## ⚠️ Read First!

All project members **must** read the **[Project Charter](/docs/PROJECT_CHARTER.md)** before writing any code. It contains the system architecture, API contracts, message queue schemas, and Git workflow.

The **`develop`** branch is our main working branch. **`main`** is locked.

## 🚀 Getting Started (Local Development)

This repository is a monorepo containing all services, managed by Docker Compose.

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/aluyapeter/notify.git](https://github.com/aluyapeter/notify.git)
    ```

2.  **Navigate to Project Root:**
    ```bash
    cd notify
    ```

3.  **Checkout the `develop` Branch:**
    ```bash
    git checkout develop
    ```

4.  **Copy Environment File:**
    *This is a critical step.*
    ```bash
    cp .env.example .env
    ```

5.  **Build and Run the System:**
    ```bash
    docker-compose up --build
    ```

This command will build all services (starting with `api-gateway`) and start the shared infrastructure (RabbitMQ, Redis, databases). You should see logs from all running containers.

## 🧪 How to Test the System

After running `docker-compose up`, verify the system is working.

### 1. Test Shared Infrastructure

* **RabbitMQ:** Open `http://localhost:15672`. Log in with `guest` / `guest`.
* **Redis:** In a new terminal, run `docker exec -it notify-redis-1 redis-cli ping`. It should reply `PONG`.

### 2. Test the API Gateway ("Happy Path")

This tests that the `api-gateway` is running, validating requests, and publishing to `RabbitMQ`.

* **Tool:** Use Postman, Insomnia, or `curl`.
* **Method:** `POST`
* **URL:** `http://localhost:8000/api/v1/notifications/`
* **Body (raw JSON):**
    ```json
    {
      "notification_type": "email",
      "user_id": "27c2c0e1-73e8-4d2a-b003-145cb090cdfb",
      "template_code": "welcome_email",
      "variables": {
        "name": "Peter",
        "link": "[http://example.com/verify](http://example.com/verify)"
      },
      "request_id": "27c2c0e1-73e8-4d2a-b003-145cb090cdfb",
      "priority": 1
    }
    ```

* **Expected Response (Status `202 Accepted`):**
    ```json
    {
      "success": true,
      "message": "Notification request accepted for processing.",
      "data": {
        "request_id": "27c2c0e1-73e8-4d2a-b003-145cb090cdfb"
      },
      "error": null,
      "meta": null
    }
    ```

* **How to Verify in RabbitMQ:**
    1.  Go to `http://localhost:15672` (RabbitMQ Admin).
    2.  Click the **"Queues"** tab.
    3.  Manually create the queues:
        * Add a new queue named `email.queue`.
        * Add a new queue named `push.queue`.
    4.  Click the **"Exchanges"** tab, then click on `notifications.direct`.
    5.  Under **"Bindings"**:
        * Bind `email.queue` with routing key `email`.
        * Bind `push.queue` with routing key `push`.
    6.  **Re-send your Postman request.**
    7.  Go back to the **"Queues"** tab. You should see "1" under the "Ready" column for `email.queue`. This proves your gateway successfully published the message.

## 🧑‍💻 Your First Contribution (For Teammates)

Now that the `api-gateway` is running, you can build your service.

1.  Pull the latest `develop` branch.
2.  Create your feature branch (e.g., `dave/user-service-skeleton`).
3.  Go to your service's folder (e.g., `/user-service`).
4.  Build your "walking skeleton":
    * Create your app (e.g., `main.py`, `index.js`).
    * Add a `GET /health` endpoint.
    * Add your `Dockerfile`.
5.  Add your service to the root `docker-compose.yml`. Copy the `api-gateway` block as a template.
6.  Run `docker-compose up --build` and prove your new service runs *with* the gateway.
7.  Open a Pull Request to `develop`.