import uuid
from datetime import datetime, timezone
from pathlib import Path


from supabase import create_client
from assistant import config
from assistant.logger import get_logger


logger = get_logger(__name__)

# Supabase client

def get_supabase():

    if not config.SUPABASE_URL:

        raise ValueError(
            "Missing SUPABASE_URL."
        )

    if not config.SUPABASE_SERVICE_ROLE_KEY:

        raise ValueError(
            "Missing SUPABASE_SERVICE_ROLE_KEY."
        )

    return create_client(
        config.SUPABASE_URL,
        config.SUPABASE_SERVICE_ROLE_KEY,
    )

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
}


# ==================================================
# Upload
# ==================================================

def upload_document(
    filename: str,
    file_bytes: bytes,
):
    """
    Upload a document to Supabase Storage and
    create its metadata record in PostgreSQL.

    Returns:
        document_id
        storage_path
    """

    extension = Path(
        filename
    ).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    supabase = get_supabase()

    document_id = str(
        uuid.uuid4()
    )

    storage_path = (
        f"documents/"
        f"{document_id}/"
        f"{filename}"
    )

    # ----------------------------------------------
    # Upload actual file
    # ----------------------------------------------

    content_type = {
        ".pdf": "application/pdf",
        ".docx": (
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml.document"
        ),
        ".txt": "text/plain",
        ".md": "text/markdown",
    }.get(
        extension,
        "application/octet-stream",
    )

    logger.info(
        "Uploading %s to Supabase: %s",
        filename,
        storage_path,
    )

    supabase.storage \
        .from_(
            config.SUPABASE_BUCKET_NAME
        ) \
        .upload(
            storage_path,
            file_bytes,
            {
                "content-type": content_type,
                "upsert": False,
            },
        )

    # ----------------------------------------------
    # Store metadata
    # ----------------------------------------------

    metadata = {
        "id": document_id,
        "filename": filename,
        "storage_path": storage_path,
        "file_type": extension,
        "file_size": len(file_bytes),
        "uploaded_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    try:

        supabase.table(
            "documents"
        ).insert(
            metadata
        ).execute()

    except Exception:

        # If database insertion fails,
        # remove uploaded file so we don't
        # leave orphaned storage.

        try:

            supabase.storage \
                .from_(
                    config.SUPABASE_BUCKET_NAME
                ) \
                .remove(
                    [storage_path]
                )

        except Exception:

            logger.exception(
                "Failed to clean up "
                "orphaned storage file."
            )

        raise

    logger.info(
        "Document uploaded successfully: %s",
        document_id,
    )

    return metadata


# ==================================================
# List documents
# ==================================================

def list_documents():

    supabase = get_supabase()

    response = (
        supabase
        .table("documents")
        .select("*")
        .order(
            "uploaded_at",
            desc=True,
        )
        .execute()
    )

    return response.data or []


# ==================================================
# Get one document
# ==================================================

def get_document(
    document_id: str
):

    supabase = get_supabase()

    response = (
        supabase
        .table("documents")
        .select("*")
        .eq(
            "id",
            document_id,
        )
        .single()
        .execute()
    )

    return response.data


# ==================================================
# Download document
# ==================================================

def download_document(
    storage_path: str
):

    supabase = get_supabase()

    logger.info(
        "Downloading document: %s",
        storage_path,
    )

    response = (
        supabase.storage
        .from_(
            config.SUPABASE_BUCKET_NAME
        )
        .download(
            storage_path
        )
    )

    return response


# ==================================================
# Delete document
# ==================================================

def delete_document(
    document_id: str
):
    """
    Delete both:

    1. Supabase Storage file
    2. PostgreSQL metadata

    Qdrant deletion is handled separately.
    """

    supabase = get_supabase()

    document = get_document(
        document_id
    )

    if not document:

        raise ValueError(
            "Document does not exist."
        )

    storage_path = document[
        "storage_path"
    ]

    filename = document[
        "filename"
    ]

    # ----------------------------------------------
    # Delete storage object
    # ----------------------------------------------

    logger.info(
        "Deleting storage file: %s",
        storage_path,
    )

    supabase.storage \
        .from_(
            config.SUPABASE_BUCKET_NAME
        ) \
        .remove(
            [storage_path]
        )

    # ----------------------------------------------
    # Delete database metadata
    # ----------------------------------------------

    supabase.table(
        "documents"
    ).delete().eq(
        "id",
        document_id,
    ).execute()

    logger.info(
        "Deleted document: %s",
        filename,
    )

    return document