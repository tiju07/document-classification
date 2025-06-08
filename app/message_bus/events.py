from pydantic import BaseModel
from typing import Dict, Optional

class DocReceivedEvent(BaseModel):
    doc_id: str
    file_name: str
    metadata: Dict[str, str]
    priority: str | None

class DocTextEvent(BaseModel):
    doc_id: str
    text: str
    entities: Dict

class DocTypeEvent(BaseModel):
    doc_id: str
    type: str
    score: float

class DocRoutedEvent(BaseModel):
    doc_id: str
    destination: str
    status: str