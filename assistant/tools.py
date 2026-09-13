from langchain_core.tools import tool


from assistant.logger import get_logger


logger = get_logger(__name__)


def create_search_tool(
    retriever
):

    @tool
    def search_hr_policy_with_context(
        question: str
    ) -> str:
        """
        Search uploaded HR policy documents
        using the vector database.
        """

        logger.info(
            "Searching HR policy for: %s",
            question
        )

        matching_chunks = (
            retriever.invoke(
                question
            )
        )

        logger.info(
            "Found %d matching chunks.",
            len(matching_chunks)
        )

        if not matching_chunks:

            return (
                "No relevant HR policy "
                "information was found."
            )

        results = []

        for index, chunk in enumerate(
            matching_chunks,
            start=1,
        ):

            filename = chunk.metadata.get(
                "filename",
                "Unknown document",
            )

            document_id = chunk.metadata.get(
                "document_id",
                "Unknown",
            )

            content = (
                chunk.page_content
            )

            results.append(
                f"""
SOURCE {index}
Document: {filename}
Document ID: {document_id}

Content:
{content}
"""
            )

        return "\n".join(
            results
        )

    return search_hr_policy_with_context