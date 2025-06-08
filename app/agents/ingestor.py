import pika
import json
from threading import Thread
from app.message_bus.bus import MessageBus
from app.message_bus.events import DocReceivedEvent
from app.utils.logging import setup_logging
from app.services.llm import summarize_email_body

logger = setup_logging()

def ingestor_worker():
    message_bus = MessageBus()
    channel, queue_name = message_bus.subscribe("doc.initialize")
    
    def callback(ch, method, properties, body):
        try:
            event = DocReceivedEvent.parse_raw(body)
            
            # Determine priority based on metadata(to be modified)
            metadata = event.metadata
            event.priority = "low"
            if metadata.get("sender") == "urgent@example.com":
                event.priority = "high"
            elif int(metadata.get("file_size", "0")) > 10 * 1024 * 1024:  # >10MB
                event.priority = "medium"
            
            # Placeholder for LLM summarization (optional)

            if(metadata.get("input_type") == "email_hook"):
                summary = summarize_email_body(metadata.get("email_body", ""))
                event.metadata["email_body"] = summary
            
            logger.info(f"Processed document {event.doc_id} ({event.file_name}) with priority {event.priority}")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            # TODO: Publish to next stage if needed (Extractor will subscribe directly)
            logger.warning(event.json())
            message_bus.publish("doc.received", event.json())
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid event data: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    try:
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        logger.info("Ingestor worker started consuming messages")
        channel.start_consuming()
    except pika.exceptions.AMQPError as e:
        logger.error(f"Error in message consumption: {e}")
    finally:
        message_bus.close()

def start_ingestor():
    thread = Thread(target=ingestor_worker, daemon=True)
    thread.start()
    logger.info("Ingestor worker started")