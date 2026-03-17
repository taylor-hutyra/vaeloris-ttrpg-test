"""OpenAI embedding provider."""

from __future__ import annotations

import os
from typing import Optional

from .base import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Embedding provider using OpenAI's text-embedding-3-large model."""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-large"):
        self.model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key."
            )

        import openai
        self._client = openai.OpenAI(api_key=self._api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts using the OpenAI embeddings API."""
        response = self._client.embeddings.create(
            input=texts,
            model=self.model,
        )
        return [item.embedding for item in response.data]

    @property
    def dimensions(self) -> int:
        return 3072
