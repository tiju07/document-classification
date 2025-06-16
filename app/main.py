from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.utils.config import settings
from app.utils.logging import setup_logging
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.ingestion import router as ingestor_router
from app.database.db import engine
from app.models.document import Base
from app.agents.ingestor import start_ingestor
from app.api.v1.routes.documents import router as documents_router
from app.message_bus.bus import MessageBus
from app.agents.extractor import start_extractor
from app.agents.classifier import start_classifier
from app.agents.router import start_router
from dotenv import load_dotenv, find_dotenv
from app.utils.websocket import document_clients, mailbox_clients


load_dotenv(find_dotenv())

# Initialize logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health_router)
app.include_router(ingestor_router)
app.include_router(documents_router)


# WebSocket endpoint for document status updates
@app.websocket("/ws/documents")
async def websocket_documents(websocket: WebSocket):
    await websocket.accept()
    document_clients.add(websocket)
    try:
        while True:
            # Keep connection alive; clients can send pings if needed
            await websocket.receive_text()
    except WebSocketDisconnect:
        document_clients.remove(websocket)

# WebSocket endpoint for mailbox connection updates
@app.websocket("/ws/mailbox")
async def websocket_mailbox(websocket: WebSocket):
    await websocket.accept()
    mailbox_clients.add(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        mailbox_clients.remove(websocket)

async def broadcast_document_update(document: Dict):
    message = {
        "doc_id": document["doc_id"],
        "status": document["status"],
        "type": document.get("type"),
        "confidence": document.get("confidence"),
        "destination": document.get("destination"),
        "last_updated": document["last_updated"],
    }
    disconnected_clients = set()
    for client in document_clients:
        try:
            await client.send_json(message)
        except:
            disconnected_clients.add(client)
    # Clean up disconnected clients
    document_clients.difference_update(disconnected_clients)

# Broadcast mailbox update to all connected mailbox clients
async def broadcast_mailbox_update(config_id: str, status: str, message: str, doc_id: str = None):
    message = {
        "config_id": config_id,
        "status": status,
        "message": message,
        "doc_id": doc_id,
    }
    disconnected_clients = set()
    for client in mailbox_clients:
        try:
            await client.send_json(message)
        except:
            disconnected_clients.add(client)
    # Clean up disconnected clients
    mailbox_clients.difference_update(disconnected_clients)


@app.on_event("startup")
async def startup_event():
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    # Start Ingestor worker
    start_ingestor()
    start_extractor()
    start_classifier()
    start_router()
    logger.info("Starting Document Ingestion System")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Document Ingestion System")