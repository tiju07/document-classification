from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.document import Document
from app.message_bus.bus import MessageBus
from app.message_bus.events import DocTypeEvent, DocRoutedEvent
from app.utils.logging import setup_logging
from app.api.v1.schemas import DocumentStatusResponse, DocumentOverrideRequest

router = APIRouter(prefix="/documents", tags=["documents"])
logger = setup_logging()

@router.get("/{doc_id}", response_model=DocumentStatusResponse)
async def get_document_status(doc_id: str, db: Session = Depends(get_db)):
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"Retrieved status for document {doc_id}")
        return DocumentStatusResponse(
            doc_id=document.id,
            filename=document.name,
            status=document.status,
            type=document.type,
            confidence=document.confidence,
            destination=document.destination
        )
    except Exception as e:
        logger.error(f"Failed to retrieve status for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document status")
    
@router.get("", response_model=List[DocumentStatusResponse])
async def get_all_documents(db: Session = Depends(get_db)):
    try:
        documents = db.query(Document).all()
        if not documents:
            return []
        
        logger.info("Retrieved all documents from database")
        return [
            DocumentStatusResponse(
                doc_id=doc.id,
                filename=doc.name,
                status=doc.status,
                type=doc.type,
                confidence=doc.confidence,
                destination=doc.destination
            )
            for doc_id, doc in enumerate(documents)
        ]
    except Exception as e:
        logger.error(f"Failed to retrieve all documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")

@router.put("/{doc_id}/override")
async def override_document(
    doc_id: str,
    override: DocumentOverrideRequest,
    db: Session = Depends(get_db)
):
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if at least one field is provided
        if override.type is None and override.confidence is None and override.destination is None:
            raise HTTPException(status_code=400, detail="At least one field (type, confidence, destination) must be provided")
        
        message_bus = MessageBus()
        updated = False
        
        # Update type and confidence if provided
        if override.type is not None or override.confidence is not None:
            if override.type is not None:
                document.type = override.type
            if override.confidence is not None:
                document.confidence = override.confidence
            document.status = "classified"
            updated = True
            
            # Publish DocTypeEvent if type or confidence changed
            if override.type is not None:
                type_event = DocTypeEvent(
                    doc_id=doc_id,
                    type=document.type,
                    score=override.confidence or document.confidence or 1.0
                )
                message_bus.publish("doc.type", type_event.json())
                logger.info(f"Overridden type for document {doc_id} to {document.type}")
        
        # Update destination if provided
        if override.destination is not None:
            document.destination = override.destination
            document.status = "routed"
            updated = True
            
            # Publish DocRoutedEvent
            routed_event = DocRoutedEvent(
                doc_id=doc_id,
                destination=override.destination,
                status="routed"
            )
            message_bus.publish("doc.routed", routed_event.json())
            logger.info(f"Overridden destination for document {doc_id} to {override.destination}")
        
        # Commit changes if any updates were made
        if updated:
            db.commit()
            db.refresh(document)
        
        message_bus.close()
        return {"message": "Document overridden successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to override document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to override document")