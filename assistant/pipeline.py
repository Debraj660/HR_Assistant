"""Wires all the components together into one ready-to-use agent.

This is the single entry point that main.py (CLI) and app.py (Streamlit)
both call. Each step is handled by its own small module.
"""


from assistant import config
from assistant.agent import create_hr_agent
from assistant.doc_loader import load_documents
from assistant.llm import get_llm
from assistant.splitters import split_into_chunks
from assistant.tools import create_search_tool

from assistant.vector_store import (
    build_vector_store,
    get_retriever,
    load_vector_store,
    vector_store_exists,
)


from assistant.logger import get_logger
logger = get_logger(__name__)


# data ingestion

def build_vector_store_for_document(file_path: str = config.DATA_FILE_PATH):

    if vector_store_exists():
        print("Found an existing Qdrant Cloud collection, connecting to it (fast, no re-embedding).")
        logger.info("Qdrant Cloud collection already exists, reusing it")
        return load_vector_store()


    print("No Qdrant Cloud collection found, building one from scratch...")
    logger.info("No Qdrant Cloud collection found, building one from scratch")
    documents = load_documents(file_path)
    chunks = split_into_chunks(documents)
    print(f"Loaded '{file_path}' and split it into {len(chunks)} chunks.")


    vector_store = build_vector_store(chunks)
    print("Vector store built and uploaded to Qdrant Cloud.")
    return vector_store
    
# data retreival    
    
def build_hr_assistant(file_path: str = config.DATA_FILE_PATH):
    """Build the full RAG agent, ready to answer questions."""
    logger.info("Building HR assistant...")
    config.check_api_keys()
    vector_store = build_vector_store_for_document(file_path)
    retriever = get_retriever(vector_store)
    search_tool = create_search_tool(retriever)

    llm = get_llm()
    agent = create_hr_agent(llm, [search_tool])

    logger.info("HR assistant is ready to take questions")
    return agent


def ask(agent, question: str) -> str:
    """Ask the agent a question and
    return its final answer as plain text."""
    logger.info("User question: %s", question)
    
    # # input guard - to get safe inputs 
    
    # input_is_safe, _ = check_input(question)
    # if not input_is_safe:
    #     return REFUSAL_MESSAGE
    
    response = agent.invoke({"messages": [{"role": "user", "content": question}]})
    answer = response["messages"][-1].content
    logger.info("Final answer: %s", answer)
    
    # # output guard - to check if agent gives safe answer 
    # output_is_safe, _ = check_output(answer)
    # if not output_is_safe:
    #     return REFUSAL_MESSAGE
    
    
    return answer

