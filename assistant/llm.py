from langchain_groq import ChatGroq
from assistant.logger import get_logger
from assistant import config

logger = get_logger(__name__)

def get_llm():

    return ChatGroq(model=config.LLM_MODEL_NAME, temperature=0.1)