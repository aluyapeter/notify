export class EmailNotificationDto {
  // Core fields from original request (defined in message_schemas.json)
  notification_type: string;
  user_id: string;
  template_code: string;
  variables: {
    name: string;
    link: string;
    meta?: Record<string, any>;
    [key: string]: any;
  };
  request_id: string;
  priority: number;
  metadata?: Record<string, any>;

  // Enriched fields added by API Gateway
  user_email: string;
  timestamp: string;
}
