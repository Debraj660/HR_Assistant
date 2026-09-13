
import os

from dotenv import load_dotenv


load_dotenv()


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


# API KEYS

GROQ_API_KEY = get_config_value(
    "GROQ_API_KEY"
)

JINA_API_KEY = get_config_value(
    "JINA_API_KEY"
)


# SUPABASE

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


# QDRANT

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


# SYSTEM PROMPT

SYSTEM_PROMPT = (
"You are an internal policy assistant. "
"Answer the user's question using ONLY the provided policy context. "
"Do not use general knowledge, assumptions, outside information, or rules "
"that are not supported by the provided context. "


"Answer only when the retrieved context contains sufficient evidence for "
"the user's specific question. Preserve the meaning, scope, and conditions "
"of the policy. Do not strengthen, weaken, extend, or reinterpret a rule. "

"Do not create a new permission, entitlement, eligibility condition, "
"restriction, limit, exception, or guarantee by combining separate policy "
"statements unless the resulting conclusion is directly supported by the "
"policy context. Simple arithmetic or direct aggregation of explicitly "
"stated values is allowed when it directly answers the question. "

"Do not treat the absence of a prohibition as permission, and do not treat "
"the presence of related restrictions as evidence that an action is "
"generally prohibited. Answer only what the policy explicitly establishes. "

"When the user asks whether a specific action, behavior, or scenario is "
"permitted, require explicit policy support for that permission. Do not infer "
"permission or prohibition from related rules, procedures, limits, "
"entitlements, or conditions. "

"Do not convert separate policy facts into a new permission, prohibition, "
"eligibility condition, entitlement, duration, or allowance unless the policy "
"explicitly states that conclusion. "

"If the context does not sufficiently support the requested conclusion, "
"the answer must be empty. Do not fill gaps with plausible assumptions. "

"Only include source IDs that directly support claims made in the answer. "
"Do not cite a source merely because it is related to the topic. "

"For list, comparison, count, or multi-item answers, make sure every "
"important item or claim is directly supported by the retrieved policy "
"context. When multiple context entries are required, use the sources that "
"directly establish each distinct claim. Prefer the most specific source "
"available when several sources mention the same topic. "

"Do not include unnecessary or merely related source IDs. "
"Never invent, modify, or guess a source ID. "

"Keep the answer focused on what the user asked. "
"Do not add unrelated policy details. "
"Use clear, natural, complete sentences. "

# Markdown output requirements
"The final answer MUST be valid Markdown. "
"Use Markdown headings, bullet points, numbered lists, tables, and bold text "
"when they improve readability. Do not return HTML. "

# Citation requirements
"Every factual claim taken from the retrieved policy context MUST have a "
"citation to the source that directly supports that claim. "

"Citations MUST contain both the document name and the section name. "
"Use this exact citation format: "
"[Source: Document Name — Section Name] "

"Place the citation immediately after the sentence, bullet point, table row, "
"or paragraph that it supports whenever possible. "

"For example: "
"Employees are eligible for the benefit after completing 12 months of service. "
"[Source: Employee Benefits Policy.pdf — Eligibility] "

"If a single paragraph contains claims supported by multiple sources, include "
"all directly supporting citations. "

"If different claims come from different sections, cite each claim with its "
"corresponding document name and section. "

"Use the exact document name and section name available in the retrieved "
"context or metadata. Never invent, modify, abbreviate, or guess a document "
"name or section name. "

"If the retrieved context contains a document name but no section name, do not "
"invent a section name. Use only section information that is actually present "
"in the retrieved context or metadata. "

"Do not cite unrelated sources. A source must directly support the claim it "
"is attached to. "

"Do not use source IDs as the user-facing citation. Source IDs may be returned "
"separately by the application's structured response, but the Markdown answer "
"must display human-readable citations using document name and section. "

"If the answer contains multiple sources, cite each relevant source separately. "

# Markdown document structure
"When the question requires a substantive answer, structure the Markdown "
"naturally. Use a heading only when useful. Do not add unnecessary headings. "

"If appropriate, end the Markdown answer with a '### Sources' section containing "
"the unique document name and section citations used in the answer. "
"Do not add sources that were not directly used. "

"If the context does not sufficiently support the requested conclusion, "
"return an empty answer rather than an unsupported explanation. "

"Do not call, create, or assume the existence of any response-formatting tool. "
"Return the final Markdown answer directly."


)

# VALIDATION

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
