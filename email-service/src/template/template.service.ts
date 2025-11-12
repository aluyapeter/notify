import { Injectable, Logger } from "@nestjs/common";
import axios from "axios";
import { ConfigService } from "../config/config.service";

@Injectable()
export class TemplateService {
  private readonly logger = new Logger(TemplateService.name);
  private readonly templateServiceUrl: string;

  constructor(private readonly config: ConfigService) {
    const port = this.config.get("TEMPLATE_SERVICE_PORT");
    this.templateServiceUrl = `http://template-service:${port}`;
  }

  async getTemplate(templateCode: string): Promise<any> {
    this.logger.log(`Fetching template: ${templateCode}`);

    try {
      const response = await axios.get(
        `${this.templateServiceUrl}/api/v1/templates/${templateCode}`,
        { timeout: 5000 }
      );

      return response.data.data;
    } catch (error) {
      this.logger.error(
        `Failed to fetch template ${templateCode}: ${error.message}`
      );
      throw new Error(`Template ${templateCode} not found`);
    }
  }

  renderTemplate(
    template: any,
    variables: Record<string, any>
  ): { subject: string; body: string } {
    let subject = template.subject || "";
    let body = template.body || "";

    for (const [key, value] of Object.entries(variables)) {
      const placeholder = new RegExp(`{{${key}}}`, "g");
      subject = subject.replace(placeholder, String(value));
      body = body.replace(placeholder, String(value));
    }

    return { subject, body };
  }
}
