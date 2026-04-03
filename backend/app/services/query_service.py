import asyncio
import logging
from app.schemas.custom_types import RAGSearchResult
from app.schemas.meta_detec import extract_filters
from app.geminiAdapter import GeminiAdapter
from chroma_db.vector_db import ChromaVectorStore
from ingestion.load_docs import embed_texts


logger = logging.getLogger("uvicorn")
vector_db = ChromaVectorStore()

SYSTEM_PROMPT = """
    You are a University Academic Assistant.
    Answer ONLY using the provided context from university documents.
    If the answer is not found in the context, respond exactly with:
    "I could not find this in the university documents."
    Always format answers using clean Markdown.
    Formatting rules:
    - Use headings (###) for sections
    - Use numbered lists for learning outcomes or steps
    - Use bullet points for explanations
    - Leave blank lines between sections
    Response format:
    ### Answer
    A short explanation answering the question.
    ### Details
    Structured information such as outcomes, steps, or definitions.
    ### Sources
    List the document names where the information was found.
""".strip()

def _build_where_filter(filters: dict | None) -> dict | None:
    """
    Safely convert an extracted filter dict into a ChromaDB `where` clause.
 
    ChromaDB requires that every field used in a `where` clause exists on ALL
    documents in the collection — otherwise it raises an error. We guard
    against unknown fields here so a bad LLM extraction never crashes the query.
 
    Supported fields: doc_type
    """
    if not filters or not isinstance(filters, dict):
        return None
 
    allowed_fields = {"doc_type"}
    valid = {k: v for k, v in filters.items() if k in allowed_fields and isinstance(v, str)}
 
    if not valid:
        return None
 
    # Single-field filter: {"doc_type": "policy"}
    if len(valid) == 1:
        field, value = next(iter(valid.items()))
        return {field: {"$eq": value}}
 
    # Multi-field filter: wrap in $and
    return {"$and": [{k: {"$eq": v}} for k, v in valid.items()]}
 
 

def _search(question: str, top_k: int, filters: dict | None) -> RAGSearchResult:
    query_embedding = embed_texts([question])[0]
    where_clause = _build_where_filter(filters)
    results = None

    if where_clause:
        try:
            results = vector_db.similarity_search(query_embedding, top_k, where=where_clause)
            logger.info("Filtered search returned %d results", len(results["contexts"]))
        except Exception as e:
            logger.warning("Filtered search failed (%s) — falling back to unfiltered", e)
            results = None

    if not results or len(results["contexts"]) < 2:
        results = vector_db.similarity_search(query_embedding, top_k, where=None)

    for i, (ctx_text, src) in enumerate(zip(results["contexts"], results["sources"])):
        logger.info("Result %d | source: %s | preview: %s", i + 1, src, ctx_text[:200])

    return RAGSearchResult(contexts=results["contexts"], sources=results["sources"])


async def run_query(question: str, top_k: int) -> dict:
    filters = await asyncio.to_thread(extract_filters, question)
    logger.info("Extracted filters: %s", filters)

    found = await asyncio.to_thread(_search, question, top_k, filters)

    context_block = "\n\n".join(
        f"[Source: {found.sources[i]}]\n{found.contexts[i]}"
        for i in range(len(found.contexts))
    )

    prompt = f"""
        {SYSTEM_PROMPT}
        --------------------------------
        Context from University Documents:
        {context_block}
        --------------------------------
        Student Question:
        {question}
        Write the answer now.
    """.strip()

    gemini = GeminiAdapter()
    answer = await asyncio.to_thread(gemini.generate, prompt)

    logger.info("Query complete — %d contexts used", len(found.contexts))

    return {
        "answer": answer.strip(),
        "sources": list(set(found.sources)),
        "num_contexts": len(found.contexts),
        "filters_applied": filters,
        "contexts": found.contexts,
    }