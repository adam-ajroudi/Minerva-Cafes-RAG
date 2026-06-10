"""
Build Script
Run this once to process documents and build the vector store.
After running, you can launch app.py for the query interface.

Usage: python build.py
"""

from ingest import load_documents
from chunker import chunk_documents, print_sample_chunks
from embedder import build_vector_store


def main():
    print("=" * 60)
    print("  The Unofficial Guide — Building Pipeline")
    print("=" * 60)

    # Step 1: Load and clean documents
    print("\n📥 Step 1: Loading documents...")
    documents = load_documents()

    # Step 2: Chunk documents
    print("\n✂️  Step 2: Chunking documents...")
    chunks = chunk_documents(documents)

    # Step 3: Print sample chunks for validation
    print_sample_chunks(chunks, n=5)

    # Step 4: Embed and store in ChromaDB
    print("\n🧠 Step 3: Embedding and storing in ChromaDB...")
    collection = build_vector_store(chunks, force_rebuild=True)

    print("\n" + "=" * 60)
    print(f"  ✅ Pipeline complete!")
    print(f"  📄 Documents: {len(documents)}")
    print(f"  ✂️  Chunks: {len(chunks)}")
    print(f"  🗃️  Stored in ChromaDB: {collection.count()}")
    print(f"\n  Run 'python app.py' to launch the query interface.")
    print("=" * 60)


if __name__ == "__main__":
    main()
