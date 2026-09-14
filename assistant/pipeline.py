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


# ============================================================
# Upload + Index
# ============================================================

def add_uploaded_document(
    filename: str,
    file_bytes: bytes,
) -> dict:
    """
    Complete upload pipeline:

    Streamlit
        -> Supabase Storage
        -> Document Loader
        -> Chunking
        -> Qdrant
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
            raise ValueError(
                "The document contains no readable text."
            )

        # 3. Split document into chunks
        chunks = split_into_chunks(documents)

        if not chunks:
            raise ValueError(
                "The document produced no chunks."
            )

        logger.info(
            "%s produced %d chunks.",
            filename,
            len(chunks),
        )

        # 4. Add chunks to Qdrant
        add_documents_to_vector_store(chunks)

        logger.info(
            "Successfully indexed %s.",
            filename,
        )

        return document

    except Exception as indexing_error:
        # Roll back Supabase upload if indexing fails
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


# ============================================================
# Delete Document
# ============================================================

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


# ============================================================
# List Documents
# ============================================================

def get_all_documents() -> list[dict]:
    """
    Retrieve all document metadata records.
    """
    return list_documents()


# ============================================================
# Build HR Assistant
# ============================================================

def build_hr_assistant() -> Any:
    """
    Initialize connections, load tools, and build the HR agent.
    """

    logger.info("Building HR assistant...")

    # Check required API keys/configuration
    config.check_api_keys()

    # There must be at least one document
    if not vector_store_exists():
        raise ValueError(
            "No HR documents have been uploaded yet."
        )

    # Load Qdrant vector store
    vector_store = load_vector_store()

    # Create retriever
    retriever = get_retriever(vector_store)

    # Create policy search tool
    search_tool = create_search_tool(retriever)

    # Initialize LLM
    llm = get_llm()

    # Create HR agent
    agent = create_hr_agent(
        llm,
        [search_tool],
    )

    logger.info("HR assistant ready.")

    return agent


# ============================================================
# Fallback Response
# ============================================================

FALLBACK_RESPONSE = (
    "I couldn't find enough information in the available HR policies "
    "to answer that. Please contact HR."
)


# ============================================================
# Question Validation
# ============================================================

def is_question_clear(
    llm: Any,
    question: str,
) -> bool:
    """
    Determine whether the user's question is clear enough
    to be sent to the HR policy agent.

    Returns:
        True  -> Question is clear.
        False -> Question is unclear/ambiguous/malformed.
    """

    validation_prompt = f"""
You are a strict question validation system.

Your ONLY task is to determine whether the user's question is
clear and semantically understandable.

Return ONLY one word:

YES

or

NO

Rules:

1. Do not guess the user's intention.

2. Do not rewrite, repair, or correct the user's question.

3. Do not infer the intended meaning from individual keywords.

4. The question must clearly express what the user wants to know.

5. If the relationship between the important words is unclear,
   return NO.

6. If the question is grammatically malformed in a way that makes
   its intended meaning unclear, return NO.

7. If the question is ambiguous and multiple interpretations are
   reasonably possible, return NO.

8. If the question is incomplete or nonsensical, return NO.

9. Do not use any policy knowledge to determine what the user
   probably intended.

10. A keyword such as "gym", "salary", "expense", "leave",
    "health", or "LTA" does NOT make an unclear question clear.

Examples:

Question:
Is this covered?
Answer:
NO

Question:
What about gym?
Answer:
NO

Now validate this user question:

{question}
"""

    try:
        response = llm.invoke(validation_prompt)

        result = response.content.strip().upper()

        # Accept ONLY an exact YES.
        # Anything else is treated as unclear.
        if result == "YES":
            return True

        return False

    except Exception:
        logger.exception(
            "Question validation failed."
        )

        # Fail safely.
        # If validation fails, do not allow the question
        # to reach the policy agent.
        return False

# Ask HR Assistant

def ask(
    agent: Any,
    question: str,
) -> str:
    """
    Process a user question.

    Flow:

    User question
        -> Question validation
        -> If unclear: fallback
        -> If clear: HR agent
        -> Policy retrieval
        -> Final answer
    """

    # --------------------------------------------------------
    # Basic input validation
    # --------------------------------------------------------

    if not question or not question.strip():
        return FALLBACK_RESPONSE

    question = question.strip()

    logger.info(
        "Processing HR question: %s",
        question,
    )

    # --------------------------------------------------------
    # STEP 1: Validate question BEFORE agent/retrieval
    # --------------------------------------------------------

    try:
        validation_llm = get_llm()

        question_is_clear = is_question_clear(
            validation_llm,
            question,
        )

    except Exception:
        logger.exception(
            "Unable to initialize question validation LLM."
        )

        return FALLBACK_RESPONSE

    # --------------------------------------------------------
    # STEP 2: Unclear question -> immediate fallback
    # --------------------------------------------------------

    if not question_is_clear:
        logger.info(
            "Question rejected because it is unclear: %s",
            question,
        )

        return FALLBACK_RESPONSE

    # --------------------------------------------------------
    # STEP 3: Clear question -> send to HR agent
    # --------------------------------------------------------

    try:
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

    except Exception:
        logger.exception(
            "HR agent failed while processing question."
        )

        return FALLBACK_RESPONSE

    # --------------------------------------------------------
    # STEP 4: Extract agent response
    # --------------------------------------------------------

    try:
        answer = response["messages"][-1].content
    except (KeyError, IndexError, TypeError, AttributeError):
        logger.exception(
            "Could not extract answer from HR agent response."
        )

        return FALLBACK_RESPONSE

    # --------------------------------------------------------
    # STEP 5: Empty answer -> fallback
    # --------------------------------------------------------

    if not answer or not answer.strip():
        return FALLBACK_RESPONSE

    return answer.strip()
