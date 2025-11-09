# Distributed Notification System

This project is a scalable, fault-tolerant notification system built with a polyglot microservice architecture.

## ⚠️ Read First!

All project members **must** read the **[Project Charter](/docs/PROJECT_CHARTER.md)** before writing any code. It contains the system architecture, API contracts, message queue schemas, and Git workflow.

## 🚀 Getting Started (Local Development)

This repository is a monorepo containing all 5 services, managed by Docker Compose.

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/aluyapeter/notify.git](https://github.com/aluyapeter/notify.git)
    ```

2.  **Navigate to Project Root:**
    ```bash
    cd notify
    ```

3.  **Copy Environment File:**
    *This is a critical step.*
    ```bash
    cp .env.example .env
    ```

4.  **Review Environment File (Optional):**
    Open the `.env` file and add any personal API keys (e.g., Mailgun, SendGrid) if you are working on the `email-service`.

5.  **Run the System:**
    ```bash
    docker-compose up --build
    ```

This command will build all services and start the shared infrastructure (RabbitMQ, Redis, databases).

## 🧪 Testing the Skeleton

You can verify the shared infrastructure is running:

* **RabbitMQ:** Open `http://localhost:15672`. Log in with `guest` / `guest`.
* **Redis:** Run `docker exec -it notify-redis-1 redis-cli ping`. It should reply `PONG`.