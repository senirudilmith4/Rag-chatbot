# 🎓 University Assistant

An AI-powered Retrieval-Augmented Generation (RAG) chatbot for university students. Ask questions about module descriptors, policies, forms, exam papers, and timetables — and get accurate, sourced answers drawn directly from university PDF documents.

Built with **FastAPI**, **ChromaDB**, **Google Gemini 2.5 Flash**, and **Inngest** for reliable background job orchestration. 

---

## ✨ Features

- 📄 **PDF Ingestion** — Automatically loads, chunks, and embeds university PDFs into a persistent vector store
- 🔍 **Semantic Search** — Retrieves the most relevant document chunks using cosine similarity
- 🧠 **Metadata-Aware Filtering** — Detects document types (`module_descriptor`, `policy`, `form`, `exam_paper`, `timetable`) and applies smart filters to narrow search results
- 💬 **LLM-Powered Answers** — Generates clean, Markdown-formatted answers using Google Gemini 2.5 Flash, grounded strictly in retrieved context
- ⚙️ **Background Job Orchestration** — Uses Inngest for durable, retryable serverless functions (ingestion + query pipeline)
- 🖥️ **Frontend Client** — Lightweight frontend for interacting with the chatbot
- 🚀 **Render Deployment** — Designed for easy cloud deployment

---

## 🏗️ Architecture

```
Student Question
      │
      ▼
 Inngest Event (rag/query_pdf_ai)
      │
      ├─ Step 1: Extract metadata filters from question (Gemini)
      │
      ├─ Step 2: Embed question → Filtered similarity search (ChromaDB)
      │          └─ Fallback: Unfiltered search if too few results
      │
      ├─ Step 3: Build prompt with retrieved context chunks
      │
      └─ Step 4: Generate answer (Gemini 2.5 Flash)
                        │
                        ▼
              Structured Markdown Answer + Sources
```

**Ingestion Pipeline** (`rag/inngest-document`):
```
PDFs in data/docs/
    │
    ├─ Load & extract text
    ├─ Detect doc_type & metadata (Gemini)
    ├─ Chunk text (doc-type-aware chunking)
    ├─ Embed chunks
    └─ Upsert into ChromaDB (deterministic IDs — safe to re-run)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| LLM | Google Gemini 2.5 Flash |
| Vector Store | ChromaDB (persistent) |
| Job Orchestration | Inngest |
| Frontend | HTMl, CSS, Vanilla JS |
| Deployment | Render |

---

## 📁 Project Structure

```
RAG-CHATBOT/
├── backend/
│   ├── app/
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── custom_types.py       # Pydantic models (RAGChunkAndSrc, RAGSearchResult, etc.)
│   │   │   └── meta_detec.py         # Doc type detection & filter extraction (Gemini-powered)
│   │   ├── geminiAdapter.py          # Google Gemini API client wrapper
│   │   └── main.py                   # FastAPI app entry point + Inngest function definitions
│   ├── chroma_db/
│   │   ├── __init__.py
│   │   └── vector_db.py              # ChromaVectorStore — upsert & similarity search
│   ├── data/
│   │   ├── chroma_db/                # Persistent ChromaDB vector store (auto-created)
│   │   └── docs/                     # 📂 Place your university PDFs here
│   └── ingestion/
│       ├── __init__.py
│       └── load_docs.py              # PDF loading, chunking, embedding, chunk ID utilities
├── frontend/
│   ├── app.py                        # Frontend entry point
│   └── rag_client.py                 # Client for communicating with the backend API
├── venv/                             # Virtual environment (not committed)
├── .env                              # Environment variables (not committed)
├── .gitignore
└── requirements.txt
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root:

```env
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash          # Optional — defaults to gemini-2.5-flash

# Inngest
INNGEST_EVENT_KEY=your_inngest_event_key
INNGEST_SIGNING_KEY=your_inngest_signing_key
INNGEST_ENV=production                  # Set to "production" on Render; omit locally
```

---

## 🚀 Local Development

### Prerequisites

