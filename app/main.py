from fastapi import FastAPI
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

load_dotenv(find_dotenv())

# Initialize logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version
)

# Include API routes
app.include_router(health_router)
app.include_router(ingestor_router)
app.include_router(documents_router)

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