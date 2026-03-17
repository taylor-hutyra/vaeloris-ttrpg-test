"""Custom embedding provider that shells out to an external command."""

from __future__ import annotations

import json
import subprocess

from .base import EmbeddingProvider


class CustomEmbeddingProvider(EmbeddingProvider):
    """BYO embedding provider.

    Runs a command via subprocess. Passes text as JSON array via stdin,
    reads a JSON array of arrays of floats from stdout.
    """

    def __init__(self, command: str, dimensions: int):
        self._command = command
        self._dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts by piping them through the external command."""
        input_data = json.dumps(texts)
        try:
            result = subprocess.run(
                self._command,
                input=input_data,
                capture_output=True,
                text=True,
                shell=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Custom embedding command timed out: {self._command}")

        if result.returncode != 0:
            raise RuntimeError(
                f"Custom embedding command failed (exit {result.returncode}): "
                f"{result.stderr.strip()}"
            )

        try:
            embeddings = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(
                f"Custom embedding command returned invalid JSON: {result.stdout[:200]}"
            )

        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise RuntimeError(
                f"Expected {len(texts)} embeddings, got {len(embeddings) if isinstance(embeddings, list) else 'non-list'}"
            )

        return embeddings

    @property
    def dimensions(self) -> int:
        return self._dimensions
