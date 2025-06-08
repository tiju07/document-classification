import pika
import json
from threading import Thread
from app.message_bus.bus import MessageBus
from app.message_bus.events import DocTextEvent, DocTypeEvent
from app.utils.logging import setup_logging
from app.database.db import get_db
from app.models.document import Document
from sqlalchemy.orm import Session
from app.services.llm import classify_document

logger = setup_logging()

def classifier_worker():
    message_bus = MessageBus()
    channel, queue_name = message_bus.subscribe("doc.text")
    
    def callback(ch, method, properties, body):
        try:
            event = DocTextEvent.parse_raw(body)
            
            # Classify document
            res = classify_document(event.text, str(event.entities))
            res = json.loads(res.strip().removeprefix("```json").removesuffix("```").strip())

            print(res)
            doc_type = res["category"]
            confidence = int(res["confidence_score"])

            # Update document in database
            db = next(get_db())
            document = db.query(Document).filter(Document.id == event.doc_id).first()
            if document:
                document.type = doc_type
                document.confidence = confidence
                document.status = "classified"
                db.commit()
                db.refresh(document)
            
            # Publish doc.type event
            type_event = DocTypeEvent(
                doc_id=event.doc_id,
                type=doc_type,
                score=confidence
            )
            message_bus.publish("doc.type", type_event.json())
            logger.warning(type_event.json())
            logger.info(f"Classified document {event.doc_id} as {doc_type} with confidence {confidence}")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid event data: {e}")
        except Exception as e:
            logger.error(f"Error processing document {event.doc_id}: {e}")
    
    try:
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        logger.info("Classifier worker started consuming messages")
        channel.start_consuming()
    except pika.exceptions.AMQPError as e:
        logger.error(f"Error in message consumption: {e}")
    finally:
        message_bus.close()

def start_classifier():
    thread = Thread(target=classifier_worker, daemon=True)
    thread.start()
    logger.info("Classifier worker started")