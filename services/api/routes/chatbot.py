"""
chatbot.py — FastAPI router for the FAQ chatbot.

Endpoints
---------
GET  /api/v1/chatbot/faqs            → list all FAQ chips
POST /api/v1/chatbot/query           → natural-language query → matched scheme
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.api.db import get_db
from services.api.chatbot.matcher import find_best_match
from services.api.chatbot.scheme_retriever import find_matching_schemes
from services.api.chatbot.generator import generate_scheme_answer

router = APIRouter(tags=["Chatbot"])


# ── Pydantic models ──────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    matched: bool
    faq_question: Optional[str] = None
    answer: Optional[str] = None
    similarity: Optional[float] = None
    scheme: Optional[dict] = None
    suggestions: Optional[list] = None


class AssistantRequest(BaseModel):
    question: str


class AssistantResponse(BaseModel):
    answer: str
    schemes: list[dict]
    retrieval_count: int


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fetch_scheme(cur, scheme_id: str) -> Optional[dict]:
    """
    Fetch a scheme row from the *schemes* table (confirmed column names from
    schemas/postgres.sql).  Returns a slim dict for the chatbot card.
    """
    cur.execute(
        """
        SELECT s.id, s.name, s.description, s.eligibility_text,
               s.state_code, s.status, s.link, s.tags,
               c.name AS category_name
        FROM   schemes s
        LEFT JOIN categories c ON s.category_id = c.id
        WHERE  s.id = %s
        """,
        (scheme_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id":               str(row["id"]),
        "name":             row["name"],
        "description":      row["description"],
        "eligibility_text": row["eligibility_text"],
        "state_code":       row["state_code"],
        "status":           row["status"],
        "link":             row["link"],
        "tags":             row["tags"],
        "category_name":    row["category_name"],
    }


def _top_suggestions(cur, n: int = 3) -> list:
    """Return top-N FAQ question strings as fallback suggestions."""
    cur.execute(
        "SELECT question FROM faqs ORDER BY id LIMIT %s",
        (n,),
    )
    return [r["question"] for r in cur.fetchall()]


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/chatbot/faqs")
def list_faqs():
    """Return FAQ questions and answers for the frontend accordion."""
    with get_db() as cur:
        cur.execute("SELECT id, question, answer FROM faqs ORDER BY id")
        rows = cur.fetchall()
    return {
        "faqs": [
            {"id": r["id"], "question": r["question"], "answer": r["answer"]}
            for r in rows
        ]
    }


@router.post("/chatbot/query", response_model=QueryResponse)
def chatbot_query(body: QueryRequest):
    """
    Match the user's question to the best FAQ entry via semantic similarity.
    If a confident match is found, also return the linked scheme card.
    If no match clears the threshold, return suggestion chips instead.
    """
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must not be empty")

    with get_db() as cur:
        match = find_best_match(question, cur)

        if match is None:
            suggestions = _top_suggestions(cur)
            return QueryResponse(matched=False, suggestions=suggestions)

        scheme = None
        if match["scheme_id"]:
            scheme = _fetch_scheme(cur, match["scheme_id"])

        return QueryResponse(
            matched=True,
            faq_question=match["faq_question"],
            answer=match["faq_answer"],
            similarity=match["similarity"],
            scheme=scheme,
        )


@router.post("/chatbot/assistant", response_model=AssistantResponse)
def chatbot_assistant(body: AssistantRequest):
    """
    RAG + local-Qwen scheme assistant endpoint.
    Retrieves semantic schemes based on query and generates a grounded response.
    """
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must not be empty")

    with get_db() as cur:
        schemes = find_matching_schemes(question, cur, limit=5)
        
        # Ensure returned scheme IDs are strings for JSON serialization
        for scheme in schemes:
            if "id" in scheme and scheme["id"] is not None:
                scheme["id"] = str(scheme["id"])

        answer = generate_scheme_answer(question, schemes)
        
    return AssistantResponse(
        answer=answer,
        schemes=schemes,
        retrieval_count=len(schemes)
    )

