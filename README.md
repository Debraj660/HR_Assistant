# HR Assistant

HR Assistant is a document-backed policy question-answering app for internal HR documents. It lets an admin upload HR policy files, indexes their contents into a vector database, and answers employee questions using only retrieved policy context.

The current application uses Streamlit for the UI, Supabase for uploaded document storage and metadata, Qdrant for vector search, Jina embeddings for document embeddings, and Groq-hosted chat models through LangChain.

## Features

- Upload HR documents from the Streamlit sidebar.
- Supports `.pdf`, `.docx`, `.txt`, and `.md` files up to 20 MB.
- Stores uploaded files in Supabase Storage.
- Stores document metadata in a Supabase `documents` table.
- Splits uploaded documents into retrievable chunks.
- Indexes chunks in Qdrant with citation metadata.
- Lets users ask HR policy questions through a chat interface.
- Forces answers to stay grounded in retrieved policy context.
- Displays human-readable source citations in the generated Markdown answer.
- Deletes uploaded documents from both Supabase and Qdrant.

## Project Structure

```text
HR-Assistant/
├── app.py
├── main.py
├── init_DB.py
├── requirement.txt
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
├── rag.ipynb
└── ragenv/
```

## Main Files

### `app.py`

Streamlit web application. It provides:

- page setup and app title
- admin sidebar for upload and delete actions
- uploaded document list
- cached assistant initialization
- chat history in `st.session_state`
- chat input and answer rendering

The app calls the pipeline functions from `assistant/pipeline.py` to upload, index, remove, list, build, and query documents.

### `main.py`

Command-line demo entry point. It builds the HR assistant and asks a few hardcoded sample questions:

- `How many paid annual leave days do I get?`
- `What is the notice period during probation?`
- `Can I work from home every day?`

Use this file when you want to test the assistant outside the Streamlit UI.

### `assistant/pipeline.py`

Central orchestration layer. It connects the document storage, loader, splitter, vector store, retriever, LLM, and agent.

Important functions:

- `add_uploaded_document()` uploads a file to Supabase, loads it, chunks it, and indexes it in Qdrant.
- `remove_document()` deletes a document from Qdrant and Supabase.
- `get_all_documents()` retrieves Supabase metadata records.
- `build_hr_assistant()` validates configuration, loads Qdrant, creates a retriever, creates the search tool, initializes the LLM, and builds the LangChain agent.
- `ask()` sends a user question to the agent and returns the final answer.

### `assistant/config.py`

Loads configuration from environment variables first, then from Streamlit secrets if available.

It defines:

- API keys
- Supabase settings
- Qdrant settings
- LLM model name
- embedding model name
- chunking settings
- retriever top-k value
- strict HR assistant system prompt

The system prompt tells the assistant to answer only from retrieved policy context, return Markdown, and cite sources using this format:

```text
[Source: Document Name — Section Name]
```

### `assistant/doc_loader.py`

Loads uploaded document bytes into LangChain document objects.

Supported file types:

- PDF through `PyPDFLoader`
- DOCX through `Docx2txtLoader`
- TXT through `TextLoader`
- Markdown through `TextLoader`

It also attaches metadata used later for citations, including:

- `document_id`
- `filename`
- `document_type`
- `source_type`
- `section`
- `page_number` for PDFs

For Markdown files, the section is inferred from the latest Markdown heading in the loaded text.

### `assistant/splitters.py`

Splits loaded documents using `RecursiveCharacterTextSplitter`.

Current defaults from `assistant/config.py`:

- chunk size: `1000`
- chunk overlap: `150`

### `assistant/embeddings.py`

Creates the embedding model.

Current model:

```text
jina-embeddings-v2-base-en
```

### `assistant/vector_store.py`

Handles Qdrant vector database operations.

It can:

- create a Qdrant client
- check whether the collection exists
- create a payload index for `metadata.document_id`
- build a new Qdrant collection from chunks
- load an existing collection
- add new document chunks
- delete all vectors for one document
- create a retriever
- delete the entire vector collection

The payload index is important because document deletion filters Qdrant points by `metadata.document_id`.

### `assistant/tools.py`

Creates the LangChain tool used by the agent.

The tool searches the retriever and returns matching chunks with:

- source number
- citation
- document name
- section
- document ID
- content

The agent uses this returned context to produce grounded HR answers.

### `assistant/llm.py`

Creates the chat model through Groq.

Current model from config:

```text
openai/gpt-oss-20b
```

Temperature is set to `0.1` for more deterministic answers.

### `assistant/agent.py`

Creates the LangChain agent using:

- the configured LLM
- the HR policy search tool
- the strict system prompt from `assistant/config.py`

### `assistant/supabase_storage.py`

Handles Supabase Storage and database metadata.

It can:

- create the Supabase client
- upload document bytes into Supabase Storage
- insert document metadata into the `documents` table
- list uploaded documents
- retrieve one document metadata record
- download a stored document
- delete both the storage object and metadata record

If metadata insertion fails after file upload, the code attempts to roll back the uploaded storage object.

