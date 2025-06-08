import base64
import os
from typing import Tuple
from fastapi import UploadFile
from app.api.v1.schemas import Attachment
from app.utils.logging import setup_logging

logger = setup_logging()

def save_uploaded_file(file: UploadFile) -> str:
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as f:
            content = file.file.read()
            f.write(content)
        logger.info(f"Saved file to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save file {file.filename}: {e}")
        raise

def save_email_attachment(attachment: Attachment) -> Tuple[str, str, int]:
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, attachment.filename)
    
    try:
        # Decode base64 content
        content = base64.b64decode(attachment.content)
        file_size = len(content)
        
        # Save to file
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved email attachment to {file_path}")
        return file_path, attachment.filename, file_size
    except Exception as e:
        logger.error(f"Failed to save email attachment {attachment.filename}: {e}")
        raise