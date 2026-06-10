"""
Embedding & Vector Store Module
Embeds chunks using all-MiniLM-L6-v2 and stores them in a local ChromaDB collection.
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer

# Configuration
COLLECTION_NAME = "minerva_spots"
CHROMA_DIR = "chroma_data"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_embedding_model() -> SentenceTransformer:
    """Load the sentence transformer model."""
    print(f"🧠 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"   Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}")
    return model


def get_chroma_client() -> chromadb.PersistentClient:
    """Get or create a persistent ChromaDB client."""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def build_vector_store(chunks: list[dict], force_rebuild: bool = False):
    """
    Embed all chunks and store them in ChromaDB.

    Args:
        chunks: List of chunk dicts from chunker.chunk_documents()
        force_rebuild: If True, delete existing collection and rebuild
    """
    model = get_embedding_model()
    client = get_chroma_client()

    # Check if collection already exists
    existing_collections = [c.name for c in client.list_collections()]

    if COLLECTION_NAME in existing_collections:
        if force_rebuild:
            print(f"🗑️  Deleting existing collection '{COLLECTION_NAME}'...")
            client.delete_collection(COLLECTION_NAME)
        else:
            collection = client.get_collection(COLLECTION_NAME)
            count = collection.count()
            print(f"✅ Collection '{COLLECTION_NAME}' already exists with {count} chunks.")
            print("   Use force_rebuild=True to rebuild.")
            return collection

    print(f"\n📦 Building vector store with {len(chunks)} chunks...")

    # Prepare data for ChromaDB
    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        ids.append(f"chunk_{i}")
        documents.append(chunk["text"])
        metadatas.append({
            "source": chunk["source"],
            "city": chunk["city"],
            "chunk_index": chunk["chunk_index"],
        })

    # Embed all chunks
    print("   Embedding chunks...")
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    embeddings_list = embeddings.tolist()

    # Create collection and add data
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # Use cosine similarity
    )

    # Add in batches (ChromaDB has a limit per call)
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
            embeddings=embeddings_list[i:end],
        )

    print(f"✅ Vector store built: {collection.count()} chunks stored in ChromaDB")
    return collection


if __name__ == "__main__":
    from ingest import load_documents
    from chunker import chunk_documents

    documents = load_documents()
    chunks = chunk_documents(documents)
    collection = build_vector_store(chunks, force_rebuild=True)
    print(f"\nTotal chunks in store: {collection.count()}")
