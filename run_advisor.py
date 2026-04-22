#!/usr/bin/env python3
"""
Atlas Sizing Advisor — CLI Entrypoint

Reads a markdown file describing the customer's MongoDB schema and
workload, retrieves relevant Atlas documentation via RAG, and generates
a detailed tier selection and sizing report using Claude.

Usage:
  python run_advisor.py --input workload.md [--output sizing_report.md]

Environment variables required:
  MONGODB_URI        - Atlas connection string (for the KB collection)
  VOYAGE_API_KEY     - Voyage AI API key (for embeddings)
  ANTHROPIC_API_KEY  - Anthropic API key (for Claude)
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import config
from knowledge_base import KnowledgeBase
from sizing_advisor import build_search_topics, generate_sizing_report


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an Atlas cluster sizing recommendation from a "
                    "schema/workload description.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_advisor.py --input workload.md
  python run_advisor.py --input workload.md --output my_report.md
  python run_advisor.py --input workload.md --log-level DEBUG
        """
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to the markdown file describing the schema and workload"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output file path for the sizing report (default: <input>-sizing-report.md)"
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--ai-model", default=None,
        help=f"Claude model override (default: {config.LLM_MODEL})"
    )
    parser.add_argument(
        "--kb-chunks", type=int, default=4,
        help="Number of KB chunks to retrieve per search topic (default: 4)"
    )
    return parser.parse_args()


def validate_env():
    """Check that all required environment variables are set."""
    errors = []
    if not config.MONGODB_URI:
        errors.append("MONGODB_URI is not set")
    if not config.VOYAGE_API_KEY:
        errors.append("VOYAGE_API_KEY is not set")
    if not config.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is not set")
    if errors:
        print("Missing required environment variables:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)


def main():
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("run_advisor")

    validate_env()

    # Read input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    schema_text = input_path.read_text(encoding="utf-8")
    if not schema_text.strip():
        print(f"Error: Input file is empty: {input_path}", file=sys.stderr)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Atlas Sizing Advisor")
    logger.info("=" * 60)
    logger.info(f"Input: {input_path} ({len(schema_text)} chars)")

    start_time = time.time()

    # Step 1: Build search topics from the schema description
    logger.info("Analyzing schema for relevant topics...")
    topics = build_search_topics(schema_text)
    logger.info(f"Search topics: {len(topics)}")

    # Step 2: Retrieve RAG context from knowledge base
    logger.info("Retrieving relevant documentation from knowledge base...")
    kb = KnowledgeBase()
    kb_context = kb.get_context(topics, chunks_per_topic=args.kb_chunks)
    logger.info(f"KB context retrieved: {len(kb_context)} chars")

    # Step 3: Generate sizing report
    logger.info("Generating sizing report with Claude...")
    report = generate_sizing_report(
        schema_text=schema_text,
        kb_context=kb_context,
        model=args.ai_model,
    )

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        stem = input_path.stem
        output_path = input_path.parent / f"{stem}-sizing-report.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    elapsed = time.time() - start_time

    logger.info("=" * 60)
    logger.info(f"Report generated: {output_path}")
    logger.info(f"Total time: {elapsed:.1f}s")
    logger.info("=" * 60)

    print()
    print(f"  Sizing report saved to: {output_path}")
    print(f"  Time: {elapsed:.1f}s")
    print()


if __name__ == "__main__":
    main()
