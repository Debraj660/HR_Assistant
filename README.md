# HR Assistant

HR Assistant is a Streamlit-based internal policy assistant. It lets an admin upload HR policy documents, indexes those documents into Qdrant, and answers employee questions using only retrieved policy context.

The active application stack is:

- Streamlit for the web UI
- Supabase Storage for uploaded policy files
- Supabase Postgres for document metadata
- Qdrant for vector search
- Jina embeddings for document embeddings
- Groq and LangChain for the HR policy agent

## Features

- Upload HR documents from the Streamlit sidebar.
- Supports `.pdf`, `.docx`, `.txt`, and `.md` files.
- Rejects files larger than 20 MB.
- Stores uploaded files in Supabase Storage.
- Stores document metadata in a Supabase `documents` table.
- Loads, chunks, embeds, and indexes uploaded documents into Qdrant.
- Searches the top matching policy chunks for each clear user question.
- Validates questions before retrieval to reject unclear or malformed prompts.
- Answers only from retrieved policy context.
- Returns a fallback response when the question is unclear, retrieval is weak, or the model cannot produce a supported answer.
- Deletes documents from Qdrant, Supabase Storage, and Supabase metadata.

## Project Structure

```text
HR-Assistant/
├── app.py
├── main.py
├── init_DB.py
├── requirements.txt
├── README.md
├── DESIGN.md
├── .env
├── .gitignore
├── assistant/
│   ├── _init_.py
│   ├── agent.py
│   ├── config.py
│   ├── doc_loader.py
│   ├── embeddings.py
│   ├── llm.py
│   ├── logger.py
│   ├── pipeline.py
│   ├── splitters.py
│   ├── supabase_storage.py
│   ├── tools.py
│   └── vector_store.py
├── data/
│   └── benefits-policy.md
└── rag.ipynb
```

## How It Works

### Upload And Index

1. An admin uploads a supported document in the Streamlit sidebar.
2. The UI checks the file size limit.
3. `assistant.pipeline.add_uploaded_document()` uploads the raw file to Supabase Storage.
4. Supabase metadata is inserted into the `documents` table.
5. The uploaded bytes are loaded into LangChain document objects.
6. Metadata is attached to each document object.
7. Documents are split into chunks.
8. Chunks are embedded with Jina embeddings.
9. Chunk vectors and metadata are stored in Qdrant.
10. The cached assistant is cleared so the next query uses the updated knowledge base.

### Query And Answer

1. A user asks a question in the Streamlit chat input.
2. `assistant.pipeline.ask()` strips and validates the question.
3. A validation LLM decides whether the question is clear enough to process.
4. Unclear, ambiguous, empty, or malformed questions return the fallback response immediately.
5. Clear questions are sent to the HR agent.
6. The HR agent calls the `search_hr_policy_with_context` tool.
7. The tool retrieves the top matching chunks from Qdrant.
8. The model answers only from the retrieved context.
9. Empty or unsupported answers are converted to the fallback response.
10. Streamlit renders the final Markdown answer.

## Main Files

### `app.py`

Streamlit web application. It provides:

- page setup and title
- admin sidebar
- upload flow
- document list
- delete flow
- cached assistant initialization through `st.cache_resource`
- chat history through `st.session_state`
- chat input and Markdown answer rendering

### `main.py`

CLI demo entry point. It builds the HR assistant and asks three hardcoded sample questions. Use it for a quick local command-line smoke test after the app is configured and at least one document is indexed.

### `assistant/pipeline.py`

Central orchestration layer.

Important functions:

- `add_uploaded_document(filename, file_bytes)`: uploads, loads, chunks, embeds, and indexes a document.
- `remove_document(document_id)`: deletes vectors first, then deletes the Supabase file and metadata.
- `get_all_documents()`: lists document metadata from Supabase.
- `build_hr_assistant()`: validates config, loads Qdrant, builds the retriever, creates the tool, initializes the LLM, and creates the agent.
- `is_question_clear(llm, question)`: uses a strict validation prompt and returns `True` only for an exact `YES`.
- `ask(agent, question)`: validates the input, rejects unclear questions, invokes the HR agent, extracts the final answer, and applies fallback behavior.

### `assistant/config.py`

Loads configuration from environment variables first and Streamlit secrets second.

It defines:

- Groq and Jina API keys
- Supabase URL, service role key, and bucket name
- Qdrant URL, API key, and collection name
- LLM model name
- embedding model name
- chunk size and overlap
- retriever `top_k`
- strict HR policy system prompt

Current model and retrieval settings:

```text
LLM model: openai/gpt-oss-20b
Embedding model: jina-embeddings-v2-base-en
Chunk size: 1000
Chunk overlap: 150
Top retrieved chunks: 5
```

The system prompt requires the assistant to answer only from retrieved policy context, cite factual claims, avoid policy invention, and return an empty answer when context is insufficient.

### `assistant/doc_loader.py`

Loads uploaded bytes into LangChain documents.

Supported loaders:

- `.pdf`: `PyPDFLoader`
- `.docx`: `Docx2txtLoader`
- `.txt`: `TextLoader`
- `.md`: `TextLoader`

Attached metadata:

