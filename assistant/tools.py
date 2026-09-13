from langchain_core.tools import tool

from assistant.logger import get_logger


logger = get_logger(__name__)


def create_search_tool(
    retriever,
):

    @tool
    def search_hr_policy_with_context(
        question: str,
    ) -> str:
        """
        Search uploaded HR policy documents using
        the vector database and return relevant
        policy context with citation information.
        """

        logger.info(
            "Searching HR policy for: %s",
            question,
        )

        matching_chunks = retriever.invoke(
            question
        )

        logger.info(
            "Found %d matching chunks.",
            len(matching_chunks),
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


            # Document information


            filename = chunk.metadata.get(
                "filename",
                "Unknown document",
            )

            document_id = chunk.metadata.get(
                "document_id",
                "Unknown",
            )


            # Section information


            section = chunk.metadata.get(
                "section",
                "General",
            )


            # Page information

            page_number = chunk.metadata.get(
                "page_number"
            )

            # Content

            content = chunk.page_content.strip()

            # Build citation

            citation = (
                f"{filename} — {section}"
            )

            if page_number is not None:

                citation += (
                    f" (Page {page_number})"
                )

            # Build search result

            results.append(
                f"""
SOURCE {index}
Citation: {citation}
Document: {filename}
Section: {section}
Document ID: {document_id}

Content:
{content}
"""
            )

        return "\n".join(results)

    return search_hr_policy_with_context