import { Injectable, Logger, OnModuleInit } from "@nestjs/common";
import * as nodemailer from "nodemailer";
import { EmailNotificationDto } from "./email.dto";
import { TemplateService } from "../template/template.service";
import { ConfigService } from "../config/config.service";
import { CircuitBreaker } from "./circuit-breaker";

@Injectable()
export class EmailService implements OnModuleInit {
  private readonly logger = new Logger(EmailService.name);
  private transporter: nodemailer.Transporter;
  private circuitBreaker: CircuitBreaker;

  constructor(
    private readonly template: TemplateService,
    private readonly config: ConfigService
  ) {
    this.circuitBreaker = new CircuitBreaker("SMTP", 5, 60000);
  }

  async onModuleInit() {
    this.transporter = nodemailer.createTransport({
      host: this.config.get("SMTP_HOST"),
      port: this.config.getNumber("SMTP_PORT"),
      secure: false,
      auth: {
        user: this.config.get("SMTP_USER"),
        pass: this.config.get("SMTP_PASS"),
      },
    });

    try {
      await this.transporter.verify();
      this.logger.log(" SMTP server ready");
    } catch (error) {
      this.logger.error(" SMTP connection failed:", error.message);
    }
  }

  async sendEmail(notification: EmailNotificationDto): Promise<void> {
    const logPrefix = `[${notification.request_id}]`;
    this.logger.log(`${logPrefix} 📧 Processing email`);

    await this.circuitBreaker.execute(async () => {
      const template = await this.template.getTemplate(
        notification.template_code
      );
      const rendered = this.template.renderTemplate(
        template,
        notification.variables
      );

      const info = await this.transporter.sendMail({
        from: this.config.get("SMTP_USER"),
        to: notification.user_email,
        subject: rendered.subject,
        html: rendered.body,
      });

      this.logger.log(`${logPrefix} Email sent: ${info.messageId}`);
    });
  }

  getCircuitState(): string {
    return this.circuitBreaker.getState();
  }

  getCircuitFailures(): number {
    return this.circuitBreaker.getFailureCount();
  }
}
