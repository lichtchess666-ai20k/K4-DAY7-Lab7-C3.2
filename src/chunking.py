from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
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
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        
        parts = re.split(r'(\. |! |\? |\.\n)', text)
        sentences: list[str] = []
        for i in range(0, len(parts) - 1, 2):
            sent = (parts[i] + parts[i+1]).strip()
            if sent:
                sentences.append(sent)
        if len(parts) % 2 != 0:
            last = parts[-1].strip()
            if last:
                sentences.append(last)

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_sents = sentences[i : i + self.max_sentences_per_chunk]
            chunk_text = " ".join(chunk_sents).strip()
            if chunk_text:
                chunks.append(chunk_text)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        sep = remaining_separators[0]
        if sep == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        parts = current_text.split(sep)
        
        components = []
        for part in parts:
            if len(part) <= self.chunk_size:
                components.append(part)
            else:
                components.extend(self._split(part, remaining_separators[1:]))

        merged_chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for comp in components:
            if not comp:
                continue
            if current_chunk:
                new_len = current_length + len(sep) + len(comp)
                if new_len <= self.chunk_size:
                    current_chunk.append(comp)
                    current_length = new_len
                else:
                    merged_chunks.append(sep.join(current_chunk))
                    current_chunk = [comp]
                    current_length = len(comp)
            else:
                current_chunk = [comp]
                current_length = len(comp)

        if current_chunk:
            merged_chunks.append(sep.join(current_chunk))

        return merged_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_prod = _dot(vec_a, vec_b)
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot_prod / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        comparison = {}
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=max(0, chunk_size // 10)),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=max(1, chunk_size // 80)),
            "recursive": RecursiveChunker(chunk_size=chunk_size)
        }
        
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = (sum(len(c) for c in chunks) / count) if count > 0 else 0.0
            comparison[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks
            }
        return comparison
