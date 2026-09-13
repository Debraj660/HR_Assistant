from assistant import config


from assistant.agent import create_hr_agent


from assistant.doc_loader import (
    load_document_from_bytes,
)


from assistant.embeddings import (
    get_embeddings_model,
)


from assistant.llm import get_llm


from assistant.logger import get_logger


from assistant.splitters import (
    split_into_chunks,
)


from assistant.supabase_storage import (
    download_document,
    get_document,
    list_documents,
    upload_document,
    delete_document,
)


from assistant.tools import (
    create_search_tool,
)


from assistant.vector_store import (
    add_documents_to_vector_store,
    delete_document_from_vector_store,
    get_retriever,
    load_vector_store,
    vector_store_exists,
)


logger = get_logger(__name__)


# ==================================================
# Upload + index
# ==================================================

def add_uploaded_document(
    filename: str,
    file_bytes: bytes,
):
    """
    Complete upload pipeline:

    Streamlit
        ↓
    Supabase Storage
        ↓
    Download bytes
        ↓
    Document loader
        ↓
    Chunking
        ↓
    Qdrant
    """

    # ----------------------------------------------
    # Upload to Supabase first
    # ----------------------------------------------

    document = upload_document(
        filename=filename,
        file_bytes=file_bytes,
    )

    document_id = document[
        "id"
    ]

    try:

        # ------------------------------------------
        # Load document
        # ------------------------------------------

        documents = (
            load_document_from_bytes(
                file_bytes=file_bytes,
                filename=filename,
                document_id=document_id,
            )
        )

        if not documents:

            raise ValueError(
                "The document contains no readable text."
            )

        # ------------------------------------------
        # Split
        # ------------------------------------------

        chunks = split_into_chunks(
            documents
        )

        if not chunks:

            raise ValueError(
                "The document produced no chunks."
            )

        logger.info(
            "%s produced %d chunks.",
            filename,
            len(chunks),
        )

        # ------------------------------------------
        # Add to Qdrant
        # ------------------------------------------

        add_documents_to_vector_store(
            chunks
        )

        logger.info(
            "Successfully indexed %s.",
            filename,
        )

        return document

    except Exception:

        # ------------------------------------------
        # Roll back Supabase upload if indexing
        # fails.
        # ------------------------------------------

        logger.exception(
            "Indexing failed for %s. "
            "Rolling back Supabase document.",
            filename,
        )

        try:

            delete_document(
                document_id
            )

        except Exception:

            logger.exception(
                "Failed to rollback Supabase document."
            )

        raise


# ==================================================
# Delete document
# ==================================================

def remove_document(
    document_id: str
):
    """
    Delete from BOTH:

    1. Qdrant
    2. Supabase Storage
    3. Supabase PostgreSQL
    """

    document = get_document(
        document_id
    )

    if not document:

        raise ValueError(
            "Document not found."
        )

    # ----------------------------------------------
    # Delete vectors FIRST
    # ----------------------------------------------

    delete_document_from_vector_store(
        document_id
    )

    # ----------------------------------------------
    # Delete Supabase file + metadata
    # ----------------------------------------------

    delete_document(
        document_id
    )

    logger.info(
        "Completely removed document: %s",
        document["filename"],
    )

    return document


# ==================================================
# List documents
# ==================================================

def get_all_documents():

    return list_documents()


# ==================================================
# Build assistant
# ==================================================

def build_hr_assistant():

    logger.info(
        "Building HR assistant..."
    )

    config.check_api_keys()

    # ----------------------------------------------
    # There must be at least one document
    # ----------------------------------------------

    if not vector_store_exists():

        raise ValueError(
            "No HR documents have been uploaded yet."
        )

    # ----------------------------------------------
    # Connect Qdrant
    # ----------------------------------------------

    vector_store = (
        load_vector_store()
    )

    # ----------------------------------------------
    # Retriever
    # ----------------------------------------------

    retriever = get_retriever(
        vector_store
    )

    # ----------------------------------------------
    # Search tool
    # ----------------------------------------------

    search_tool = create_search_tool(
        retriever
    )

    # ----------------------------------------------
    # LLM
    # ----------------------------------------------

    llm = get_llm()

    # ----------------------------------------------
    # Agent
    # ----------------------------------------------

    agent = create_hr_agent(
        llm,
        [search_tool],
    )

    logger.info(
        "HR assistant ready."
    )

    return agent


# ==================================================
# Ask
# ==================================================

def ask(
    agent,
    question: str,
):

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

    return (
        response["messages"][-1]
        .content
    )