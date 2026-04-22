#!/usr/bin/env python3
"""
Document Ingestion Pipeline

Fetches MongoDB Atlas documentation pages, strips navigation/chrome,
chunks the content by ~400 words with overlap, generates embeddings
via Voyage AI, and stores everything in MongoDB Atlas for RAG retrieval.

Usage:
  python ingest_docs.py [--drop]

  --drop   Drop the existing collection before ingesting (clean start)

Requires:
  MONGODB_URI, VOYAGE_API_KEY environment variables
"""

import argparse
import re
import sys
import time

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import config

try:
    import voyageai
except ImportError:
    print("Error: voyageai is required. Install with: pip install voyageai")
    sys.exit(1)


# ── HTML Cleaning ────────────────────────────────────────────────────────────

def fetch_and_clean(url: str) -> str:
    """Fetch a MongoDB docs page and extract only the article content."""
    print(f"  Fetching {url}...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # MongoDB docs use <main> or a specific article section
    # Try several selectors to find the content area
    content = None
    for selector in ["main article", "main", "[role='main']",
                     ".content", "#main-column", "article"]:
        content = soup.select_one(selector)
        if content:
            break

    if not content:
        content = soup.body or soup

    # Remove nav, sidebar, footer, breadcrumbs, TOC
    for tag in content.select(
        "nav, aside, footer, .sidebar, .breadcrumbs, .toc, "
        ".on-this-page, .header-actions, .feedback, script, style, "
        ".edit-link, .rate-this-page, .share-feedback"
    ):
        tag.decompose()

    # Extract text
    text = content.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Remove common navigation remnants
    lines = text.split("\n")
    cleaned = []
    skip_patterns = [
        "Docs Home", "Get Started", "Development", "Management",
        "Client Libraries", "Tools", "AI Models", "Atlas Architecture",
        "Sign In", "Get Started", "View All Products",
        "Build with MongoDB Atlas", "Test Enterprise Advanced",
        "Try Community Edition", "Register now",
    ]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.startswith(p) for p in skip_patterns):
            continue
        if len(stripped) < 3:
            continue
        cleaned.append(stripped)

    return "\n".join(cleaned)


# ── Chunking ─────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = config.CHUNK_SIZE,
               overlap: int = config.CHUNK_OVERLAP) -> list:
    """Split text into overlapping word-based chunks.

    Tries to split at paragraph boundaries when possible to keep
    related content together.
    """
    # Split into paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_words = []
    current_para_start = 0

    for para in paragraphs:
        words = para.split()

        # If adding this paragraph would exceed chunk size, finalize current chunk
        if current_words and len(current_words) + len(words) > chunk_size:
            chunk_text_str = " ".join(current_words)
            chunks.append(chunk_text_str)
            # Start next chunk with overlap from end of current
            if overlap > 0 and len(current_words) > overlap:
                current_words = current_words[-overlap:]
            else:
                current_words = []

        current_words.extend(words)

        # If current chunk is very large (paragraph was huge), split it
        while len(current_words) > chunk_size:
            chunk_text_str = " ".join(current_words[:chunk_size])
            chunks.append(chunk_text_str)
            current_words = current_words[chunk_size - overlap:]

    # Don't forget the last chunk
    if current_words:
        chunk_text_str = " ".join(current_words)
        if len(chunk_text_str.split()) > 20:  # skip tiny trailing chunks
            chunks.append(chunk_text_str)

    return chunks


# ── Embedding ────────────────────────────────────────────────────────────────

def embed_chunks(chunks: list, voyage_client) -> list:
    """Generate embeddings for a list of text chunks using Voyage AI.

    Batches in groups of 50 to respect API limits.
    """
    all_embeddings = []
    batch_size = 50

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"  Embedding batch {i // batch_size + 1} "
              f"({len(batch)} chunks)...")
        result = voyage_client.embed(
            batch,
            model=config.EMBEDDING_MODEL,
            input_type="document",
        )
        all_embeddings.extend(result.embeddings)
        if i + batch_size < len(chunks):
            time.sleep(0.5)  # rate limit courtesy

    return all_embeddings


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Ingest MongoDB Atlas docs into the sizing knowledge base."
    )
    parser.add_argument(
        "--drop", action="store_true",
        help="Drop the existing collection before ingesting"
    )
    args = parser.parse_args()

    # Validate env
    if not config.MONGODB_URI:
        print("Error: MONGODB_URI environment variable is required.")
        sys.exit(1)
    if not config.VOYAGE_API_KEY:
        print("Error: VOYAGE_API_KEY environment variable is required.")
        sys.exit(1)

    # Connect
    print("Connecting to MongoDB Atlas...")
    mongo = MongoClient(config.MONGODB_URI)
    db = mongo[config.DB_NAME]
    coll = db[config.COLLECTION_NAME]

    if args.drop:
        print(f"Dropping collection {config.DB_NAME}.{config.COLLECTION_NAME}...")
        coll.drop()

    print("Initializing Voyage AI client...")
    voyage_client = voyageai.Client(api_key=config.VOYAGE_API_KEY)

    # Process each source doc
    all_docs = []
    for source in config.SOURCE_DOCS:
        url = source["url"]
        title = source["title"]
        print(f"\nProcessing: {title}")

        try:
            text = fetch_and_clean(url)
        except Exception as e:
            print(f"  ERROR fetching {url}: {e}")
            continue

        word_count = len(text.split())
        print(f"  Extracted {word_count} words")

        # Chunk
        chunks = chunk_text(text)
        print(f"  Created {len(chunks)} chunks")

        # Embed
        embeddings = embed_chunks(chunks, voyage_client)

        # Build documents
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            all_docs.append({
                "title": title,
                "source": url,
                "chunk_index": i,
                "text": chunk,
                "word_count": len(chunk.split()),
                "embedding": embedding,
            })

    if not all_docs:
        print("No documents to insert.")
        sys.exit(1)

    # Insert into MongoDB
    print(f"\nInserting {len(all_docs)} chunks into MongoDB Atlas...")
    try:
        result = coll.insert_many(all_docs)
        print(f"Inserted {len(result.inserted_ids)} documents.")
    except PyMongoError as e:
        print(f"Error inserting documents: {e}")
        sys.exit(1)

    # Remind about vector index
    print(f"""
=====================================================
Ingestion complete!

Collection: {config.DB_NAME}.{config.COLLECTION_NAME}
Documents:  {len(all_docs)}

IMPORTANT: You must create a Vector Search index on
this collection in the Atlas UI or via API:

  Index Name: {config.VECTOR_INDEX_NAME}
  Path:       embedding
  Dimensions: {config.EMBEDDING_DIMENSIONS}
  Similarity: cosine

Example index definition:
{{
  "fields": [
    {{
      "type": "vector",
      "path": "embedding",
      "numDimensions": {config.EMBEDDING_DIMENSIONS},
      "similarity": "cosine"
    }}
  ]
}}
=====================================================
""")


if __name__ == "__main__":
    main()
