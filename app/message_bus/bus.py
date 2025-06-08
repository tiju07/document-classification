import pika
from app.utils.config import settings
from app.utils.logging import setup_logging

logger = setup_logging()

class MessageBus:
    def __init__(self):
        try:
            credentials = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password)
            parameters = pika.ConnectionParameters(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.exchange = "document_exchange"
            self.channel.exchange_declare(exchange=self.exchange, exchange_type="topic")
            logger.info(f"Connected to RabbitMQ at {settings.rabbitmq_host}:{settings.rabbitmq_port}")
        except pika.exceptions.AMQPError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish(self, routing_key: str, message: str):
        try:
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message
            )
            logger.info(f"Published message to exchange {self.exchange} with routing key {routing_key}")
        except pika.exceptions.AMQPError as e:
            logger.error(f"Failed to publish message to {routing_key}: {e}")
            raise

    def subscribe(self, routing_key: str):
        try:
            # Declare a unique queue for each subscriber
            result = self.channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue
            self.channel.queue_bind(
                exchange=self.exchange,
                queue=queue_name,
                routing_key=routing_key
            )
            logger.info(f"Subscribed to exchange {self.exchange} with routing key {routing_key}")
            return self.channel, queue_name
        except pika.exceptions.AMQPError as e:
            logger.error(f"Failed to subscribe to {routing_key}: {e}")
            raise

    def close(self):
        try:
            self.channel.close()
            self.connection.close()
            logger.info("RabbitMQ connection closed")
        except pika.exceptions.AMQPError as e:
            logger.error(f"Failed to close RabbitMQ connection: {e}")
            raise