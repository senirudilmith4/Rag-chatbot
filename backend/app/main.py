import asyncio
import logging
import os
import inngest
from inngest.fast_api import serve
from fastapi import Body, FastAPI
from inngest.experimental import ai  # Simplifies calling LLMs, managing retries, background AI execution
from dotenv import load_dotenv
from ingestion.load_docs import DOCS_PATH, load_pdf,chunk_texts, embed_texts,sample_texts_for_metadata,chunk_id
from chroma_db.vector_db import ChromaVectorStore
from app.schemas.custom_types import RAGChunkAndSrc, RAGUpsertResult, RAGSearchResult, RAGQueryResult
from app.schemas.meta_detec import detect_doc_type_and_metadata
from app.services.query_service import run_query
from fastapi.middleware.cors import CORSMiddleware



load_dotenv()  # Load environment variables from .env file
logger = logging.getLogger("uvicorn")



inngest_client = inngest.Inngest(   # Initialize Inngest client for handling serverless functions and AI tasks
    app_id="rag_api",               # Unique identifier for Inngest application
    logger = logging.getLogger("uvicorn"),
    serializer=inngest.PydanticSerializer(),
    event_key=os.getenv("INNGEST_EVENT_KEY"),
    signing_key=os.getenv("INNGEST_SIGNING_KEY"),
)

app = FastAPI(                # creates a web server
    title="LLM-RAG API", 
    version="1.0.0"
    )     
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)


vector_db = ChromaVectorStore()
# app.include_router(ask_router, prefix="/api")   # take all the routes defined in ask router and add them to the main app with the prefix /api

@inngest_client.create_function(
    fn_id="RAG: Ingest Document",
    trigger=inngest.TriggerEvent(event="rag/inngest-document"),
)
async def ingest_document(ctx: inngest.Context):
 
    def _load() -> RAGChunkAndSrc:
        """Load every PDF in DOCS_PATH, chunk it, and collect metadata."""
        pdf_files = list(DOCS_PATH.rglob("*.pdf"))
        if not pdf_files:
            raise ValueError(f"No PDF files found in {DOCS_PATH}")
 
        all_chunks: list[str] = []
        all_ids: list[str] = []
        metadatas: list[dict] = []
 
        for pdf in pdf_files:
            source = str(pdf)
            texts = load_pdf(source)
 
            # Sample across the full document for better type detection
            sample = sample_texts_for_metadata(texts)
            base_metadata = detect_doc_type_and_metadata(source, sample)
            doc_type = base_metadata.get("doc_type", "default")
 
            # Use doc-type-aware chunking
            chunks = chunk_texts(texts, doc_type=doc_type)
 
            for i, c in enumerate(chunks, start=1):
                all_chunks.append(c)
                # Deterministic ID prevents duplicate vectors on re-ingestion
                all_ids.append(chunk_id(c, source))
                metadatas.append({**base_metadata, "chunk": i})
 
        return RAGChunkAndSrc(chunks=all_chunks, metadatas=metadatas)
 
    def _upsert(chunk_and_src: RAGChunkAndSrc) -> RAGUpsertResult:
        """Embed chunks and upsert into ChromaDB."""
        chunks = chunk_and_src.chunks
        vecs = embed_texts(chunks)
        # Re-derive deterministic IDs from the chunk content + source stored in metadata
        ids = [
            chunk_id(c, meta.get("source", "unknown"))
            for c, meta in zip(chunks, chunk_and_src.metadatas)
        ]
        vector_db.upsert(ids, chunks, vecs, chunk_and_src.metadatas)
        return RAGUpsertResult(ingested=len(chunks))
 
    chunk_and_src = await ctx.step.run(
        "load-and-chunk",
        lambda: asyncio.to_thread(_load),
        output_type=RAGChunkAndSrc,
    )
 
    ingested = await ctx.step.run(
        "embed-and-upsert",
        lambda: asyncio.to_thread(_upsert, chunk_and_src),
        output_type=RAGUpsertResult,
    )
 
    logger.info("Chunks ingested: %d", ingested.ingested)
    return ingested.model_dump()
    
serve(
    app,                       # <- pass your FastAPI app first
    client=inngest_client,     # <- then the client
    functions=[ingest_document]     # optional prefix
)


@app.post("/ask")
async def query_pdf_ai(payload: dict = Body(...)):
    question: str = payload["question"]
    top_k: int = payload.get("top_k", 10)
    return await run_query(question, top_k)


@app.get("/health")
def health_check():
    return {"status": "backend is running"} # defines a simple endpoint to check if the backend is running. When you access /health, it will return a JSON response indicating the status of the backend.

@app.get("/")
def home():
    return {"message": "Chatbot running"}