"""
Generation Module
Uses Groq's llama-3.3-70b-versatile to generate grounded responses
from retrieved chunks. Enforces source attribution and prevents hallucination.
"""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Configuration
MODEL = "llama-3.3-70b-versatile"

# System prompt that enforces grounding
SYSTEM_PROMPT = """You are "The Unofficial Guide" — a helpful assistant that answers questions about Minerva University student favorite spots (cafes, restaurants, study spaces) across rotation cities.

CRITICAL RULES:
1. Answer ONLY using information from the provided source documents below. Do NOT use your general knowledge about these cities, restaurants, or cafes.
2. If the source documents don't contain enough information to answer the question, say: "I don't have enough information in my sources to answer that question."
3. When you reference specific information, mention the source document it comes from using the format [Source: filename].
4. Be specific — include prices, ratings, addresses, and student quotes when available in the sources.
5. If different sources give conflicting opinions, present both perspectives.
6. Do NOT make up restaurant names, prices, ratings, or any details that aren't in the provided sources."""

USER_PROMPT_TEMPLATE = """Here are the source documents retrieved for this question:

{context}

---

Question: {question}

Answer the question using ONLY the information in the source documents above. Cite your sources."""


def get_groq_client() -> Groq:
    """Initialize the Groq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Copy .env.example to .env and add your key."
        )
    return Groq(api_key=api_key)


def format_context(retrieved_chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a context string for the LLM prompt.
    Each chunk is labeled with its source for citation.
    """
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        context_parts.append(
            f"[Document {i} — Source: {chunk['source']} ({chunk['city']})]\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(context_parts)


def generate_response(question: str, retrieved_chunks: list[dict]) -> dict:
    """
    Generate a grounded response using the LLM.

    Args:
        question: The user's question
        retrieved_chunks: List of chunk dicts from retriever.retrieve()

    Returns:
        Dict with keys: 'answer', 'sources', 'model'
    """
    client = get_groq_client()

    # Format the context from retrieved chunks
    context = format_context(retrieved_chunks)

    # Build the user prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        context=context,
        question=question,
    )

    # Call the LLM
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=MODEL,
        temperature=0.3,  # Low temperature for factual accuracy
        max_tokens=1024,
    )

    answer = chat_completion.choices[0].message.content

    # Extract unique sources from retrieved chunks (programmatic attribution)
    sources = list(dict.fromkeys(
        f"{chunk['source']} ({chunk['city']})" for chunk in retrieved_chunks
    ))

    return {
        "answer": answer,
        "sources": sources,
        "model": MODEL,
    }


if __name__ == "__main__":
    from retriever import get_retriever, retrieve

    model, collection = get_retriever()

    # Test with a sample question
    test_questions = [
        "Which cafes in Berlin have the best wifi for long study sessions?",
        "What is the best pizza restaurant in New York City?",  # Out-of-scope test
    ]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"❓ {question}")
        print("=" * 60)

        chunks = retrieve(question, model, collection, top_k=5)
        result = generate_response(question, chunks)

        print(f"\n💬 Answer:\n{result['answer']}")
        print(f"\n📎 Sources: {', '.join(result['sources'])}")
