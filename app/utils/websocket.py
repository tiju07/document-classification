from typing import Set, Dict, Optional
from fastapi import WebSocket
import json
import asyncio

# Store connected WebSocket clients
document_clients: Set[WebSocket] = set()
mailbox_clients: Set[WebSocket] = set()

async def broadcast_document_update(document: Dict):
    """
    Broadcast document status update to all connected document clients.
    """
    # message = {
    #     "doc_id": document["doc_id"],
    #     "status": document["status"],
    #     "type": document.get("type"),
    #     "confidence": document.get("confidence"),
    #     "destination": document.get("destination"),
    #     "last_updated": document["last_updated"],
    # }

    disconnected_clients = set()
    for client in document_clients:
        try:
            asyncio.create_task(client.send_json(document))
        except:
            disconnected_clients.add(client)
    document_clients.difference_update(disconnected_clients)

async def broadcast_mailbox_update(config_id: str, status: str, message: str, doc_id: Optional[str] = None):
    """
    Broadcast mailbox status update to all connected mailbox clients.
    """
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
    mailbox_clients.difference_update(disconnected_clients)