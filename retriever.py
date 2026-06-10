"""
Retrieval Module
Queries the ChromaDB vector store to find the most relevant chunks
for a given user query.
"""

from sentence_transformers import SentenceTransformer
from embedder import get_chroma_client, COLLECTION_NAME, EMBEDDING_MODEL


def get_retriever():
    """
    Initialize the retriever components (model + collection).
    Returns a tuple of (model, collection).
    """
    model = SentenceTransformer(EMBEDDING_MODEL)
    client = get_chroma_client()
    collection = client.get_collection(COLLECTION_NAME)
    return model, collection


def retrieve(query: str, model: SentenceTransformer, collection,
             top_k: int = 5, city_filter: str = None) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks for a query.

    Args:
        query: The user's question
        model: SentenceTransformer model for embedding the query
        collection: ChromaDB collection to search
        top_k: Number of results to return
        city_filter: Optional city name to filter results

    Returns:
        List of result dicts with keys:
        'text', 'source', 'city', 'chunk_index', 'distance'
    """
    # Embed the query
    query_embedding = model.encode([query]).tolist()

    # Build query parameters
    query_params = {
        "query_embeddings": query_embedding,
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }

    # Add city filter if specified
    if city_filter:
        query_params["where"] = {"city": city_filter}

    # Query ChromaDB
    results = collection.query(**query_params)

    # Format results into a clean list of dicts
    formatted = []
    for i in range(len(results["ids"][0])):
        formatted.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "city": results["metadatas"][0][i]["city"],
            "chunk_index": results["metadatas"][0][i]["chunk_index"],
            "distance": results["distances"][0][i],
        })

    return formatted


def print_retrieval_results(query: str, results: list[dict]):
    """Pretty-print retrieval results for debugging."""
    print(f"\n🔍 Query: \"{query}\"")
    print(f"   Retrieved {len(results)} chunks:\n")

    for i, r in enumerate(results, 1):
        print(f"   [{i}] Distance: {r['distance']:.4f}")
        print(f"       Source: {r['source']} ({r['city']})")
        print(f"       Text: {r['text'][:200]}...")
        print()


if __name__ == "__main__":
    model, collection = get_retriever()
    print(f"✅ Retriever ready. Collection has {collection.count()} chunks.\n")

    # Test with evaluation questions
    test_queries = [
        "Which cafes in Berlin have the best wifi for long study sessions?",
        "What is the cheapest filling meal a student can get in Hyderabad?",
        "Which San Francisco restaurants are affordable and filling for students?",
        "Are there any 24-hour study spots in Seoul?",
        "Which places should students avoid eating at in Buenos Aires?",
    ]

    for query in test_queries:
        results = retrieve(query, model, collection, top_k=5)
        print_retrieval_results(query, results)
        print("=" * 60)
