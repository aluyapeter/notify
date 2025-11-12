import {
  Injectable,
  Logger,
  OnModuleInit,
  OnModuleDestroy,
} from "@nestjs/common";
import * as amqp from "amqplib";
import axios from "axios";
import { EmailService } from "../email/email.service";
import { ConfigService } from "../config/config.service";
import { EmailNotificationDto } from "../email/email.dto";

@Injectable()
export class ConsumerService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(ConsumerService.name);
  private channel: amqp.Channel;
  private connection: amqp.Connection;
  private gatewayUrl: string;

  constructor(
    private readonly email: EmailService,
    private readonly config: ConfigService
  ) {
    const gatewayPort = this.config.get("GATEWAY_PORT");
    this.gatewayUrl = `http://api-gateway:${gatewayPort}`;
  }

  async onModuleInit() {
    await this.connectToRabbitMQ();
    await this.startConsuming();
  }

  private async connectToRabbitMQ(maxRetries = 10): Promise<void> {
    const host = this.config.get("RABBITMQ_HOST");
    const user = this.config.get("RABBITMQ_DEFAULT_USER");
    const pass = this.config.get("RABBITMQ_DEFAULT_PASS");
    const url = `amqp://${user}:${pass}@${host}:5672`;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        this.connection = await amqp.connect(url);
        this.channel = await this.connection.createChannel();
        await this.channel.assertQueue("email.queue", { durable: true });
        this.channel.prefetch(1);
        this.logger.log("Connected to RabbitMQ");
        return;
      } catch (error) {
        this.logger.error(`Connection attempt ${attempt}/${maxRetries} failed`);
        if (attempt < maxRetries) {
          await new Promise((resolve) => setTimeout(resolve, 3000));
        }
      }
    }
    throw new Error("Failed to connect to RabbitMQ");
  }

  private async startConsuming(): Promise<void> {
    this.logger.log(" Listening for email notifications...");

    this.channel.consume("email.queue", async (msg) => {
      if (!msg) return;
      await this.processMessage(msg);
    });
  }

  private async processMessage(msg: amqp.ConsumeMessage): Promise<void> {
    const notification: EmailNotificationDto = JSON.parse(
      msg.content.toString()
    );
    const retryCount = msg.properties.headers?.["x-retry-count"] || 0;

    this.logger.log(
      `[${notification.request_id}] Received (attempt ${retryCount + 1}/4)`
    );

    try {
      await this.email.sendEmail(notification);
      await this.reportStatus(notification.request_id, "delivered", null);
      this.channel.ack(msg);
    } catch (error) {
      this.logger.error(
        `[${notification.request_id}] Failed: ${error.message}`
      );

      if (retryCount < 3) {
        const delay = Math.pow(2, retryCount) * 1000;
        setTimeout(() => {
          this.channel.publish("notifications.direct", "email", msg.content, {
            headers: { "x-retry-count": retryCount + 1 },
          });
          this.channel.ack(msg);
        }, delay);
      } else {
        await this.reportStatus(
          notification.request_id,
          "failed",
          error.message
        );
        await this.channel.assertQueue("failed.queue", { durable: true });
        this.channel.sendToQueue("failed.queue", msg.content);
        this.channel.ack(msg);
      }
    }
  }

  private async reportStatus(
    requestId: string,
    status: string,
    error: string | null
  ): Promise<void> {
    try {
      await axios.post(`${this.gatewayUrl}/api/v1/email/status/`, {
        notification_id: requestId,
        status: status,
        timestamp: new Date().toISOString(),
        error: error,
      });
      this.logger.log(`[${requestId}] Status '${status}' reported`);
    } catch (err) {
      this.logger.warn(`[${requestId}] Failed to report status`);
    }
  }

  async onModuleDestroy() {
    if (this.channel) await this.channel.close();
    if (this.connection) await this.connection.close();
  }
}
