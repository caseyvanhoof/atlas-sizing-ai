"""
Knowledge Base: vector search retrieval for RAG context.

Embeds a query with Voyage AI and searches the MongoDB Atlas
vector index to find the most relevant documentation chunks.
"""

import logging
from typing import Optional

from pymongo import MongoClient
import voyageai

import config

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Retrieves relevant documentation context via Atlas Vector Search."""

    def __init__(self, mongo_uri: Optional[str] = None,
                 voyage_api_key: Optional[str] = None):
        self.mongo = MongoClient(mongo_uri or config.MONGODB_URI)
        self.db = self.mongo[config.DB_NAME]
        self.coll = self.db[config.COLLECTION_NAME]
        self.voyage = voyageai.Client(api_key=voyage_api_key or config.VOYAGE_API_KEY)

    def search(self, query: str, num_results: int = 8,
               num_candidates: int = 80) -> list:
        """Search the knowledge base for relevant documentation chunks.

        Args:
            query: the sizing-related question or topic to search for
            num_results: number of chunks to return
            num_candidates: number of candidates for HNSW (higher = more accurate)

        Returns:
            List of dicts with keys: title, source, text, score, chunk_index
        """
        # Embed the query
        logger.info(f"Embedding query: {query[:80]}...")
        result = self.voyage.embed(
            [query],
            model=config.EMBEDDING_MODEL,
            input_type="query",
        )
        query_vector = result.embeddings[0]

        # Atlas Vector Search
        pipeline = [
            {
                "$vectorSearch": {
                    "index": config.VECTOR_INDEX_NAME,
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": num_candidates,
                    "limit": num_results,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "source": 1,
                    "text": 1,
                    "chunk_index": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        results = list(self.coll.aggregate(pipeline))
        logger.info(f"Retrieved {len(results)} chunks (top score: "
                    f"{results[0]['score']:.3f})" if results else "No results")
        return results

    def get_context(self, topics: list, chunks_per_topic: int = 4) -> str:
        """Build a RAG context string from multiple search topics.

        Args:
            topics: list of query strings to search for
            chunks_per_topic: how many chunks to retrieve per topic

        Returns:
            Formatted string with all retrieved context, deduplicated
        """
        seen_texts = set()
        all_chunks = []

        for topic in topics:
            results = self.search(topic, num_results=chunks_per_topic)
            for r in results:
                # Deduplicate by text content
                text_key = r["text"][:100]
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    all_chunks.append(r)

        if not all_chunks:
            return "(No relevant documentation found in knowledge base)"

        # Format as context string
        sections = []
        for i, chunk in enumerate(all_chunks):
            sections.append(
                f"--- Context #{i+1} (source: {chunk['title']}) ---\n"
                f"{chunk['text']}\n"
                f"[Source: {chunk['source']}]"
            )

        return "\n\n".join(sections)
