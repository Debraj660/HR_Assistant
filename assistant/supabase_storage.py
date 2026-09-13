import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from supabase import create_client, Client
from assistant import config
from assistant.logger import get_logger

logger = get_logger(__name__)

# Constants
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


def get_supabase() -> Client:
    """Initialize and return the Supabase client."""
    if not config.SUPABASE_URL:
        raise ValueError("Missing SUPABASE_URL.")
    
    if not config.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("Missing SUPABASE_SERVICE_ROLE_KEY.")

    return create_client(
        config.SUPABASE_URL,
        config.SUPABASE_SERVICE_ROLE_KEY,
    )



# Upload

def upload_document(filename: str, file_bytes: bytes) -> dict:
    """
    Upload a document to Supabase Storage and create its metadata record.

    Returns:
        dict: Document metadata record.
        
    Raises:
        ValueError: If file type is unsupported or file size exceeds limit.
        Exception: If Supabase storage or database operations fail.
    """
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}")

    # Validate file size
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File exceeds maximum size of 20 MB (current: {file_size_mb:.2f} MB)"
        )

    supabase = get_supabase()
    document_id = str(uuid.uuid4())
    storage_path = f"documents/{document_id}/{filename}"

    content_type = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }.get(extension, "application/octet-stream")

    logger.info(
        "Uploading %s to Supabase: %s (Size: %.2f MB)",
        filename, storage_path, file_size_mb
    )

    # 1. Upload File to Storage
    try:
        response = supabase.storage.from_(config.SUPABASE_BUCKET_NAME).upload(
            storage_path,
            file_bytes,
            file_options={"content-type": content_type, "upsert": False},
        )
        
        if response is None:
            raise Exception("Upload returned no response from Supabase")
            
        if hasattr(response, "error") and response.error:
            raise Exception(f"Supabase storage upload error: {response.error}")
        
        logger.info("File uploaded to storage successfully: %s", storage_path)
        
    except Exception as upload_error:
        logger.exception("Storage upload failed for %s: %s", filename, str(upload_error))
        raise

    # 2. Store Metadata in Database
    metadata = {
        "id": document_id,
        "filename": filename,
        "storage_path": storage_path,
        "file_type": extension,
        "file_size": len(file_bytes),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        supabase.table("documents").insert(metadata).execute()
    except Exception as db_error:
        # Rollback storage if database insert fails
        logger.exception("Database insertion failed for %s, rolling back storage upload", filename)
        try:
            supabase.storage.from_(config.SUPABASE_BUCKET_NAME).remove([storage_path])
            logger.info("Storage cleanup successful for %s", storage_path)
        except Exception as cleanup_error:
            logger.exception(
                "Failed to rollback storage file: %s. Manual cleanup may be needed for %s",
                str(cleanup_error), storage_path
            )
        raise

    logger.info(
        "Document uploaded successfully: %s (ID: %s, Size: %.2f MB)",
        filename, document_id, file_size_mb
    )

    return metadata


# List documents

def list_documents() -> list[dict]:
    """Retrieve all document metadata records ordered by newest first."""
    supabase = get_supabase()
    response = supabase.table("documents").select("*").order("uploaded_at", desc=True).execute()
    return response.data or []


# Get one document

def get_document(document_id: str) -> Optional[dict]:
    """Retrieve a single document's metadata by ID."""
    supabase = get_supabase()
    try:
        response = supabase.table("documents").select("*").eq("id", document_id).single().execute()
        return response.data
    except Exception as e:
        logger.warning("Document %s not found or API error occurred: %s", document_id, e)
        return None


# Download document

def download_document(storage_path: str) -> bytes:
    """Download the raw bytes of a document from Supabase Storage."""
    supabase = get_supabase()
    logger.info("Downloading document: %s", storage_path)
    return supabase.storage.from_(config.SUPABASE_BUCKET_NAME).download(storage_path)


# Delete document


def delete_document(document_id: str) -> dict:
    """
    Delete both the Supabase Storage file and the PostgreSQL metadata.
    Returns the metadata of the deleted document.
    """
    supabase = get_supabase()
    document = get_document(document_id)

    if not document:
        raise ValueError(f"Document with ID '{document_id}' does not exist.")

    storage_path = document["storage_path"]
    filename = document["filename"]

    # 1. Delete storage object
    logger.info("Deleting storage file: %s", storage_path)
    remove_response = supabase.storage.from_(config.SUPABASE_BUCKET_NAME).remove([storage_path])
    
    # Validate the storage deletion actually worked
    if hasattr(remove_response, "error") and remove_response.error:
        logger.error("Failed to delete storage file %s: %s", storage_path, remove_response.error)
        raise Exception(f"Supabase storage deletion error: {remove_response.error}")

    # 2. Delete database metadata
    supabase.table("documents").delete().eq("id", document_id).execute()
    logger.info("Deleted document: %s", filename)

    return document