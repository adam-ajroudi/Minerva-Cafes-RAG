"""
Chunking Module
Splits documents into semantic chunks using a paragraph-aware strategy.
Respects natural review boundaries (double-newline separated blocks),
then character-splits oversized blocks with overlap.
"""

import re


# Chunking parameters (from planning.md)
MAX_CHUNK_SIZE = 600       # characters
MIN_CHUNK_SIZE = 50        # minimum viable chunk — skip anything smaller
OVERLAP = 80               # character overlap for split chunks


def split_into_blocks(text: str) -> list[str]:
    """
    Split text on double-newline boundaries (--- dividers and blank lines).
    This respects the natural structure of our review documents where
    each venue review is separated by blank lines or --- dividers.
    """
    # Split on divider lines (---) and double newlines
    blocks = re.split(r"\n-{3,}\n|\n{2,}", text)

    # Clean each block and filter out empties / pure formatting
    cleaned = []
    for block in blocks:
        block = block.strip()
        # Skip empty blocks, pure dividers, and header-only blocks
        if not block:
            continue
        if re.match(r"^-+$", block):
            continue
        if len(block) < MIN_CHUNK_SIZE:
            continue
        cleaned.append(block)

    return cleaned


def split_oversized_block(block: str, max_size: int = MAX_CHUNK_SIZE,
                          overlap: int = OVERLAP) -> list[str]:
    """
    Split a block that exceeds max_size into smaller chunks with overlap.
    Tries to split on sentence boundaries (. ! ?) when possible.
    """
    if len(block) <= max_size:
        return [block]

    chunks = []
    start = 0

    while start < len(block):
        end = start + max_size

        if end >= len(block):
            # Last chunk — take everything remaining
            chunk = block[start:].strip()
            if chunk and len(chunk) >= MIN_CHUNK_SIZE:
                chunks.append(chunk)
            break

        # Try to find a sentence boundary to split on
        # Look backwards from the end position for . ! ? followed by a space
        search_region = block[start:end]
        last_sentence_end = -1

        for match in re.finditer(r'[.!?]["\')\]]?\s', search_region):
            last_sentence_end = match.end()

        if last_sentence_end > max_size * 0.3:
            # Found a good sentence boundary — split there
            end = start + last_sentence_end
        else:
            # No good sentence boundary — try splitting on newline
            last_newline = search_region.rfind("\n")
            if last_newline > max_size * 0.3:
                end = start + last_newline

        chunk = block[start:end].strip()
        if chunk and len(chunk) >= MIN_CHUNK_SIZE:
            chunks.append(chunk)

        # Move start forward, accounting for overlap
        start = end - overlap

    return chunks


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk all documents into retrieval-ready pieces.

    Args:
        documents: List of dicts from ingest.load_documents()
                  Each has 'text', 'source', 'city'

    Returns:
        List of chunk dicts with keys:
        'text', 'source', 'city', 'chunk_index'
    """
    all_chunks = []

    for doc in documents:
        doc_chunks = []
        blocks = split_into_blocks(doc["text"])

        for block in blocks:
            if len(block) <= MAX_CHUNK_SIZE:
                doc_chunks.append(block)
            else:
                sub_chunks = split_oversized_block(block)
                doc_chunks.extend(sub_chunks)

        # Create chunk dicts with metadata
        for i, chunk_text in enumerate(doc_chunks):
            all_chunks.append({
                "text": chunk_text,
                "source": doc["source"],
                "city": doc["city"],
                "chunk_index": i,
            })

    print(f"\n✅ Chunked {len(documents)} documents into {len(all_chunks)} chunks")
    print(f"   Average chunk size: {sum(len(c['text']) for c in all_chunks) // max(len(all_chunks), 1)} chars")

    # Distribution by source
    from collections import Counter
    source_counts = Counter(c["source"] for c in all_chunks)
    for source, count in sorted(source_counts.items()):
        print(f"   • {source}: {count} chunks")

    return all_chunks


def print_sample_chunks(chunks: list[dict], n: int = 5):
    """Print n sample chunks for validation."""
    import random
    samples = random.sample(chunks, min(n, len(chunks)))

    print(f"\n📋 {n} Sample Chunks:")
    print("=" * 60)
    for i, chunk in enumerate(samples, 1):
        print(f"\n--- Chunk {i} (from {chunk['source']}, {chunk['city']}) ---")
        print(f"Length: {len(chunk['text'])} chars")
        print(chunk["text"][:400])
        if len(chunk["text"]) > 400:
            print("... [truncated]")
        print()


if __name__ == "__main__":
    from ingest import load_documents

    documents = load_documents()
    chunks = chunk_documents(documents)
    print_sample_chunks(chunks, n=5)
