from langchain_core.tools import tool
from assistant.logger import get_logger

logger = get_logger(__name__)


@tool
def search_hr_policy(question: str) -> str:
    """Search HR policy documents to answer employee questions.
    
    Args:
        question: The employee's question about HR policies
        
    Returns:
        Relevant HR policy information
    """
    logger.info("search_hr_policy called with query: %s", question)
    return f"HR Policy information for: {question}"


def create_search_tool(retriever):
    """Create a search tool using the retriever."""
    
    @tool
    def search_hr_policy_with_context(question: str) -> str:
        """Search HR policy documents using vector store.
        
        Args:
            question: The employee's question about HR policies
            
        Returns:
            Relevant HR policy information from documents
        """
        logger.info("search_hr_policy called with query: %s", question)
        matching_chunks = retriever.invoke(question)
        logger.info("Found %d matching chunk(s)", len(matching_chunks))
        return "\n".join(chunk.page_content for chunk in matching_chunks)
    
    return search_hr_policy_with_context