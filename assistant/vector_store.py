from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
)


from langchain_qdrant import QdrantVectorStore


from assistant import config
from assistant.embeddings import get_embeddings_model
from assistant.logger import get_logger


logger = get_logger(__name__)


# Qdrant client


def get_qdrant_client():

    if not config.QDRANT_URL:

        raise ValueError(
            "Missing QDRANT_URL."
        )

    if not config.QDRANT_API_KEY:

        raise ValueError(
            "Missing QDRANT_API_KEY."
        )

    return QdrantClient(
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_KEY,
    )


# ==================================================
# Check collection
# ==================================================

def vector_store_exists():

    client = get_qdrant_client()

    try:

        return client.collection_exists(
            config.QDRANT_COLLECTION_NAME
        )

    finally:

        client.close()


# ==================================================
# Create vector store
# ==================================================

def build_vector_store(
    chunks
):

    if not chunks:

        raise ValueError(
            "No document chunks provided."
        )

    logger.info(
        "Creating Qdrant collection '%s' "
        "with %d chunks.",
        config.QDRANT_COLLECTION_NAME,
        len(chunks),
    )

    embeddings = (
        get_embeddings_model()
    )

    vector_store = (
        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            url=config.QDRANT_URL,
            api_key=config.QDRANT_API_KEY,
            collection_name=(
                config.QDRANT_COLLECTION_NAME
            ),
        )
    )

    return vector_store


# Load existing vector store

def load_vector_store():

    if not vector_store_exists():

        raise ValueError(
            "Qdrant collection does not exist."
        )

    embeddings = (
        get_embeddings_model()
    )

    vector_store = (
        QdrantVectorStore
        .from_existing_collection(
            embedding=embeddings,
            collection_name=(
                config.QDRANT_COLLECTION_NAME
            ),
            url=config.QDRANT_URL,
            api_key=config.QDRANT_API_KEY,
        )
    )

    return vector_store


# Add documents

def add_documents_to_vector_store(
    chunks
):

    if not chunks:

        raise ValueError(
            "No chunks provided."
        )

    if not vector_store_exists():

        return build_vector_store(
            chunks
        )

    vector_store = (
        load_vector_store()
    )

    vector_store.add_documents(
        chunks
    )

    logger.info(
        "Added %d chunks to Qdrant.",
        len(chunks),
    )

    return vector_store


# Delete document from Qdrant

def delete_document_from_vector_store(
    document_id: str
):
    """
    Delete ALL Qdrant points belonging
    to the specified document.
    """

    if not vector_store_exists():

        logger.info(
            "Qdrant collection does not exist."
        )

        return

    client = get_qdrant_client()

    try:

        document_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.document_id",
                    match=MatchValue(
                        value=document_id
                    ),
                )
            ]
        )

        logger.info(
            "Deleting Qdrant vectors for "
            "document_id=%s",
            document_id,
        )

        client.delete(
            collection_name=(
                config.QDRANT_COLLECTION_NAME
            ),
            points_selector=FilterSelector(
                filter=document_filter
            ),
            wait=True,
        )

        logger.info(
            "Qdrant vectors deleted for "
            "document_id=%s",
            document_id,
        )

    finally:

        client.close()


# Retriever

def get_retriever(
    vector_store,
    k: int = config.TOP_K_RESULTS,
):

    return vector_store.as_retriever(
        search_kwargs={
            "k": k
        }
    )

# Delete entire collection

def delete_vector_store():

    if not vector_store_exists():

        return

    client = get_qdrant_client()

    try:

        client.delete_collection(
            config.QDRANT_COLLECTION_NAME
        )

    finally:

        client.close()