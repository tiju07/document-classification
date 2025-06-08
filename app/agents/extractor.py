import pika
import json
from threading import Thread
from app.message_bus.bus import MessageBus
from app.message_bus.events import DocReceivedEvent, DocTextEvent
from app.utils.logging import setup_logging
from app.services.ocr import extract_text
# from app.services.nlp import clean_text, extract_entities
from app.database.db import get_db
from app.models.document import Document
from sqlalchemy.orm import Session
from app.services.llm import process_file, extract_entities

logger = setup_logging()

def extractor_worker():
    message_bus = MessageBus()
    channel, queue_name = message_bus.subscribe("doc.received")
    
    def callback(ch, method, properties, body):
        try:
            event = DocReceivedEvent.parse_raw(body)
            file_path = f"uploads/{event.file_name}"

            cleaned_text = process_file(file_path)
            
            # Extract entities
            entities = None
            
            entities = extract_entities(event.metadata.get("email_body", "") + "\n" + cleaned_text)
            entities = json.loads(entities)

            # Update document status in database
            db = next(get_db())
            document = db.query(Document).filter(Document.id == event.doc_id).first()
            if document:
                document.status = "extracted"
                db.commit()
                db.refresh(document)
            
            # Publish doc.text event
            text_event = DocTextEvent(
                doc_id=event.doc_id,
                text=cleaned_text,
                entities=entities if not entities == None else {} 
            )
            message_bus.publish("doc.text", text_event.json())
            logger.warning(text_event.json())
            
            logger.info(f"Extracted text and entities for document {event.doc_id} ({event.file_name})")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid event data: {e}")
        except Exception as e:
            logger.error(f"Error processing document {event.doc_id}: {e}")
    
    try:
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        logger.info("Extractor worker started consuming messages")
        channel.start_consuming()
    except pika.exceptions.AMQPError as e:
        logger.error(f"Error in message consumption: {e}")
    finally:
        message_bus.close()

def start_extractor():
    thread = Thread(target=extractor_worker, daemon=True)
    thread.start()
    logger.info("Extractor worker started")