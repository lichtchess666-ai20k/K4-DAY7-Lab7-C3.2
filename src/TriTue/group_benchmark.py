"""Benchmark Tri Tue's custom chunker on the shared Shopee corpus."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

from ingest import parse_front_matter

from .custom_chunking import ContextualParagraphWindowChunker
from .embeddings import LocalEmbedder, _mock_embed
from .models import Document
from .store import EmbeddingStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "k4_ecommerce"
GROUP_REPORT_PATH = PROJECT_ROOT / "report" / "REPORT_NHOM.md"

CORPUS_FILENAMES = (
    "shopee-marketplace-terms.md",
    "shopee-payment-methods.md",
    "shopee-privacy-policy.md",
    "shopee-returns-refund.md",
    "shopee-seller-listing-rules.md",
    "shopee-shipping-policy.md",
)

BENCHMARK_QUERIES: list[dict[str, Any]] = [
    {
        "query": (
            "Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng/hoàn tiền kể từ "
            "khi đơn hàng giao thành công? Trường hợp nào có thời hạn ngắn hơn?"
        ),
        "gold_answer": (
            "15 ngày kể từ khi đơn hàng được cập nhật giao hàng thành công; riêng "
            "thực phẩm tươi sống/đông lạnh chỉ có 24 giờ kể từ lúc giao thành công."
        ),
        "expected_doc_id": "shopee-returns-refund",
        "evidence_groups": [
            ("15 ngày", "15 (mười lăm) ngày", "mười lăm ngày"),
            ("24 giờ",),
        ],
    },
    {
        "query": (
            "Theo quy định đăng bán sản phẩm, hình ảnh sản phẩm do người bán tự "
            "chụp phải chiếm tối thiểu bao nhiêu % diện tích ảnh?"
        ),
        "gold_answer": (
            "Phải có ít nhất 1 hình ảnh thật do chính Người Bán tự chụp, trong đó "
            "diện tích sản phẩm thật phải chiếm tối thiểu 40% diện tích toàn ảnh."
        ),
        "expected_doc_id": "shopee-seller-listing-rules",
        "evidence_groups": [("40%",)],
        "metadata_filter": {"customer_role": "seller"},
    },
    {
        "query": (
            "Đơn hàng thanh toán bằng Apple Pay trên Shopee cần có giá trị thanh "
            "toán cuối cùng trong khoảng nào?"
        ),
        "gold_answer": (
            "Từ 10.000 VNĐ đến 25.000.000 VNĐ, đã gồm phí vận chuyển và các chi "
            "phí phát sinh khác nếu có."
        ),
        "expected_doc_id": "shopee-payment-methods",
        "evidence_groups": [
            ("10.000 VNĐ", "10,000 VNĐ"),
            ("25.000.000 VNĐ", "25,000,000 VNĐ"),
        ],
    },
    {
        "query": (
            "Kiện hàng vận chuyển theo hình thức Hỏa Tốc (Instant) bị giới hạn "
            "kích thước và cân nặng tối đa bao nhiêu?"
        ),
        "gold_answer": (
            "Tối đa mỗi cạnh 60 x 60 x 60 cm và giới hạn cân nặng 30kg."
        ),
        "expected_doc_id": "shopee-shipping-policy",
        "evidence_groups": [("60 x 60 x 60",), ("30kg", "30 kg", "\n30\n")],
    },
    {
        "query": (
            "Chính sách bảo mật của Shopee áp dụng cho những đối tượng người dùng nào?"
        ),
        "gold_answer": (
            "Áp dụng cho cả Người Bán và Người Mua đang sử dụng Dịch vụ, trừ khi "
            "có tuyên bố rõ ràng ngược lại."
        ),
        "expected_doc_id": "shopee-privacy-policy",
        "evidence_groups": [("Người bán",), ("Người mua",)],
    },
]


def load_corpus(
    data_dir: Path,
    chunker: ContextualParagraphWindowChunker,
) -> list[Document]:
    """Load the six shared documents and attach source metadata to every chunk."""
    chunks: list[Document] = []

    for filename in CORPUS_FILENAMES:
        path = data_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing corpus file: {path}")

        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        doc_id = str(metadata.get("doc_id") or path.stem)
        base_metadata = dict(metadata)
        base_metadata["doc_id"] = doc_id
        base_metadata.setdefault("source", str(path))

        for index, content in enumerate(chunker.chunk(body)):
            chunk_metadata = dict(base_metadata)
            chunk_metadata.update(
                {
                    "chunk_index": index,
                    "chunking_strategy": "contextual_paragraph_window",
                }
            )
            chunks.append(
                Document(
                    id=f"{doc_id}::contextual_{index}",
                    content=content,
                    metadata=chunk_metadata,
                )
            )

    return chunks


def is_relevant(result: dict[str, Any], benchmark: dict[str, Any]) -> bool:
    """Require both the expected source document and every evidence concept."""
    metadata = result.get("metadata") or {}
    if str(metadata.get("doc_id")) != str(benchmark["expected_doc_id"]):
        return False

    content = str(result.get("content") or "").casefold()
    return all(
        any(str(variant).casefold() in content for variant in evidence_group)
        for evidence_group in benchmark["evidence_groups"]
    )


def run_benchmark(
    embedding_fn,
    data_dir: Path = DEFAULT_DATA_DIR,
    top_k: int = 3,
    embedding_label: str | None = None,
) -> dict[str, Any]:
    """Chunk, index, and retrieve the shared five-query benchmark."""
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    chunker = ContextualParagraphWindowChunker()
    chunks = load_corpus(Path(data_dir), chunker)
    store = EmbeddingStore(
        collection_name="tritue_contextual_benchmark",
        embedding_fn=embedding_fn,
    )
    store.add_documents(chunks)

    query_summaries: list[dict[str, Any]] = []
    for number, benchmark in enumerate(BENCHMARK_QUERIES, start=1):
        metadata_filter = benchmark.get("metadata_filter")
        if metadata_filter:
            raw_results = store.search_with_filter(
                benchmark["query"],
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        else:
            raw_results = store.search(benchmark["query"], top_k=top_k)

        results: list[dict[str, Any]] = []
        first_relevant_rank: int | None = None
        for rank, result in enumerate(raw_results, start=1):
            relevant = is_relevant(result, benchmark)
            if relevant and first_relevant_rank is None:
                first_relevant_rank = rank
            results.append(
                {
                    "rank": rank,
                    "content": result["content"],
                    "metadata": dict(result.get("metadata") or {}),
                    "score": float(result["score"]),
                    "relevant": relevant,
                }
            )

        query_summaries.append(
            {
                "number": number,
                "query": benchmark["query"],
                "gold_answer": benchmark["gold_answer"],
                "expected_doc_id": benchmark["expected_doc_id"],
                "metadata_filter": metadata_filter,
                "first_relevant_rank": first_relevant_rank,
                "top_k_relevant": first_relevant_rank is not None,
                "results": results,
            }
        )

    label = embedding_label or str(
        getattr(embedding_fn, "_backend_name", type(embedding_fn).__name__)
    )
    average_length = (
        sum(len(chunk.content) for chunk in chunks) / len(chunks) if chunks else 0.0
    )
    return {
        "embedding_label": label,
        "chunker": {
            "name": type(chunker).__name__,
            "chunk_size": chunker.chunk_size,
            "overlap_paragraphs": chunker.overlap_paragraphs,
            "word_overlap": chunker.word_overlap,
        },
        "total_chunks": len(chunks),
        "average_chunk_length": average_length,
        "top_k": top_k,
        "queries": query_summaries,
    }


def _table_text(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _result_excerpt(content: str, limit: int = 360) -> str:
    compact = " ".join(content.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def render_markdown(summary: dict[str, Any]) -> str:
    """Render a handoff report based only on actual retrieval results."""
    chunker = summary["chunker"]
    lines = [
        "# Đóng góp benchmark của TriTue",
        "",
        "## Cấu hình",
        "",
        f"- Chunker: `{chunker['name']}`",
        (
            f"- Tham số: `chunk_size={chunker['chunk_size']}`, "
            f"`overlap_paragraphs={chunker['overlap_paragraphs']}`, "
            f"`word_overlap={chunker['word_overlap']}`"
        ),
        f"- Embedding: `{summary['embedding_label']}`",
        f"- Tổng số chunk: {summary['total_chunks']}",
        f"- Độ dài chunk trung bình: {summary['average_chunk_length']:.1f} ký tự",
        "",
    ]

    if "mock" in str(summary["embedding_label"]).casefold():
        lines.extend(
            [
                "> **Cảnh báo:** Đây là mock embedding xác định dùng để smoke test; "
                "điểm và thứ hạng không có ý nghĩa ngữ nghĩa.",
                "",
            ]
        )

    lines.extend(
        [
            f"## Kết quả retrieval top-{summary['top_k']}",
            "",
            "| # | Metadata filter | Có chunk liên quan | Hạng đầu tiên | Top-1 nguồn | Score |",
            "|---:|---|---|---:|---|---:|",
        ]
    )
    for item in summary["queries"]:
        top_result = item["results"][0] if item["results"] else None
        source = top_result["metadata"].get("doc_id", "-") if top_result else "-"
        score = f"{top_result['score']:.4f}" if top_result else "-"
        filter_text = item["metadata_filter"] or "Không"
        rank = item["first_relevant_rank"] or "-"
        lines.append(
            f"| {item['number']} | {_table_text(filter_text)} | "
            f"{'Có' if item['top_k_relevant'] else 'Không'} | {rank} | "
            f"{_table_text(source)} | {score} |"
        )

    lines.extend(["", "## Chi tiết bằng chứng truy xuất", ""])
    for item in summary["queries"]:
        lines.extend(
            [
                f"### Câu {item['number']}",
                "",
                item["query"],
                "",
                f"Expected document: `{item.get('expected_doc_id', '-')}`",
                "",
            ]
        )
        if not item["results"]:
            lines.extend(["Không có kết quả truy xuất.", ""])
            continue
        for result in item["results"]:
            source = result["metadata"].get("doc_id", "không rõ")
            relevance = "liên quan" if result["relevant"] else "không đủ bằng chứng"
            lines.extend(
                [
                    (
                        f"- Hạng {result['rank']} — `{source}` — "
                        f"score `{result['score']:.4f}` — **{relevance}**: "
                        f"{_result_excerpt(result['content'])}"
                    ),
                    "",
                ]
            )

    failed = [
        str(item["number"])
        for item in summary["queries"]
        if not item["top_k_relevant"]
    ]
    failure_text = ", ".join(failed) if failed else "Không có"
    lines.extend(
        [
            "## Trường hợp retrieval thất bại",
            "",
            f"Các câu không có chunk đủ `doc_id + evidence` trong top-{summary['top_k']}: {failure_text}.",
            "",
            "> File này là phần bàn giao cá nhân cho nhóm trưởng; runner không sửa `report/REPORT_NHOM.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock embeddings")
    parser.add_argument("--output", type=Path, help="Write Markdown to this path")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args(argv)

    if args.output and args.output.resolve() == GROUP_REPORT_PATH.resolve():
        print(
            "Từ chối ghi report/REPORT_NHOM.md: file này thuộc quyền quản lý của nhóm trưởng.",
            file=sys.stderr,
        )
        return 2

    if args.mock:
        embedding_fn = _mock_embed
        embedding_label = "mock"
    else:
        try:
            embedding_fn = LocalEmbedder()
        except Exception as exc:
            print(
                "Không khởi tạo được local embedding. Hãy chạy "
                "`python -m pip install -r requirements-local.txt` rồi thử lại.\n"
                f"Chi tiết: {exc}",
                file=sys.stderr,
            )
            return 2
        embedding_label = str(embedding_fn._backend_name)

    try:
        summary = run_benchmark(
            embedding_fn,
            args.data_dir,
            top_k=args.top_k,
            embedding_label=embedding_label,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Không thể chạy benchmark: {exc}", file=sys.stderr)
        return 2

    markdown = render_markdown(summary)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
        print(f"Đã ghi kết quả benchmark vào {args.output}")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
