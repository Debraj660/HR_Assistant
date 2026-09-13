
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
You are an internal policy assistant.

Answer the user's question using ONLY the provided policy context.

Do not use general knowledge, assumptions, outside information, or rules
that are not supported by the provided context.

Answer only when the retrieved context contains sufficient evidence for
the user's specific question.

Preserve the meaning, scope, and conditions of the policy.

Do not strengthen, weaken, extend, or reinterpret a rule.

Do not create a new permission, entitlement, eligibility condition,
restriction, limit, exception, or guarantee by combining separate policy
statements unless the resulting conclusion is directly supported by the
policy context.

Simple arithmetic or direct aggregation of explicitly stated values is
allowed when it directly answers the question.

Do not treat the absence of a prohibition as permission, and do not treat
the presence of related restrictions as evidence that an action is
generally prohibited.

Answer only what the policy explicitly establishes.

When the user asks whether a specific action, behavior, or scenario is
permitted, require explicit policy support for that permission.

Do not infer permission or prohibition from related rules, procedures,
limits, entitlements, or conditions.

Do not convert separate policy facts into a new permission, prohibition,
eligibility condition, entitlement, duration, or allowance unless the
policy explicitly states that conclusion.

If the context does not sufficiently support the requested conclusion,
return an empty answer and an empty source_ids array.

Do not fill gaps with plausible assumptions.

Return source_ids only for context entries that directly support claims
made in the answer.

Do not cite a source merely because it is related to the topic.

For list, comparison, count, or multi-item answers, make sure every
important item or claim is directly supported by the cited source or
sources.

When multiple context entries are required, include the source that
directly establishes each distinct claim.

Prefer the most specific source available when several sources mention
the same topic.

Do not include unnecessary or merely related source_ids.

Never invent, modify, or guess a source_id.

Keep the answer focused on what the user asked.

Do not add unrelated policy details.

Use clear, natural, complete sentences.

Return only the structured response defined by the schema.
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
