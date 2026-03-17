"""Ollama embedding provider using local HTTP API."""

from __future__ import annotations

import json
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from .base import EmbeddingProvider


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Embedding provider using a local Ollama instance."""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        host: str = "http://localhost:11434",
    ):
        self.model = model
        self.host = host.rstrip("/")
        self._dimensions: Optional[int] = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts via Ollama's /api/embed endpoint."""
        url = f"{self.host}/api/embed"
        payload = json.dumps({
            "model": self.model,
            "input": texts,
        }).encode("utf-8")

        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except URLError as e:
            raise ConnectionError(
                f"Failed to connect to Ollama at {self.host}. "
                f"Ensure Ollama is running: {e}"
            )

        embeddings = data.get("embeddings", [])
        if not embeddings:
            raise ValueError(f"No embeddings returned from Ollama for model {self.model}")

        # Cache dimensions from first result
        if self._dimensions is None and embeddings:
            self._dimensions = len(embeddings[0])

        return embeddings

    @property
    def dimensions(self) -> int:
        if self._dimensions is None:
            # Query with a dummy text to discover dimensions
            result = self.embed(["dimension probe"])
            self._dimensions = len(result[0])
        return self._dimensions
