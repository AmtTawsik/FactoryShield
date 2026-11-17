"""Loads the documents listed in a manifest into the knowledge base used by the chat assistant.

Usage: uv run python -m scripts.ingest_knowledge [--manifest knowledge/manifest.toml]

Each file is read (PDF, TXT or Markdown), split into chunks, embedded with the embedding service and
stored with its metadata. Safe to run again: documents are matched by their manifest key, unchanged
documents are skipped and changed ones are re-embedded and replaced.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.integrations.embeddings.client import EmbeddingClient, get_embedding_client
from app.integrations.embeddings.errors import EmbeddingUnavailableError
from app.modules.auth.service import FactoryScope
from app.modules.factories.repository import FactoryRepository
from app.modules.factories.service import FactoryService
from app.modules.knowledge.ingestion import IngestionError, ingest_prepared, load_manifest, prepare
from app.modules.knowledge.repository import KnowledgeRepository
from app.modules.knowledge.service import KnowledgeService

DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "knowledge" / "manifest.toml"
# The script runs with operator rights: it may load general documents and documents for any factory.
ALL_FACTORIES = FactoryScope(factory_ids=None)


async def ingest(manifest: Path, embeddings: EmbeddingClient) -> int:
    """Returns the process exit code: 0 when every document was stored, 1 otherwise."""
    try:
        documents = prepare(load_manifest(manifest))
    except IngestionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for document in documents:
        if document.unreadable_characters:
            print(
                f"warning: {document.entry.path.name}: {document.unreadable_characters} characters could not be "
                "read from the PDF and were replaced with spaces"
            )

    async with SessionLocal() as session:
        service = KnowledgeService(
            session,
            KnowledgeRepository(session),
            FactoryService(session, FactoryRepository(session)),
            embeddings,
            get_settings().rag_min_score,
        )
        try:
            results = await ingest_prepared(documents, service, ALL_FACTORIES)
        except EmbeddingUnavailableError:
            print(
                f"error: the embedding service at {get_settings().embedding_base_url} is not reachable. "
                "Start it with `docker compose up -d embeddings` and run the script again.",
                file=sys.stderr,
            )
            return 1

    for result in results:
        print(f"{result.status.value:<9} {result.document.source_key} ({result.chunk_count} chunks)")
    counts = {status: sum(r.status == status for r in results) for status in {r.status for r in results}}
    print(", ".join(f"{count} {status.value}" for status, count in sorted(counts.items())))
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description="Load safety and compliance documents into the knowledge base.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="path to the manifest TOML file")
    args = parser.parse_args()
    # pypdf logs font details it cannot parse fully; the extracted text is still checked and reported above.
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    try:
        return await ingest(args.manifest, get_embedding_client())
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
