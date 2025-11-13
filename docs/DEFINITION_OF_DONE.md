# Definition of Done (Checklist)

A service is not "finished" until it meets these minimum requirements.
All PRs must be checked against this list.

### All Services
- [ ] **Docker:** Has a working `Dockerfile`.
- [ ] **Compose:** Is added to the root `docker-compose.yml` with ports, env vars, and healthcheck.
- [ ] **Healthcheck:** Has a `GET /health` endpoint (even workers should have a simple HTTP server for this).
- [ ] **Config:** All secrets/config are read from environment variables (no hardcoded values).
- [ ] **Contracts:** All JSON payloads (request/response) strictly follow the `snake_case` convention.
- [ ] **Logging:** Logs requests and errors. *Must* include Correlation IDs if provided.

---

### 1. API Gateway
- [ ] **Rate Limiting:** `429 Too Many Requests` error is working.
- [ ] **Status DB:** All requests are logged to `notification_logs` as `pending`.
- [ ] **Status Endpoints:** `GET /status/{id}` and `POST /.../status` webhooks are working.
- [ ] **Publishing:** Correctly publishes to `notifications.direct` exchange.
- [ ] **Real User Fetch:** Mocks for User Service are **removed** and replaced with a real `httpx` call to `http://user-service:8001/...`.
- [ ] **Auth:** Validates incoming `Authorization` headers (JWTs). Rejects with `401 Unauthorized` if invalid.

### 2. User Service
- [ ] **DB:** Has its own PostgreSQL DB (`user-db`).
- [ ] **Signup:** `POST /api/v1/users/` works and **hashes the password** (e.g., with `bcrypt` or `argon2`).
- [ ] **Login:** `POST /api/v1/users/login` works (checks hash) and returns a **JWT Access Token**.
- [ ] **Get User:** `GET /api/v1/users/{id}` returns user email, preferences, and push tokens (but **never** the password hash).
- [ ] **Preferences:** DB model contains `email: bool` and `push: bool` preferences.

### 3. Template Service
- [ ] **DB:** Has its own PostgreSQL DB (`template-db`).
- [ ] **CRUD:** `POST /api/v1/templates` (create) and `GET /api/v1/templates/{template_code}` (read) endpoints exist.
- [ ] **Rendering:** The `GET` endpoint can optionally take `variables` and return the *rendered* template.
- [ ] **Language:** Supports multiple languages (e.g., via a `lang` query parameter).

### 4. Email Service (Worker)
- [ ] **Consumer:** Connects to RabbitMQ and consumes messages from `email.queue`.
- [ ] **Template Fetch:** Makes an `httpx` call to the Template Service (`http://template-service:8002/...`) to get the template.
- [ ] **Render:** Renders the template with variables from the message.
- [ ] **Send:** Sends the email via a 3rd party API (Mailgun, SendGrid).
- [ ] **Status Update:** Makes an `httpx` call to the Gateway's webhook (`http://api-gateway:8000/api/v1/email/status/`) with "delivered" or "failed".
- [ ] **Retry/DLQ:** Failed messages are retried, and permanent failures are sent to the `failed.queue`.

### 5. Push Service (Worker)
- [ ] **Consumer:** Connects to RabbitMQ and consumes messages from `push.queue`.
- [ ] **Send:** Sends the push notification via a 3rd party (FCM).
- [ ] **Status Update:** Makes an `httpx` call to the Gateway's webhook (`http://api-gateway:8000/api/v1/push/status/`).
- [ ] **Retry/DLQ:** Failed messages are retried/sent to DLQ.