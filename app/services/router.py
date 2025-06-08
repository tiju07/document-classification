from app.utils.logging import setup_logging

logger = setup_logging()

def route_document(doc_type: str) -> str:
    try:
        routing_map = {
            "invoice": "accounting_system",
            "contract": "crm_system",
            "unknown": "archive"
        }
        destination = routing_map.get(doc_type, "archive")
        logger.info(f"Routed document of type {doc_type} to {destination}")
        return destination
    except Exception as e:
        logger.error(f"Failed to route document: {e}")
        raise