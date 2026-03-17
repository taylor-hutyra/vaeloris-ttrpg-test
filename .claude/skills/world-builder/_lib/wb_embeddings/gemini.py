"""Gemini embedding provider using the google-genai SDK."""

from __future__ import annotations

import os
from typing import Optional

from .base import EmbeddingProvider


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Embedding provider using Google Gemini's text-embedding-004 model."""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-004"):
        self.model = model
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY env var or pass api_key."
            )

        from google import genai
        self._client = genai.Client(api_key=self._api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts using the Gemini embedding API."""
        result = self._client.models.embed_content(
            model=self.model,
            contents=texts,
        )
        return [list(e.values) for e in result.embeddings]

    @property
    def dimensions(self) -> int:
        return 768
