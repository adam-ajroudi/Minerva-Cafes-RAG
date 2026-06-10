"""
Query Module
End-to-end function that ties retrieval and generation together.
Used by the Gradio interface and for evaluation.
"""

from retriever import get_retriever, retrieve
from generator import generate_response


# Load model and collection once at module level
_model = None
_collection = None


def _ensure_initialized():
    """Lazy-initialize the retriever components."""
    global _model, _collection
    if _model is None or _collection is None:
        _model, _collection = get_retriever()


def ask(question: str, top_k: int = 5, city_filter: str = None) -> dict:
    """
    End-to-end query: retrieve relevant chunks and generate a grounded answer.

    Args:
        question: The user's question in plain language
        top_k: Number of chunks to retrieve
        city_filter: Optional city name to restrict search

    Returns:
        Dict with keys:
        - 'answer': The generated response text
        - 'sources': List of source filenames
        - 'retrieved_chunks': The raw retrieved chunks (for evaluation)
        - 'model': The LLM model used
    """
    _ensure_initialized()

    # Step 1: Retrieve relevant chunks
    chunks = retrieve(question, _model, _collection,
                      top_k=top_k, city_filter=city_filter)

    # Step 2: Generate grounded response
    result = generate_response(question, chunks)

    # Add retrieved chunks to the result for evaluation/debugging
    result["retrieved_chunks"] = chunks

    return result


if __name__ == "__main__":
    # Quick end-to-end test
    result = ask("Which cafes in Seoul have the best wifi for studying?")
    print(f"Answer: {result['answer']}\n")
    print(f"Sources: {result['sources']}")
    print(f"Chunks retrieved: {len(result['retrieved_chunks'])}")
