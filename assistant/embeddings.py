from langchain_community.embeddings import (
    JinaEmbeddings,
)


from assistant import config
from assistant.logger import get_logger


logger = get_logger(__name__)


def get_embeddings_model():

    logger.info(
        "Initializing embedding model '%s'",
        config.EMBEDDING_MODEL_NAME,
    )

    return JinaEmbeddings(
        model_name=(
            config.EMBEDDING_MODEL_NAME
        )
    )