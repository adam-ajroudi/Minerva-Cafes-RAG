"""
Document Ingestion Module
Loads .txt files from the documents/ directory, cleans them, and returns
a list of document dicts with 'text', 'source', and 'city' metadata.
"""

import os
import re


# Map filenames to cities for metadata
CITY_MAP = {
    "sf_": "San Francisco",
    "berlin_": "Berlin",
    "seoul_": "Seoul",
    "taipei_": "Taipei",
    "hyderabad_": "Hyderabad",
    "buenos_aires_": "Buenos Aires",
    "cross_city": "All Cities",
    "new_student": "All Cities",
}


def detect_city(filename: str) -> str:
    """Detect city from filename prefix."""
    for prefix, city in CITY_MAP.items():
        if filename.startswith(prefix):
            return city
    return "Unknown"


def clean_text(text: str) -> str:
    """
    Clean raw document text:
    - Normalize unicode whitespace
    - Remove excessive blank lines (keep max 2 newlines between sections)
    - Strip leading/trailing whitespace from each line
    - Remove any leftover HTML-like artifacts
    """
    # Normalize unicode spaces
    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")

    # Remove any stray HTML tags (shouldn't be in .txt but just in case)
    text = re.sub(r"<[^>]+>", "", text)

    # Remove HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&#39;", "'")
    text = text.replace("&quot;", '"')

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Collapse 3+ consecutive newlines into 2 (preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace from the whole document
    text = text.strip()

    return text


def load_documents(documents_dir: str = "documents") -> list[dict]:
    """
    Load all .txt files from the documents directory.

    Returns:
        List of dicts with keys: 'text', 'source', 'city'
    """
    docs = []

    if not os.path.isdir(documents_dir):
        raise FileNotFoundError(f"Documents directory not found: {documents_dir}")

    for filename in sorted(os.listdir(documents_dir)):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(documents_dir, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()

        cleaned = clean_text(raw_text)

        if not cleaned:
            print(f"  ⚠ Skipping empty document: {filename}")
            continue

        city = detect_city(filename)

        docs.append({
            "text": cleaned,
            "source": filename,
            "city": city,
        })

    print(f"✅ Loaded {len(docs)} documents from {documents_dir}/")
    for doc in docs:
        print(f"   • {doc['source']} ({doc['city']}, {len(doc['text'])} chars)")

    return docs


if __name__ == "__main__":
    documents = load_documents()
    print(f"\nTotal documents: {len(documents)}")
    print(f"Total characters: {sum(len(d['text']) for d in documents):,}")

    # Print first 500 chars of first document as a sanity check
    if documents:
        print(f"\n--- Preview of {documents[0]['source']} ---")
        print(documents[0]["text"][:500])
