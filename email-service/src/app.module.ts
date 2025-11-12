import { Module } from "@nestjs/common";
import { ConfigService } from "./config/config.service";
import { TemplateService } from "./template/template.service";
import { EmailService } from "./email/email.service";
import { ConsumerService } from "./consumer/consumer.service";

@Module({
  providers: [
    ConfigService, // ← MUST BE FIRST
    TemplateService,
    EmailService,
    ConsumerService,
  ],
})
export class AppModule {}
