from pydantic import BaseModel
from typing import List, Optional

class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: str

class DocumentStatusResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    type: Optional[str]
    confidence: Optional[float]
    destination: Optional[str]

class DocumentOverrideRequest(BaseModel):
    type: Optional[str] = None
    confidence: Optional[float] = None
    destination: Optional[str] = None

class Attachment(BaseModel):
    filename: str
    content: str  # Base64-encoded content
    content_type: str

class EmailWebhookPayload(BaseModel):
    from_email: str
    subject: Optional[str]
    attachments: List[Attachment]