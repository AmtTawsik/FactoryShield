import logging
from functools import lru_cache

import openai
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.integrations.embeddings.errors import EmbeddingUnavailableError

logger = logging.getLogger(__name__)

# Size of the vectors returned by intfloat/multilingual-e5-small. The database column uses the same value.
EMBEDDING_DIMENSIONS = 384


class EmbeddingClient:
    """Turns text into vectors through an OpenAI-compatible /v1/embeddings service (TEI by default)."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float,
        batch_size: int,
        query_prefix: str = "",
        passage_prefix: str = "",
        dimensions: int = EMBEDDING_DIMENSIONS,
        http_client=None,
    ):
        self.model = model
        self.batch_size = batch_size
        self.query_prefix = query_prefix
        self.passage_prefix = passage_prefix
        self.dimensions = dimensions
        self._client = AsyncOpenAI(
            base_url=base_url, api_key=api_key, timeout=timeout, max_retries=1, http_client=http_client
        )

    async def embed_query(self, text: str) -> list[float]:
        [vector] = await self._embed([self.query_prefix + text])
        return vector

    async def embed_passages(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            vectors += await self._embed([self.passage_prefix + text for text in batch])
        return vectors

    async def _embed(self, inputs: list[str]) -> list[list[float]]:
        try:
            response = await self._client.embeddings.create(model=self.model, input=inputs, encoding_format="float")
        except openai.OpenAIError as exc:
            logger.error("Embedding service error (model %s): %s", self.model, exc)
            raise EmbeddingUnavailableError() from exc

        vectors = [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
        if len(vectors) != len(inputs) or any(len(vector) != self.dimensions for vector in vectors):
            logger.error(
                "Embedding service returned %d vectors of sizes %s; expected %d of size %d",
                len(vectors),
                sorted({len(vector) for vector in vectors}),
                len(inputs),
                self.dimensions,
            )
            raise EmbeddingUnavailableError()
        return vectors


@lru_cache
def get_embedding_client() -> EmbeddingClient:
    settings = get_settings()
    api_key = settings.embedding_api_key.get_secret_value() if settings.embedding_api_key else ""
    return EmbeddingClient(
        base_url=settings.embedding_base_url,
        # TEI needs no key, but the OpenAI client requires a value.
        api_key=api_key or "not-required",
        model=settings.embedding_model,
        timeout=settings.embedding_timeout_seconds,
        batch_size=settings.embedding_batch_size,
        query_prefix=settings.embedding_query_prefix,
        passage_prefix=settings.embedding_passage_prefix,
    )
