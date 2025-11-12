import { NestFactory } from "@nestjs/core";
import { AppModule } from "./app.module";
import { Logger } from "@nestjs/common";

async function bootstrap() {
  const logger = new Logger("Bootstrap");
  const app = await NestFactory.create(AppModule);

  const emailService = app.get("EmailService");

  app
    .getHttpAdapter()
    .getInstance()
    .get("/health", (req, res) => {
      res.json({
        success: true,
        message: "Email service is healthy",
        data: {
          status: "ok",
          service: "email-service",
          circuit_breaker: {
            state: emailService.getCircuitState(),
            failures: emailService.getCircuitFailures(),
          },
          timestamp: new Date().toISOString(),
        },
        error: null,
        meta: null,
      });
    });

  const port = process.env.EMAIL_SERVICE_PORT || 8003;
  await app.listen(port, "0.0.0.0");

  logger.log(`Email Service listening on port ${port}`);
}

bootstrap();
