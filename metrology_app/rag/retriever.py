"""
Engineering RAG Retrieval & Hybrid Section Grounding Engine.
Ranks relevant standard clauses, SOP requirements, and manuals with exact section-level citations.
"""

import re
import math
from typing import List, Dict, Any, Optional
from .knowledge_store import get_all_documents


def tokenize(text: str) -> List[str]:
    """Tokenize and lowercase text into alpha-numeric terms."""
    return re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())


def compute_bm25_score(
    query_tokens: List[str],
    doc_tokens: List[str],
    doc_len: int,
    avg_doc_len: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Compute BM25 relevance score for a document."""
    score = 0.0
    for qt in query_tokens:
        freq = doc_tokens.count(qt)
        if freq > 0:
            # Term weight with length normalization
            num = freq * (k1 + 1)
            denom = freq + k1 * (1 - b + b * (doc_len / max(1.0, avg_doc_len)))
            score += num / denom
    return score


def search_engineering_knowledge(
    query: str,
    top_k: int = 3,
    filter_tags: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Execute hybrid retrieval against the engineering knowledge base.
    
    Returns structured results with exact citations:
      - doc_id, title, authority, revision, section, page, snippet, citation_string
    """
    docs = get_all_documents()
    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    # Calculate average doc length
    all_doc_tokens = [tokenize(f"{d['title']} {d['section_title']} {d['content']} {' '.join(d['tags'])}") for d in docs]
    avg_len = sum(len(dt) for dt in all_doc_tokens) / len(all_doc_tokens) if all_doc_tokens else 1.0

    scored_results = []
    for i, doc in enumerate(docs):
        dt = all_doc_tokens[i]
        
        # Tag filtering
        if filter_tags:
            doc_tags = set(t.lower() for t in doc.get("tags", []))
            if not any(ft.lower() in doc_tags for ft in filter_tags):
                continue

        score = compute_bm25_score(query_tokens, dt, len(dt), avg_len)
        
        # Bonus for exact phrase or tag matches
        for qt in query_tokens:
            if qt in [t.lower() for t in doc.get("tags", [])]:
                score += 1.5
            if qt in doc.get("doc_id", "").lower():
                score += 2.0

        if score > 0.1:
            citation_str = f"[{doc['doc_id']}] {doc['title']} §{doc['section']} ({doc['section_title']}), {doc['revision']}, p. {doc['page']}"
            scored_results.append({
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "authority": doc["authority"],
                "revision": doc["revision"],
                "section": doc["section"],
                "section_title": doc["section_title"],
                "page": doc["page"],
                "content": doc["content"],
                "citation": citation_str,
                "relevance_score": round(score, 3),
            })

    # Sort descending by relevance score
    ranked = sorted(scored_results, key=lambda x: x["relevance_score"], reverse=True)
    return ranked[:top_k]
