"""Shared configuration and constants."""

import os

MONGODB_URI = os.environ.get("MONGODB_URI", "")
VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

DB_NAME = os.environ.get("DB_NAME", "atlas_sizing_kb")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "docs_chunks")
VECTOR_INDEX_NAME = os.environ.get("VECTOR_INDEX_NAME", "docs_vector_index")

EMBEDDING_MODEL = "voyage-3-large"
EMBEDDING_DIMENSIONS = 1024

LLM_MODEL = "claude-sonnet-4-20250514"
LLM_MAX_TOKENS = 16384

# Chunking parameters
CHUNK_SIZE = 400       # approx words per chunk
CHUNK_OVERLAP = 50     # word overlap between chunks

# Source documents to ingest
SOURCE_DOCS = [
    {
        "url": "https://www.mongodb.com/docs/atlas/sizing-tier-selection/",
        "title": "Atlas Cluster Sizing and Tier Selection",
    },
    {
        "url": "https://www.mongodb.com/docs/atlas/cluster-autoscaling/",
        "title": "Configure Auto-Scaling",
    },
    {
        "url": "https://www.mongodb.com/docs/atlas/customize-storage/",
        "title": "Customize Cluster Storage",
    },
    {
        "url": "https://www.mongodb.com/docs/atlas/cluster-additional-settings/",
        "title": "Configure Additional Settings",
    },
    {
        "url": "https://www.mongodb.com/docs/atlas/cluster-sharding/",
        "title": "Manage Cluster Sharding",
    },
    {
        "url": "https://www.mongodb.com/docs/atlas/manage-clusters/",
        "title": "Manage Clusters",
    },
    {
        "url": "https://www.mongodb.com/docs/atlas/tutorial/major-version-change/",
        "title": "Upgrade Major MongoDB Version",
    },
]
