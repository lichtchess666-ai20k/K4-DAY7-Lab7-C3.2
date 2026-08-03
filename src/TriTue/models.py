"""Data models used by Tri Tue's Lab 7 solution."""

from dataclasses import dataclass, field


@dataclass
class Document:
    """A text document with a stable identifier and optional metadata."""

    id: str
    content: str
    metadata: dict = field(default_factory=dict)
