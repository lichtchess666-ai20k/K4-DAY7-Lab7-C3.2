"""Tri Tue's paragraph-window chunking strategy for policy corpora."""

from __future__ import annotations

import re


class ContextualParagraphWindowChunker:
    """Pack adjacent paragraphs and retain a small paragraph context window.

    Blank lines define paragraph boundaries. A paragraph that is larger than
    the character budget is split into overlapping word-boundary windows so a
    single unusually long paragraph cannot create an unbounded chunk.
    """

    def __init__(
        self,
        chunk_size: int = 900,
        overlap_paragraphs: int = 1,
        word_overlap: int = 20,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if overlap_paragraphs < 0:
            raise ValueError("overlap_paragraphs must be non-negative")
        if word_overlap < 0:
            raise ValueError("word_overlap must be non-negative")

        self.chunk_size = chunk_size
        self.overlap_paragraphs = overlap_paragraphs
        self.word_overlap = word_overlap

    def chunk(self, text: str) -> list[str]:
        """Return chunks built from adjacent paragraph blocks."""
        if not text or not text.strip():
            return []

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [
            block.strip()
            for block in re.split(r"\n\s*\n+", normalized)
            if block.strip()
        ]

        chunks: list[str] = []
        current: list[str] = []

        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                self._emit(current, chunks)
                current = []
                chunks.extend(self._split_oversized_paragraph(paragraph))
                continue

            if not current:
                current = [paragraph]
                continue

            candidate = "\n\n".join([*current, paragraph])
            if len(candidate) <= self.chunk_size:
                current.append(paragraph)
                continue

            self._emit(current, chunks)
            overlap = current[-self.overlap_paragraphs :] if self.overlap_paragraphs else []
            while overlap and len("\n\n".join([*overlap, paragraph])) > self.chunk_size:
                overlap.pop(0)
            current = [*overlap, paragraph]

        self._emit(current, chunks)
        return chunks

    @staticmethod
    def _emit(paragraphs: list[str], chunks: list[str]) -> None:
        if not paragraphs:
            return
        content = "\n\n".join(paragraphs)
        chunks.append(content)

    def _split_oversized_paragraph(self, paragraph: str) -> list[str]:
        words = paragraph.split()
        if not words:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = start
            current_length = 0

            while end < len(words):
                separator_length = 1 if end > start else 0
                candidate_length = current_length + separator_length + len(words[end])
                if candidate_length > self.chunk_size:
                    break
                current_length = candidate_length
                end += 1

            if end == start:
                # Preserve an indivisible token even when it exceeds the budget.
                end = start + 1

            chunks.append(" ".join(words[start:end]))
            if end >= len(words):
                break

            start = max(start + 1, end - self.word_overlap)

        return chunks
