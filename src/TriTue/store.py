"""Vector storage with an optional ChromaDB backend and safe memory fallback."""

from __future__ import annotations

import re
import uuid
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """Embed, search, filter, and delete document chunks."""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            client_factory = getattr(chromadb, "EphemeralClient", chromadb.Client)
            client = client_factory()
            self._collection = client.get_or_create_collection(
                name=self._make_chroma_collection_name(collection_name),
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    @staticmethod
    def _make_chroma_collection_name(collection_name: str) -> str:
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "-", collection_name).strip("-_")
        if len(safe_name) < 3:
            safe_name = f"lab-{safe_name or 'store'}"
        return f"{safe_name[:40]}-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _normalize_chroma_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
        normalized: dict[str, str | int | float | bool] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                normalized[str(key)] = value
            elif value is not None:
                normalized[str(key)] = str(value)
        return normalized

    @staticmethod
    def _chroma_where(metadata_filter: dict[str, Any]) -> dict[str, Any] | None:
        if not metadata_filter:
            return None
        clauses = [{str(key): value} for key, value in metadata_filter.items()]
        return clauses[0] if len(clauses) == 1 else {"$and": clauses}

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id)
        internal_id = f"{doc.id}::{self._next_index}"
        self._next_index += 1
        return {
            "id": internal_id,
            "doc_id": str(metadata["doc_id"]),
            "content": doc.content,
            "metadata": metadata,
            "embedding": [float(value) for value in self._embedding_fn(doc.content)],
        }

    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        ranked = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": float(_dot(query_embedding, record["embedding"])),
            }
            for record in records
        ]
        ranked.sort(key=lambda record: record["score"], reverse=True)
        return ranked[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        records = [self._make_record(doc) for doc in docs]
        if not records:
            return

        if self._use_chroma:
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[
                    self._normalize_chroma_metadata(record["metadata"])
                    for record in records
                ],
            )
            return
        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if top_k <= 0 or self.get_collection_size() == 0:
            return []
        if not self._use_chroma:
            return self._search_records(query, self._store, top_k)
        return self._search_chroma(query, top_k, metadata_filter=None)

    def _search_chroma(
        self,
        query: str,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        query_arguments: dict[str, Any] = {
            "query_embeddings": [self._embedding_fn(query)],
            "n_results": min(top_k, self.get_collection_size()),
            "include": ["documents", "metadatas", "distances"],
        }
        where = self._chroma_where(metadata_filter or {})
        if where is not None:
            query_arguments["where"] = where

        raw = self._collection.query(**query_arguments)
        ids = (raw.get("ids") or [[]])[0]
        documents = (raw.get("documents") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        return [
            {
                "id": record_id,
                "content": content,
                "metadata": dict(metadata or {}),
                "score": 1.0 - float(distance),
            }
            for record_id, content, metadata, distance in zip(
                ids, documents, metadatas, distances
            )
        ]

    def get_collection_size(self) -> int:
        if self._use_chroma:
            return int(self._collection.count())
        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        if not metadata_filter:
            return self.search(query, top_k)
        if top_k <= 0 or self.get_collection_size() == 0:
            return []
        if self._use_chroma:
            return self._search_chroma(query, top_k, metadata_filter)

        candidates = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        if self._use_chroma:
            matches = self._collection.get(where={"doc_id": doc_id}, include=[])
            ids = matches.get("ids") or []
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        size_before = len(self._store)
        self._store = [
            record for record in self._store if str(record["metadata"].get("doc_id")) != doc_id
        ]
        return len(self._store) < size_before
