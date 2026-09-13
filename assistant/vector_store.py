import os
from pathlib import Path
from langchain_community.vectorstores import FAISS

from assistant import config
from assistant.embeddings import get_embeddings_model
from assistant.logger import get_logger

logger = get_logger(__name__)

# Define FAISS index path
FAISS_INDEX_PATH = Path(config.DATA_FILE_PATH).parent / "faiss_index"


def build_vector_store(chunks):
    """Embed every chunk and store in local FAISS index."""
    logger.info("Embedding %d chunk(s) and storing in FAISS...", len(chunks))
    
    embeddings_model = get_embeddings_model()
    vector_store = FAISS.from_documents(chunks, embeddings_model)
    
    # Save FAISS index locally
    vector_store.save_local(str(FAISS_INDEX_PATH))
    logger.info("FAISS index saved to '%s'", FAISS_INDEX_PATH)
    
    return vector_store


def load_vector_store():
    """Load existing FAISS index from local storage."""
    logger.info("Loading FAISS index from '%s'", FAISS_INDEX_PATH)
    
    if not vector_store_exists():
        logger.error("FAISS index not found at '%s'", FAISS_INDEX_PATH)
        raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")
    
    embeddings_model = get_embeddings_model()
    return FAISS.load_local(
        str(FAISS_INDEX_PATH),
        embeddings_model,
        allow_dangerous_deserialization=True
    )


def vector_store_exists() -> bool:
    """Check if FAISS index exists locally."""
    exists = FAISS_INDEX_PATH.exists()
    logger.debug("FAISS index exists: %s", exists)
    return exists


def get_retriever(vector_store, k: int = config.TOP_K_RESULTS):
    """Turn FAISS vector store into a retriever."""
    logger.info("Creating retriever with top_k=%d", k)
    return vector_store.as_retriever(search_kwargs={"k": k})


def delete_vector_store():
    """Delete the FAISS index (useful for rebuilding)."""
    if vector_store_exists():
        import shutil
        shutil.rmtree(FAISS_INDEX_PATH)
        logger.info("FAISS index deleted from '%s'", FAISS_INDEX_PATH)
    else:
        logger.warning("No FAISS index found to delete")