- Python 3.10+
- A Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey))
- An Inngest account ([inngest.com](https://www.inngest.com))
- Node.js (for the Inngest CLI)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/rag-chatbot.git
cd rag-chatbot

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Add Your PDFs

Place your university PDF documents inside `backend/data/docs/`. The ingestion pipeline will recursively scan for all `.pdf` files in that directory.

### Run the Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### Run the Inngest Dev Server

In a separate terminal, start the Inngest dev server to handle background jobs locally:

```bash
npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
```

The Inngest dashboard will be available at `http://localhost:8288`.

### Run the Frontend

In another terminal:

```bash
cd frontend
python app.py
```

### Trigger Document Ingestion

Use the Inngest Dev Server UI at `http://localhost:8288` to send the ingestion event, or via curl:

```bash
curl -X POST http://localhost:8288/e/your_event_key \
  -H "Content-Type: application/json" \
  -d '{"name": "rag/inngest-document", "data": {}}'
```

### Query the Chatbot

```bash
curl -X POST http://localhost:8288/e/your_event_key \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rag/query_pdf_ai",
    "data": {
      "question": "What are the learning outcomes for CM1601?",
      "top_k": 10
    }
  }'
```

---

## ☁️ Deploying to Render

### 1. Push to GitHub

Make sure your code is pushed to GitHub. Ensure `venv/` and `.env` are listed in `.gitignore`. If you want the vector store to persist across deploys, do **not** ignore `backend/data/chroma_db/` — or plan to re-trigger ingestion after each deploy.

### 2. Create a New Web Service on Render

- Go to [render.com](https://render.com) → **New** → **Web Service**
- Connect your GitHub repository
- Configure the service:

| Setting | Value |
|---|---|
| **Runtime** | Python 3 |
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r ../requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

### 3. Add Environment Variables

In your Render service → **Environment**, add:

| Key | Value |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `INNGEST_EVENT_KEY` | Your Inngest event key |
| `INNGEST_SIGNING_KEY` | Your Inngest signing key |
| `INNGEST_ENV` | `production` |

### 4. Connect Inngest to Your Render URL

In the [Inngest Cloud dashboard](https://app.inngest.com):

- Navigate to **Apps** → **Sync new app**
- Enter your Render app's Inngest endpoint: `https://your-app.onrender.com/api/inngest`
- Inngest will automatically discover and register your `ingest_document` and `query_pdf_ai` functions

### 5. Trigger Ingestion After Deploy

Once the service is live, trigger the ingestion event from the Inngest Cloud dashboard to populate the vector store with your PDFs.

---

## 📡 API Reference

### HTTP Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Confirms the chatbot server is running |
| `GET` | `/health` | Backend status check |
| `POST` | `/api/inngest` | Inngest webhook — auto-configured, do not call directly |

### Inngest Events

Functions are triggered by sending named events to Inngest, not via direct HTTP:

| Event Name | Payload | Description |
|---|---|---|
| `rag/inngest-document` | `{}` | Ingest all PDFs from `data/docs/` |
| `rag/query_pdf_ai` | `{ "question": "...", "top_k": 10 }` | Answer a student question using RAG |

### Query Response Shape

```json
{
  "answer": "### Answer\n...",
  "sources": ["data/docs/module_cm1601.pdf"],
  "num_contexts": 8,
  "filters_applied": { "doc_type": "module_descriptor" },
  "contexts": ["chunk text 1", "chunk text 2", "..."]
}
```

---

## 🔎 Document Type Support

The system automatically classifies ingested PDFs and applies targeted filters during search:

| `doc_type` | Examples |
|---|---|
| `module_descriptor` | Module syllabi, learning outcomes, assessment criteria |
| `policy` | Plagiarism policy, attendance policy, academic regulations |
| `form` | Deferral forms, appeal forms, enrolment forms |
| `exam_paper` | Past exam papers |
| `timetable` | Lecture schedules, exam timetables |
| `unknown` | Anything that doesn't fit the above categories |

---

## 🧩 How RAG Works Here

1. **Ingestion** — PDFs are chunked into overlapping segments using doc-type-aware sizing. Each chunk is embedded into a vector and stored in ChromaDB alongside metadata (`doc_type`, `source`, `module_code`, etc.). Deterministic chunk IDs mean re-ingestion is safe and idempotent.

2. **Query** — When a student asks a question, Gemini extracts a metadata filter (e.g. `{"doc_type": "policy"}`). The question is then embedded and a filtered cosine similarity search finds the most relevant chunks. If the filtered search returns fewer than 2 results, the system automatically falls back to an unfiltered search across the full collection.

3. **Generation** — The top chunks are assembled into a context block and passed to Gemini 2.5 Flash with a strict system prompt: answer only from the provided context, or respond with "I could not find this in the university documents."

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## 📜 License

[MIT](LICENSE)
