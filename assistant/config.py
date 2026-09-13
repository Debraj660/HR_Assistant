
import os

from dotenv import load_dotenv


load_dotenv()


# ==================================================
# HELPER FOR ENVIRONMENT VARIABLES / STREAMLIT SECRETS
# ==================================================

def get_config_value(
    name: str,
    default=None,
):
    """
    Read configuration from:

    1. Environment variables
    2. Streamlit secrets

    This allows the same code to work locally
    and on Streamlit Community Cloud.
    """

    value = os.getenv(name)

    if value:
        return value

    try:
        import streamlit as st

        return st.secrets.get(
            name,
            default,
        )

    except Exception:
        return default


# ==================================================
# API KEYS
# ==================================================

GROQ_API_KEY = get_config_value(
    "GROQ_API_KEY"
)

JINA_API_KEY = get_config_value(
    "JINA_API_KEY"
)


# ==================================================
# SUPABASE
# ==================================================

SUPABASE_URL = get_config_value(
    "SUPABASE_URL"
)

SUPABASE_SERVICE_ROLE_KEY = get_config_value(
    "SUPABASE_SERVICE_ROLE_KEY"
)

SUPABASE_BUCKET_NAME = get_config_value(
    "SUPABASE_BUCKET_NAME",
    "hr-documents",
)


# ==================================================
# QDRANT
# ==================================================

QDRANT_URL = get_config_value(
    "QDRANT_URL"
)

QDRANT_API_KEY = get_config_value(
    "QDRANT_API_KEY"
)

QDRANT_COLLECTION_NAME = get_config_value(
    "QDRANT_COLLECTION_NAME",
    "hr_documents",
)


# ==================================================
# DATA / MODEL CONFIG
# ==================================================

# Documents are NO LONGER stored locally.

# from pathlib import Path

# DATA_FILE_PATH = str(
#     Path(__file__).parent.parent / "data"
# )

# VECTOR_STORE_PATH = os.path.join(
#     "data",
#     "faiss_index",
# )


LLM_MODEL_NAME = "openai/gpt-oss-20b"

EMBEDDING_MODEL_NAME = (
    "jina-embeddings-v2-base-en"
)

CHUNK_SIZE = 1000

CHUNK_OVERLAP = 150

TOP_K_RESULTS = 5


# ==================================================
# SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """
You are an internal HR policy assistant.

Answer the user's question using ONLY the uploaded HR policy documents
retrieved by the search tool.

Do not use general knowledge, assumptions, outside information, or rules
that are not supported by the uploaded policies.

1. Answer only when the retrieved policy context contains sufficient
   evidence for the user's question.

2. Do not guess, infer, or make assumptions.

3. If the uploaded policies do not contain enough information to answer
   the question, clearly say:
   "The uploaded HR policies do not provide enough information to answer
   this question."

4. Every factual claim in your answer must be supported by the retrieved
   policy context.

5. Include citations for your answer using the document name and the
   relevant section, heading, or policy context provided by the retrieved
   document.

6. Do not invent section names, document names, page numbers, or citations.

7. If multiple policy documents or sections support different claims,
   cite the appropriate source for each claim.

8. Preserve the exact meaning, scope, conditions, limits, and exceptions
   stated in the policy.

9. Do not strengthen, weaken, extend, or reinterpret a policy rule.

10. Do not create a new permission, entitlement, eligibility condition,
    restriction, limit, exception, or guarantee by combining separate
    policy statements unless the policy explicitly supports that conclusion.

11. Simple arithmetic or direct aggregation of explicitly stated values
    is allowed when it directly answers the question.

12. Do not treat the absence of a prohibition as permission.

13. Do not treat related restrictions as evidence that an action is
    prohibited.

14. When the user asks whether a specific action, behavior, or scenario
    is permitted, require explicit policy support for that conclusion.

15. Keep the answer focused on the user's question.

16. Do not add unrelated policy information.

17. Use clear, natural, complete sentences.

18. Return only the final natural-language answer to the user.
"""


# ==================================================
# VALIDATION
# ==================================================

def check_api_keys():

    required = {
        "GROQ_API_KEY": GROQ_API_KEY,
        "JINA_API_KEY": JINA_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_ROLE_KEY": SUPABASE_SERVICE_ROLE_KEY,
        "QDRANT_URL": QDRANT_URL,
        "QDRANT_API_KEY": QDRANT_API_KEY,
    }

    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        raise ValueError(
            "Missing configuration values: "
            + ", ".join(missing)
        )