### `assistant/logger.py`

Provides a simple stdout logger with this format:

```text
timestamp - logger_name - level - message
```

### `init_DB.py`

Utility script intended to reset Qdrant collection data. The file currently has blank Qdrant credentials inside the script, so it should be updated to read from environment variables before use.

### `data/benefits-policy.md`

Sample HR policy document covering:

- health coverage tiers
- leave travel allowance
- wellness benefits
- exclusions
- HR benefits contact

### `rag.ipynb`

Prototype notebook for local RAG experimentation. It is not part of the active Streamlit application path.

The production Streamlit flow uses Qdrant for vector search and Supabase for file storage and document metadata.

### `ragenv/`

Local Python virtual environment. It is ignored by Git and should not be committed.

## How The App Works

1. An admin uploads an HR document from the Streamlit sidebar.
2. The file is validated for type and size.
3. The file is uploaded to Supabase Storage.
4. Metadata is inserted into the Supabase `documents` table.
5. The uploaded bytes are loaded into LangChain document objects.
6. Documents are split into overlapping chunks.
7. Chunks are embedded with Jina embeddings.
8. Chunks and metadata are stored in Qdrant.
9. The assistant creates a retriever over the Qdrant collection.
10. User questions are passed to a LangChain agent.
11. The agent calls the HR policy search tool.
12. The final answer is generated only from retrieved policy context.

## Requirements

Python 3.10 or newer is recommended.

Install the Python dependencies from the provided file:

```bash
pip install -r requirement.txt
```

Depending on your environment and loader usage, you may also need packages used indirectly by loaders and storage code, such as:

```bash
pip install supabase pypdf docx2txt
```

## Environment Variables

Create a `.env` file in the project root for local development.

Required variables:

```env
GROQ_API_KEY=
JINA_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
QDRANT_URL=
QDRANT_API_KEY=
```

Optional variables:

```env
SUPABASE_BUCKET_NAME=hr-documents
QDRANT_COLLECTION_NAME=hr_documents
```

The existing `.env` file is ignored by Git. Do not commit real service keys.

## Supabase Setup

The app expects:

- a Supabase Storage bucket, default name `hr-documents`
- a Supabase table named `documents`

A compatible `documents` table should include at least:

```text
id
filename
storage_path
file_type
file_size
uploaded_at
```

The app uses the Supabase service role key because it performs server-side storage and metadata operations.

## Qdrant Setup

The app expects a reachable Qdrant instance and a configured collection name.

If the collection does not exist, it is created when the first uploaded document is indexed. The app also creates a payload index on:

```text
metadata.document_id
```

That index is used to delete all vectors belonging to a removed document.

## Running The Streamlit App

From the project root:

```bash
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

Typical first-time flow:

1. Add the required environment variables.
2. Start Streamlit.
3. Upload an HR document from the sidebar.
4. Wait for upload and indexing to complete.
5. Ask a policy question in the chat input.

## Running The CLI Demo

From the project root:

```bash
python main.py
```

This builds the assistant and runs the sample questions in `main.py`.

## Notes And Current Limitations

- The app will not start the assistant until a Qdrant collection exists.
- The Streamlit UI displays a startup message when no HR documents have been uploaded yet.
- Unsupported file types are rejected.
- Files larger than 20 MB are rejected.
- The assistant is intentionally conservative. If retrieved policy context is not enough, the system prompt instructs it to return an empty answer.
- `ask()` only applies the fallback message when the agent returns an empty response.
- `init_DB.py` should be made environment-based before using it to reset Qdrant.
- The file `assistant/_init_.py` is empty and appears to be named with single underscores. A conventional package initializer would be `assistant/__init__.py`.
- `rag.ipynb` appears to be a prototype artifact and is not part of the active Streamlit application path.

## Troubleshooting

### Missing configuration values

If startup fails with missing configuration values, make sure all required environment variables are present in `.env` or Streamlit secrets.

### No HR documents uploaded

Upload at least one supported HR document from the sidebar. The assistant needs indexed document chunks before it can answer questions.

### Upload succeeds but indexing fails

The pipeline attempts to roll back the Supabase upload when indexing fails. Check:

- Qdrant URL and API key
- Jina API key
- document file type
- readable document text
- network access to external services

### Delete fails

Deletion removes vectors from Qdrant before deleting Supabase storage and metadata. Check that the Qdrant payload index for `metadata.document_id` exists and that the Supabase service role key has the required permissions.

## Possible Improvements

- Rename `requirement.txt` to the conventional `requirements.txt`.
- Add missing direct dependencies such as `supabase`, `pypdf`, and `docx2txt` to the dependency file if they are required in the target environment.
- Replace `assistant/_init_.py` with `assistant/__init__.py`.
- Update `init_DB.py` to use `assistant.config` instead of hardcoded blank credentials.
- Add automated tests for upload rollback, document deletion, loader metadata, and fallback behavior.
- Add a setup script or SQL migration for the Supabase `documents` table.
- Add a small health-check page for Supabase, Qdrant, Groq, and Jina connectivity.
