from typing import Dict, Optional
from app.utils.websocket import broadcast_document_update, broadcast_mailbox_update

async def notify_document_update(document: Dict):
    """
    Notify clients of a document status update.
    Called by agents after updating the database.
    """
    # document = {
    #     "doc_id": id,
    #     "status": status,
    #     "type": type,
    #     "confidence": confidence,
    #     "destination": destination,
    #     "last_updated": updated_at,
    # }
    await broadcast_document_update(document)

async def notify_mailbox_update(config_id: str, status: str, message: str, doc_id: Optional[str] = None):
    """
    Notify clients of a mailbox status update or new email document.
    Called by mailbox agent after processing.
    """
    await broadcast_mailbox_update(config_id, status, message, doc_id)