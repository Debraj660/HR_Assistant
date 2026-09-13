import re
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


def _extract_markdown_section(text: str) -> str:
    """
    Extract the most recent Markdown heading from a text chunk.
    """

    headings = re.findall(
        r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*$",
        text,
    )

    if headings:
        return headings[-1].strip()

    return "General"


def load_document_from_bytes(
    file_bytes: bytes,
    filename: str,
    document_id: str,
):
    """
    Convert uploaded document bytes into LangChain Documents
    and attach citation metadata.
    """

    extension = Path(filename).suffix.lower()

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

            temp_file.write(file_bytes)
            temp_path = temp_file.name

        logger.info(
            "Loading document: %s",
            filename,
        )

        # ------------------------------------------
        # Select loader
        # ------------------------------------------

        if extension == ".pdf":

            loader = PyPDFLoader(temp_path)

        elif extension == ".docx":

            loader = Docx2txtLoader(temp_path)

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

            document.metadata["document_id"] = document_id

            document.metadata["filename"] = filename

            document.metadata["document_type"] = extension

            document.metadata["source_type"] = "admin_upload"

            # --------------------------------------
            # PDF page information
            # --------------------------------------

            if extension == ".pdf":

                page = document.metadata.get("page")

                if page is not None:

                    document.metadata["page_number"] = (
                        page + 1
                    )

                    document.metadata["section"] = (
                        f"Page {page + 1}"
                    )

                else:

                    document.metadata["section"] = (
                        "General"
                    )

            # --------------------------------------
            # Markdown section
            # --------------------------------------

            elif extension == ".md":

                document.metadata["section"] = (
                    _extract_markdown_section(
                        document.page_content
                    )
                )

            # --------------------------------------
            # DOCX / TXT
            # --------------------------------------

            else:

                document.metadata["section"] = (
                    "General"
                )

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

                Path(temp_path).unlink(
                    missing_ok=True
                )

            except Exception:

                logger.exception(
                    "Failed to remove temporary file."
                )