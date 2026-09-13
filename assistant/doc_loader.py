from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from assistant import config
from assistant.logger import get_logger

logger = get_logger(__name__)


def load_documents(file_path: str = config.DATA_FILE_PATH):
    logger.info("Loading documents from '%s'", file_path)
    
    # Use DirectoryLoader to load all .md files
    loader = DirectoryLoader(
        path=file_path,
        glob="**/*.md",  # Recursive search for all .md files
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    
    documents = loader.load()
    logger.info("Loaded %d document(s) from directory", len(documents))
    
    # Log file sources
    for doc in documents:
        logger.debug("Loaded: %s", doc.metadata.get("source"))
    
    return documents


# Alternative: If you want more control over file loading
def load_documents_custom(file_path: str = config.DATA_FILE_PATH):
    """Load all .md files with custom error handling."""
    logger.info("Loading markdown documents from '%s'", file_path)
    
    documents = []
    data_dir = Path(file_path)
    
    if not data_dir.exists():
        logger.error("Data directory does not exist: %s", file_path)
        return documents
    
    # Find all .md files recursively
    md_files = list(data_dir.glob("**/*.md"))
    logger.info("Found %d markdown file(s)", len(md_files))
    
    for md_file in md_files:
        try:
            loader = TextLoader(str(md_file), encoding="utf-8")
            docs = loader.load()
            documents.extend(docs)
            logger.debug("Loaded: %s (%d docs)", md_file.name, len(docs))
        except Exception as e:
            logger.error("Error loading %s: %s", md_file.name, str(e))
    
    logger.info("Total documents loaded: %d", len(documents))
    return documents