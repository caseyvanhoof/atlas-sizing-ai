# Atlas Sizing AI

A RAG-powered MongoDB Atlas cluster sizing advisor. Takes a customer's schema and workload description as input, retrieves relevant Atlas documentation context via vector search, and generates a detailed sizing and pricing proposal using Claude.

## How It Works

```
                                    ┌─────────────────────┐
                                    │  MongoDB Atlas Docs  │
                                    │  (7 pages ingested)  │
                                    └────────┬────────────┘
                                             │ chunked + embedded
                                             ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Customer's   │    │  Voyage AI   │    │  MongoDB     │    │  Claude      │
│  Workload     │───▶│  Embedding   │───▶│  Atlas       │───▶│  (Sizing     │
│  Description  │    │  (query)     │    │  Vector      │    │   Report)    │
│  (.md file)   │    │              │    │  Search      │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                   │
                                                                   ▼
                                                          ┌──────────────┐
                                                          │  Sizing      │
                                                          │  Report      │
                                                          │  (.md file)  │
                                                          └──────────────┘
```

1. **Ingest** — `ingest_docs.py` fetches 7 MongoDB Atlas documentation pages, chunks them (~400 words each with overlap), generates embeddings via Voyage AI, and stores them in a MongoDB Atlas collection with a vector search index.

2. **Query** — When you run the advisor, it analyzes your workload description to extract relevant topics, then performs vector search against the knowledge base to retrieve the most relevant documentation chunks.

3. **Generate** — The retrieved context, your workload description, and a detailed system prompt (with solution guardrails and output template) are sent to Claude, which produces a formal sizing proposal.

## Report Output

The generated report follows a professional solutions architecture format:

| Section | What It Covers |
|---|---|
| **Executive Summary** | Primary recommendation, sizing driver, key benefit |
| **Baseline Assumptions** | Input data recap, mandatory guardrails applied |
| **Storage & Performance Analysis** | Working set math, compression, WiredTiger cache, 4TB sharding check, IOPS, connections |
| **3 Configuration Options** | Cost-optimized, Balanced (recommended), High-performance — each with full specs and justification |
| **Pricing Summary** | Comparison table with monthly/annual estimates |
| **Auto-Scaling Config** | Min/max tier, storage scaling settings |
| **Caveats & Risks** | What could change the recommendation |
| **Testing Plan** | Load testing approach, metrics to monitor, specific thresholds |
| **Next Steps** | Final recommendation, deployment sequence, follow-ups |

## Solution Guardrails

Every proposal automatically enforces these rules:

- 5-node electable replica set per shard, 3 regions (2-2-1)
- MongoDB 8.0, BYOK encryption, multi-region cloud backups
- 4TB per-node storage limit — sharding required above this
- 70-80% disk utilization threshold — must maintain 20-30% headroom for chunk migration
- Right-sized disk per shard with storage auto-scaling (don't overprovision disk when adding shards for headroom)
- Workload-specific sizing: identifies whether the bottleneck is Storage, IOPS, or RAM
- All math shown explicitly

## Setup

### Prerequisites

- Python 3.10+
- A MongoDB Atlas cluster (for storing the knowledge base)
- [Voyage AI](https://www.voyageai.com/) API key (for embeddings)
- [Anthropic](https://www.anthropic.com/) API key (for Claude)

### Install

```bash
cd atlas-sizing-ai
pip install -r requirements.txt
```

### Environment Variables

```bash
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net"
export VOYAGE_API_KEY="your-voyage-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Or copy `.env.example` to `.env` and fill in the values.

### Create the Vector Search Index

After running the ingestion script, create a vector search index on your Atlas collection:

- **Index Name:** `docs_vector_index`
- **Collection:** `atlas_sizing_kb.docs_chunks`

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
```

## Usage

### Step 1: Ingest Documentation (one-time)

```bash
python ingest_docs.py --drop
```

This fetches, chunks, embeds, and stores all 7 Atlas documentation pages. Takes about 30 seconds. Only needs to be run once (or again if docs are updated).

### Step 2: Create Your Workload Description

Create a markdown file describing the customer's workload. See `sample_workload.md` for a complete example. Key data points to include:

- Cloud provider and region
- Collections with document counts, average document sizes, and field layouts
- Index definitions and estimated sizes
- Query patterns with operations/sec (reads, writes, aggregations)
- Peak vs steady-state traffic
- Connection requirements
- Availability/SLA requirements
- Growth projections

### Step 3: Generate the Sizing Report

```bash
python run_advisor.py --input my_workload.md
```

Options:

```
--input, -i       Path to the workload markdown file (required)
--output, -o      Output file path (default: <input>-sizing-report.md)
--ai-model        Claude model override (default: claude-sonnet-4-20250514)
--kb-chunks       KB chunks to retrieve per topic (default: 4)
--log-level       DEBUG, INFO, WARNING, ERROR (default: INFO)
```

Example with custom output:

```bash
python run_advisor.py \
  --input customer_acme.md \
  --output proposals/acme-sizing-v1.md
```

## Project Structure

```
atlas-sizing-ai/
├── config.py           # Shared configuration (env vars, models, defaults)
├── ingest_docs.py      # Document ingestion pipeline (fetch → chunk → embed → store)
├── knowledge_base.py   # Vector search retrieval for RAG context
├── sizing_advisor.py   # System prompt (guardrails + template) and Claude integration
├── run_advisor.py      # CLI entrypoint
├── sample_workload.md  # Example input file
├── requirements.txt    # Python dependencies
└── .env.example        # Environment variable template
```

## Customization

### Guardrails

The solution guardrails are defined in `sizing_advisor.py` in the `GUARDRAILS` constant. Modify these to match your organization's standards (e.g., different node counts, region requirements, or storage thresholds).

### Output Template

The report format is defined in the `OUTPUT_TEMPLATE` constant in `sizing_advisor.py`. You can adjust sections, add new ones, or change the structure to match your proposal format.

### Knowledge Base Sources

To add more documentation pages to the knowledge base, add entries to `SOURCE_DOCS` in `config.py` and re-run `python ingest_docs.py --drop`.
