import tempfile
from pathlib import Path


from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)


from assistant.logger import get_logger


logger = get_logger(__name__)


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
}


def load_document_from_bytes(
    file_bytes: bytes,
    filename: str,
    document_id: str,
):
    """
    Convert bytes downloaded from Supabase
    into LangChain Documents.
    """

    extension = Path(
        filename
    ).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    temp_path = None

    try:

        # ------------------------------------------
        # Create temporary file
        # ------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            temp_file.write(
                file_bytes
            )

            temp_path = temp_file.name

        logger.info(
            "Loading document: %s",
            filename,
        )

        # ------------------------------------------
        # Select loader
        # ------------------------------------------

        if extension == ".pdf":

            loader = PyPDFLoader(
                temp_path
            )

        elif extension == ".docx":

            loader = Docx2txtLoader(
                temp_path
            )

        else:

            loader = TextLoader(
                temp_path,
                encoding="utf-8",
            )

        documents = loader.load()

        # ------------------------------------------
        # Add metadata
        # ------------------------------------------

        for document in documents:

            document.metadata[
                "document_id"
            ] = document_id

            document.metadata[
                "filename"
            ] = filename

            document.metadata[
                "document_type"
            ] = extension

            document.metadata[
                "source_type"
            ] = "admin_upload"

        logger.info(
            "Loaded %d document object(s): %s",
            len(documents),
            filename,
        )

        return documents

    finally:

        # ------------------------------------------
        # Temporary file cleanup
        # ------------------------------------------

        if temp_path:

            try:

                Path(
                    temp_path
                ).unlink(
                    missing_ok=True
                )

            except Exception:

                logger.exception(
                    "Failed to remove temporary file."
                )