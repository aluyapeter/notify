import pika
# import json
from .config import settings
from .models import NotificationRequest
from pika.exceptions import AMQPConnectionError

class AMQPPublisher:
    def __init__(self, host, user, password):
        self.credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(host=host, credentials=self.credentials)
        self.connection = None
        self.channel = None
        self.exchange_name = 'notifications.direct'

    def connect(self):
        """Establishes a connection and a channel."""
        try:
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            self.channel.exchange_declare(
                exchange=self.exchange_name, 
                exchange_type='direct',
                durable=True
            )
            print("AMQP Publisher connected and exchange declared.")
        except AMQPConnectionError as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish_message(self, request: NotificationRequest):
        """Publishes a notification request to the correct queue."""
        if not self.channel or self.channel.is_closed:
            print("AMQP connection is closed. Reconnecting...")
            self.connect()

        if request.notification_type == 'email':
            routing_key = 'email'
        elif request.notification_type == 'push':
            routing_key = 'push'
        else:
            print(f"Unknown notification type: {request.notification_type}")
            return

        message_body = request.model_dump_json()

        try:
            self.channel.basic_publish( #type: ignore
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            print(f"Message published to exchange '{self.exchange_name}' with routing key '{routing_key}'")
        except Exception as e:
            print(f"Failed to publish message: {e}")
            # Handle potential reconnection or error
    
    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("AMQP connection closed.")


publisher = AMQPPublisher(
    host=settings.RABBITMQ_HOST,
    user=settings.RABBITMQ_DEFAULT_USER,
    password=settings.RABBITMQ_DEFAULT_PASS
)