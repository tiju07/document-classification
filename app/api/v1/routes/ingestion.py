from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
import os

from app.database.db import get_db
from app.models.document import Document
from app.message_bus.bus import MessageBus
from app.message_bus.events import DocReceivedEvent
from app.utils.logging import setup_logging
from app.utils.helpers import save_email_attachment, save_uploaded_file
from app.api.v1.schemas import UploadResponse, EmailWebhookPayload


router = APIRouter(prefix="/ingest", tags=["ingestion"])
logger = setup_logging()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Save file to uploads directory
        file_path = save_uploaded_file(file)
        
        # Store document metadata in database
        document = Document(
            id=str(uuid4()),
            name=file.filename,
            status="ingested"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Prepare and publish event
        event = DocReceivedEvent(
            doc_id=document.id,
            file_name=file.filename,
            metadata={
                    "input_type": "file_upload",       # (file_upload, file_share, email_hook)
                    "file_size": str(file.size),
                    "folder": "",                    # If from a file share
                    "sender": "unknown@example.com",   # If from an email
                    "email_body": ""                 #If from an email
                },
            priority=None
        )
        message_bus = MessageBus()
        message_bus.publish("doc.initialize", event.json())
        message_bus.close()
        
        logger.info(f"Uploaded document {file.filename} with ID {document.id}")
        return {"doc_id": document.id, "filename": file.filename, "status": "ingested"}
    except Exception as e:
        logger.error(f"Failed to process upload {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process upload")
    
@router.post("/email")
async def process_email_webhook(payload: EmailWebhookPayload, db: Session = Depends(get_db)):
    try:
        message_bus = MessageBus()
        response = {"message": "Email processed successfully", "documents": []}
        
        # Process each attachment
        for attachment in payload.attachments:
            # Save attachment to uploads directory
            file_path, filename, file_size = save_email_attachment(attachment)
            
            # Store document metadata in database
            document = Document(
                name=filename,
                status="ingested"
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Prepare and publish event
            event = DocReceivedEvent(
                doc_id=document.id,
                file_name=filename,
                metadata={
                    "file_size": str(file_size),
                    "sender": payload.from_email,
                    "subject": payload.subject or "",
                    "source": "email"
                }
            )
            message_bus.publish("doc.received", event.json())
            
            logger.info(f"Ingested email attachment {filename} with ID {document.id}")
            response["documents"].append({"doc_id": document.id, "filename": filename})
        
        message_bus.close()
        return response
    except Exception as e:
        logger.error(f"Failed to process email webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process email webhook")