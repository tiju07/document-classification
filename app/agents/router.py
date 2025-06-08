import pika
import json
from threading import Thread
from app.message_bus.bus import MessageBus
from app.message_bus.events import DocTypeEvent, DocRoutedEvent
from app.utils.logging import setup_logging
from app.services.router import route_document
from app.database.db import get_db
from app.models.document import Document
from sqlalchemy.orm import Session

logger = setup_logging()

def router_worker():
    message_bus = MessageBus()
    channel, queue_name = message_bus.subscribe("doc.type")
    
    def callback(ch, method, properties, body):
        try:
            event = DocTypeEvent.parse_raw(body)
            
            # Determine routing destination
            destination = route_document(event.type)
            
            # Update document in database
            db = next(get_db())
            document = db.query(Document).filter(Document.id == event.doc_id).first()
            if document:
                document.status = "routed"
                document.destination = destination
                db.commit()
                db.refresh(document)
            
            # Publish doc.routed event
            routed_event = DocRoutedEvent(
                doc_id=event.doc_id,
                destination=destination,
                status="routed"
            )
            message_bus.publish("doc.routed", routed_event.json())
            logger.warning(routed_event.json())
            
            logger.info(f"Routed document {event.doc_id} to {destination}")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid event data: {e}")
        except Exception as e:
            logger.error(f"Error processing document {event.doc_id}: {e}")
    
    try:
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        logger.info("Router worker started consuming messages")
        channel.start_consuming()
    except pika.exceptions.AMQPError as e:
        logger.error(f"Error in message consumption: {e}")
    finally:
        message_bus.close()

def start_router():
    thread = Thread(target=router_worker, daemon=True)
    thread.start()
    logger.info("Router worker started")