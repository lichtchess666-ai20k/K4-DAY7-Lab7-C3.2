"""Text chunking strategies and vector similarity helpers."""

from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """Split text into fixed-size sliding windows."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunks.append(text[start : start + self.chunk_size])
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """Group text by natural sentence boundaries."""

    SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])(?:[ \t]+|\r?\n+)")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []

        sentences = [
            " ".join(sentence.split())
            for sentence in self.SENTENCE_BOUNDARY.split(normalized)
            if sentence.strip()
        ]
        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk])
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """Recursively split text using separators from largest to smallest."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        self.separators = list(self.DEFAULT_SEPARATORS if separators is None else separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return self._hard_split(current_text)

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]
        if separator == "":
            return self._hard_split(current_text)
        if separator not in current_text:
            return self._split(current_text, next_separators)

        raw_parts = current_text.split(separator)
        pieces = [raw_parts[0]]
        pieces.extend(f"{separator}{part}" for part in raw_parts[1:])

        chunks: list[str] = []
        current_chunk = ""
        for piece in pieces:
            if not piece:
                continue

            if len(current_chunk) + len(piece) <= self.chunk_size:
                current_chunk += piece
                continue

            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            if len(piece) <= self.chunk_size:
                current_chunk = piece
            else:
                chunks.extend(self._split(piece, next_separators))

        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _hard_split(self, text: str) -> list[str]:
        return [
            text[start : start + self.chunk_size]
            for start in range(0, len(text), self.chunk_size)
        ]


def _dot(a: list[float], b: list[float]) -> float:
    """Return the dot product of two equally sized vectors."""

    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity and safely handle zero vectors."""

    if len(vec_a) != len(vec_b):
        raise ValueError("vectors must have the same dimension")

    magnitude_a = math.sqrt(sum(value * value for value in vec_a))
    magnitude_b = math.sqrt(sum(value * value for value in vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run and summarize all three built-in chunking strategies."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        overlap = min(50, max(0, chunk_size // 5))
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=overlap),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison: dict[str, dict] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            comparison[name] = {
                "count": count,
                "avg_length": sum(len(chunk) for chunk in chunks) / count if count else 0.0,
                "chunks": chunks,
            }
        return comparison
