import streamlit as st
from assistant.logger import get_logger

from assistant.pipeline import (
    add_uploaded_document,
    ask,
    build_hr_assistant,
    get_all_documents,
    remove_document,
)

logger = get_logger(__name__)

# PAGE CONFIG

st.set_page_config(
    page_title="HR Policy Assistant",
    page_icon="🤖",
    layout="centered",
)



# CONSTANTS


SUPPORTED_FILE_TYPES = [
    "pdf",
    "docx",
    "txt",
    "md",
]


MAX_FILE_SIZE_MB = 20



# HEADER

st.title(
    "HR Policy Assistant"
)

st.caption(
    "Ask questions about uploaded HR documents."
)



# CACHED AGENT

@st.cache_resource(
    show_spinner="Connecting to HR knowledge base..."
)
def get_agent():

    return build_hr_assistant()



# ADMIN SIDEBAR

with st.sidebar:

    st.header("Admin")

    st.divider()

    # UPLOAD

    st.subheader(
        "Upload Document"
    )

    uploaded_file = st.file_uploader(
        "Choose HR document",
        type=SUPPORTED_FILE_TYPES,
        help=(
            "Supported: PDF, DOCX, TXT and MD. "
            "Maximum size: 20 MB."
        ),
    )

    if uploaded_file:

        file_size_mb = (
            uploaded_file.size
            / (1024 * 1024)
        )

        st.write(
            f"**File:** `{uploaded_file.name}`"
        )

        st.write(
            f"**Size:** `{file_size_mb:.2f} MB`"
        )

        if file_size_mb > MAX_FILE_SIZE_MB:

            st.error(
                f"Maximum file size is "
                f"{MAX_FILE_SIZE_MB} MB."
            )

        else:

            if st.button(
                "Upload",
                type="primary",
                use_container_width=True,
            ):

                try:

                    with st.spinner(
                        "Uploading and indexing..."
                    ):

                        document = (
                            add_uploaded_document(
                                filename=(
                                    uploaded_file.name
                                ),
                                file_bytes=(
                                    uploaded_file
                                    .getvalue()
                                ),
                            )
                        )

                    # Clear cached RAG agent
                    get_agent.clear()

                    st.success(
                        f"'{uploaded_file.name}' "
                        "uploaded successfully."
                    )

                    st.rerun()

                except Exception as e:

                    logger.exception(
                        "Upload failed."
                    )

                    st.error(
                        "Failed to upload/index document."
                    )

                    st.exception(e)

    # DOCUMENT LIST

    st.divider()

    st.subheader(
        "📚 Uploaded Documents"
    )

    try:

        documents = (
            get_all_documents()
        )

    except Exception as e:

        logger.exception(
            "Failed to retrieve documents."
        )

        st.error(
            "Could not load document list."
        )

        documents = []

    if not documents:

        st.info(
            "No documents uploaded yet."
        )

    else:

        for document in documents:

            document_id = document[
                "id"
            ]

            filename = document[
                "filename"
            ]

            file_size_mb = (
                document["file_size"]
                / (1024 * 1024)
            )

            with st.container(
                border=True
            ):

                st.write(
                    f"📄 **{filename}**"
                )

                st.caption(
                    f"{file_size_mb:.2f} MB"
                )

                uploaded_at = document.get(
                    "uploaded_at",
                    ""
                )

                if uploaded_at:

                    st.caption(
                        f"Uploaded: {uploaded_at[:19]}"
                    )

                if st.button(
                    "🗑️ Delete",
                    key=(
                        f"delete_{document_id}"
                    ),
                    use_container_width=True,
                ):

                    try:

                        with st.spinner(
                            f"Deleting {filename}..."
                        ):

                            deleted_document = (
                                remove_document(
                                    document_id
                                )
                            )

                        # Clear cached agent
                        get_agent.clear()

                        st.success(
                            f"'{deleted_document['filename']}' "
                            "deleted."
                        )

                        st.rerun()

                    except Exception as e:

                        logger.exception(
                            "Delete failed."
                        )

                        st.error(
                            "Failed to delete document."
                        )

                        st.exception(e)


# INITIALIZE ASSISTANT

try:

    agent = get_agent()

except Exception as e:

    logger.warning(
        "Assistant is not ready: %s",
        str(e),
    )

    st.info(
        "Upload an HR document from the "
        "Admin section to start using the assistant."
    )

    st.stop()


# CHAT HISTORY

if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )



# CHAT INPUT

question = st.chat_input(
    "Ask a question about HR policy..."
)


if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):

        st.markdown(
            question
        )

    with st.chat_message("assistant"):

        with st.spinner(
            "Typing..."
        ):

            try:

                answer = ask(
                    agent,
                    question,
                )

            except Exception as e:

                logger.exception(
                    "Question answering failed."
                )

                answer = (
                    "Sorry, I encountered an error "
                    "while processing your question."
                )

                st.error(
                    str(e)
                )

        st.markdown(
            answer
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )