from app.utils.logging import setup_logging
from typing import Tuple

logger = setup_logging()

def classify_document(text: str, entities: dict) -> Tuple[str, float]:
    try:
        # Mock rule-based classification for hackathon
        # TODO: Replace with LLM-based classification (e.g., OpenAI) for production
        text_lower = text.lower()
        confidence = 0.8  # Default confidence
        
        if "invoice" in text_lower or "amount" in entities:
            return "invoice", confidence
        elif "contract" in text_lower or "party" in entities:
            return "contract", confidence + 0.1
        else:
            return "unknown", 0.5
        
        logger.info("Classified document")
    except Exception as e:
        logger.error(f"Failed to classify document: {e}")
        raise