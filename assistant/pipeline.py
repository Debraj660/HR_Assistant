from typing import Any

from assistant import config
from assistant.agent import create_hr_agent
from assistant.doc_loader import load_document_from_bytes
from assistant.llm import get_llm
from assistant.logger import get_logger
from assistant.splitters import split_into_chunks
from assistant.supabase_storage import (
    get_document,
    list_documents,
    upload_document,
    delete_document,
)
from assistant.tools import create_search_tool
from assistant.vector_store import (
    add_documents_to_vector_store,
    delete_document_from_vector_store,
    get_retriever,
    load_vector_store,
    vector_store_exists,
)

logger = get_logger(__name__)


# Upload + index

def add_uploaded_document(filename: str, file_bytes: bytes) -> dict:
    """
    Complete upload pipeline:
    Streamlit -> Supabase Storage -> Document loader -> Chunking -> Qdrant
    """
    # 1. Upload to Supabase first
    document = upload_document(
        filename=filename,
        file_bytes=file_bytes,
    )
    document_id = document["id"]

    try:
        # 2. Load document
        documents = load_document_from_bytes(
            file_bytes=file_bytes,
            filename=filename,
            document_id=document_id,
        )

        if not documents:
            raise ValueError("The document contains no readable text.")

        # 3. Split
        chunks = split_into_chunks(documents)

        if not chunks:
            raise ValueError("The document produced no chunks.")

        logger.info(
            "%s produced %d chunks.",
            filename,
            len(chunks),
        )

        # 4. Add to Qdrant
        add_documents_to_vector_store(chunks)

        logger.info(
            "Successfully indexed %s.",
            filename,
        )

        return document

    except Exception as indexing_error:
        # Roll back Supabase upload if indexing fails.
        logger.exception(
            "Indexing failed for %s. Rolling back Supabase document.",
            filename,
        )

        try:
            delete_document(document_id)
        except Exception as rollback_error:
            logger.exception(
                "Failed to rollback Supabase document: %s",
                rollback_error,
            )

        raise indexing_error


# Delete document

def remove_document(document_id: str) -> dict:
    """
    Delete from BOTH:
    1. Qdrant
    2. Supabase Storage
    3. Supabase PostgreSQL
    """
    document = get_document(document_id)

    if not document:
        raise ValueError(
            f"Document with ID '{document_id}' not found."
        )

    # Delete vectors FIRST
    delete_document_from_vector_store(document_id)

    # Delete Supabase file + metadata
    delete_document(document_id)

    logger.info(
        "Completely removed document: %s",
        document["filename"],
    )

    return document


# List documents

def get_all_documents() -> list[dict]:
    """Retrieve all document metadata records."""
    return list_documents()


# Build assistant

def build_hr_assistant() -> Any:
    """
    Initialize connections, load tools, and build the agent.
    """
    logger.info("Building HR assistant...")

    config.check_api_keys()

    # There must be at least one document
    if not vector_store_exists():
        raise ValueError(
            "No HR documents have been uploaded yet."
        )

    # Connect Qdrant and set up Retriever
    vector_store = load_vector_store()
    retriever = get_retriever(vector_store)

    # Initialize Tool(s)
    search_tool = create_search_tool(retriever)

    # Initialize LLM & Agent
    llm = get_llm()
    agent = create_hr_agent(
        llm,
        [search_tool],
    )

    logger.info("HR assistant ready.")

    return agent


# Ask

FALLBACK_RESPONSE = (
    "I couldn't find enough information in the available HR policies "
    "to answer that. Please contact HR."
)


def ask(agent: Any, question: str) -> str:
    """
    Pass a user question to the agent and extract the string response.

    If the agent returns an empty response, return the fallback response.
    """
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        }
    )

    answer = response["messages"][-1].content

    # Fallback when the agent returns an empty answer.
    if not answer or not answer.strip():
        return FALLBACK_RESPONSE

    return answer