- `document_id`
- `filename`
- `document_type`
- `source_type`
- `section`
- `page_number` for PDFs when available

Markdown sections are inferred from the latest Markdown heading in the text. PDF sections are represented as page labels. TXT and DOCX currently use `General`.

### `assistant/splitters.py`

Splits LangChain documents with `RecursiveCharacterTextSplitter` using the configured chunk size and overlap.

### `assistant/embeddings.py`

Creates the Jina embedding model used by the Qdrant vector store.

### `assistant/vector_store.py`

Handles Qdrant operations:

- creates a Qdrant client
- checks whether the collection exists
- creates a payload index on `metadata.document_id`
- builds a collection from chunks
- loads an existing collection
- adds document chunks
- deletes all vectors for one document
- creates a retriever
- deletes the entire collection

The `metadata.document_id` payload index supports document-level vector deletion.

### `assistant/tools.py`

Creates the LangChain search tool.

The tool retrieves matching chunks and formats each result with:

- source number
- citation
- document name
- section name
- document ID
- retrieved content

### `assistant/llm.py`

Creates the Groq chat model with temperature `0`.

### `assistant/agent.py`

Creates the LangChain HR agent using the configured LLM, the HR policy search tool, and the system prompt from `assistant/config.py`.

### `assistant/supabase_storage.py`

Handles Supabase file and metadata operations:

- create Supabase client
- validate supported extensions and size
- upload file bytes to Supabase Storage
- insert metadata into the `documents` table
- list documents
- fetch one document
- download a stored document
- delete a storage object and metadata row

If Supabase metadata insertion fails after storage upload, the code attempts to remove the uploaded storage object.

### `assistant/logger.py`

Creates stdout loggers for the project.

### `init_DB.py`

Utility script intended to reset Qdrant data. It currently has blank credentials inside the file, so it should be updated to read from environment variables before use.

### `data/benefits-policy.md`

Sample HR policy document used for local testing or ingestion examples.

### `rag.ipynb`

Prototype notebook. It is not part of the active Streamlit application path.

## Requirements

Python 3.10 or newer is recommended.

Install dependencies:

```bash
pip install -r requirements.txt
```

The active app depends on:

- `streamlit`
- `langchain`
- `langchain-core`
- `langchain-community`
- `langchain-groq`
- `langchain-qdrant`
- `qdrant-client`
- `langchain-text-splitters`
- `jinaai`
- `supabase`
- `pypdf`
- `python-docx`
- `python-dotenv`

## Environment Variables

Create a `.env` file in the project root for local development, or configure the same values in Streamlit secrets.

Required:

```env
GROQ_API_KEY=
JINA_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
QDRANT_URL=
QDRANT_API_KEY=
```

Optional:

```env
SUPABASE_BUCKET_NAME=hr-documents
QDRANT_COLLECTION_NAME=hr_documents
```

Do not commit real service keys.

## Supabase Setup

The app expects:

- a Supabase Storage bucket, default `hr-documents`
- a Supabase table named `documents`

The `documents` table should include:

```text
id
filename
storage_path
file_type
file_size
uploaded_at
```

The app uses the Supabase service role key for server-side storage and metadata operations.

## Qdrant Setup

The app expects a reachable Qdrant instance.

The collection name defaults to:

```text
hr_documents
```

If the collection does not exist, it is created during the first successful document index operation. The app also creates a payload index on:

```text
metadata.document_id
```

That payload index is used when deleting all vectors for one uploaded document.

## Run The Streamlit App

```bash
streamlit run app.py
```

First-time flow:

1. Add environment variables.
2. Start Streamlit.
3. Upload a supported HR document.
4. Wait for indexing.
5. Ask a clear policy question in the chat.

## Run The CLI Demo

```bash
python main.py
```

The CLI demo requires valid configuration and an existing indexed Qdrant collection.

## Fallback Behavior

The user receives this fallback response when:

- the question is empty
- the validation LLM marks the question unclear
- validation fails operationally
- the HR agent fails
- the agent response cannot be parsed
- the final answer is empty
- retrieved policy context is insufficient

```text
I couldn't find enough information in the available HR policies to answer that. Please contact HR.
```

## Notes And Limitations

- The assistant cannot answer until at least one document has been indexed in Qdrant.
- Upload/indexing is synchronous inside the Streamlit request.
- Question validation makes one additional LLM call before the policy agent call.
- TXT and DOCX files currently use `General` as the section name.
- PDF citations use page-based section names.
- Markdown section extraction is simple and based on headings.
- The grounding policy is intentionally strict, so some related questions may fall back instead of receiving a guessed answer.
- `assistant/_init_.py` appears to be a placeholder file. A conventional Python package initializer would be `assistant/__init__.py`.

## Possible Improvements

- Add tests for upload rollback, question validation, retrieval fallback, and document deletion.
- Move upload indexing to a background job with retry and progress state.
- Add authentication and authorization for admin actions.
- Add Supabase migrations for the `documents` table.
- Improve section extraction for DOCX and PDF documents.
- Improve PDF table extraction for structured benefits policies.
- Add answer evaluation sets for direct facts, table lookups, unknown questions, and citation quality.
- Add health checks for Supabase, Qdrant, Jina, and Groq.
