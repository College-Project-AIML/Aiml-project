"""
generator.py - Generates grounded chatbot answers using a local Ollama model.
"""

from __future__ import annotations

import requests
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))

PROMPT_TEMPLATE = """You are a helpful and strictly factual Indian Government Schemes Assistant. 
You must answer the User Query based ONLY on the Provided Context. 
Do not use any external knowledge.

RULES:
1. Answer only from the provided scheme context.
2. Never invent scheme names, eligibility requirements, benefits, amounts, deadlines, or links.
3. Return clean plain text in exactly this structure, with each item on its own line:
   Based on your question, these schemes may be relevant:
   Scheme name
   • Short reason it may match.
   • One key eligibility fact, only when present in the context.
   Scheme name
   • Short reason it may match.
4. Use at most 3 schemes and at most 2 bullets per scheme.
5. Use short phrases, not long paragraphs. Do not use markdown symbols such as **.
6. Do not repeat full descriptions, unsupported facts, links, similarity scores, or filler text.
7. Do not add an introduction other than the required first line.

Provided Context:
{context}

User Query: {query}
Answer:"""


def generate_scheme_answer(query: str, schemes: list[dict]) -> str:
    """
    Generate an answer to the user's query grounding it in the supplied schemes.
    Uses the local Ollama model via REST API.
    """
    if not schemes:
        return "I couldn't find any relevant schemes matching your query in our database."

    # Build context from at most 3 retrieved schemes
    context_blocks = []
    for index, scheme in enumerate(schemes[:3], start=1):
        name = scheme.get("name", "N/A")
        status = scheme.get("status", "N/A")
        state_code = scheme.get("state_code", "N/A")
        category_name = scheme.get("category_name", "N/A")
        
        description = str(scheme.get("description") or "N/A")
        if len(description) > 500:
            description = description[:497] + "..."
            
        eligibility = str(scheme.get("eligibility_text") or "N/A")
        if len(eligibility) > 500:
            eligibility = eligibility[:497] + "..."
            
        link = scheme.get("link", "N/A")
        block = (
            f"Scheme {index}:\n"
            f"- Name: {name}\n"
            f"- Status: {status}\n"
            f"- State Code: {state_code}\n"
            f"- Category: {category_name}\n"
            f"- Description: {description}\n"
            f"- Eligibility: {eligibility}\n"
            f"- Link: {link}\n"
        )
        context_blocks.append(block)

    context_str = "\n".join(context_blocks)
    prompt = PROMPT_TEMPLATE.format(context=context_str, query=query)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "30m",
        "options": {
            "temperature": 0.2,
            "num_predict": 120,
            "num_ctx": 2048
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "").strip()
        
        return answer.strip()
    except requests.exceptions.RequestException:
        return ("I'm currently unable to generate a response because the local AI model "
                "is unavailable or timed out. Please try again later.")


def warm_generator() -> None:
    """Ask Ollama to load and retain the model before the first user query."""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": " ",
            "stream": False,
            "keep_alive": "30m",
            "options": {"num_predict": 1, "num_ctx": 256},
        },
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
