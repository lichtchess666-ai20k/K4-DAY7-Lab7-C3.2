"""Run Tri Tue's offline personal benchmark for Lab 7."""

from __future__ import annotations

from pathlib import Path
import re
import sys

from ingest import parse_front_matter

from . import (
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    KnowledgeBaseAgent,
    RecursiveChunker,
    _mock_embed,
    compute_similarity,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STARTER_DATA_DIR = PROJECT_ROOT / "data" / "k4_ecommerce"

BENCHMARK_QUERIES = [
    {
        "query": "Khi hàng bị lỗi hoặc không đúng mô tả, yêu cầu đổi trả cần kèm gì?",
        "gold_answer": "Yêu cầu đổi trả phải kèm bằng chứng phù hợp.",
        "expected_doc_id": "k4-returns-policy",
        "evidence": "kèm bằng chứng phù hợp",
    },
    {
        "query": "Người bán có trách nhiệm gì khi nhận yêu cầu đổi trả?",
        "gold_answer": "Người bán có trách nhiệm phản hồi theo quy trình của sàn.",
        "expected_doc_id": "k4-returns-policy",
        "evidence": "phản hồi theo quy trình của sàn",
    },
    {
        "query": "Thông tin nào về sản phẩm phải được người bán cung cấp chính xác?",
        "gold_answer": "Người bán phải cung cấp chính xác giá, mô tả và tình trạng hàng.",
        "expected_doc_id": "k4-seller-listing",
        "evidence": "bao gồm giá, mô tả và tình trạng hàng",
    },
    {
        "query": "Sản phẩm bị hạn chế hoặc bị cấm có được đăng bán không?",
        "gold_answer": "Không. Sản phẩm bị hạn chế hoặc bị cấm không được đăng bán.",
        "expected_doc_id": "k4-seller-listing",
        "evidence": "không được đăng bán",
    },
    {
        "query": "Người bán cần tuân thủ điều gì khi đăng bán sản phẩm?",
        "gold_answer": (
            "Người bán phải cung cấp thông tin sản phẩm chính xác và không đăng "
            "sản phẩm bị hạn chế hoặc bị cấm."
        ),
        "expected_doc_id": "k4-seller-listing",
        "evidence": "thông tin sản phẩm chính xác",
        "metadata_filter": {"customer_role": "seller"},
    },
]

SIMILARITY_PAIRS = [
    (
        "Tôi muốn trả lại sản phẩm bị lỗi.",
        "Hướng dẫn đổi trả hàng không đúng mô tả.",
        "cao",
    ),
    (
        "Người bán phải mô tả sản phẩm chính xác.",
        "Thông tin đăng bán cần đúng với tình trạng hàng.",
        "cao",
    ),
    (
        "Khách hàng gửi yêu cầu hoàn tiền.",
        "Hôm nay thời tiết có mưa.",
        "thấp",
    ),
    (
        "Chính sách giao hàng áp dụng toàn quốc.",
        "Quy định thanh toán bằng thẻ tín dụng.",
        "thấp",
    ),
    (
        "Không được đăng bán sản phẩm bị cấm.",
        "Hàng hóa thuộc danh mục cấm phải bị gỡ khỏi sàn.",
        "cao",
    ),
]


def load_starter_chunks() -> list[Document]:
    """Load and recursively split the K4 starter documents at 500 characters."""

    chunker = RecursiveChunker(chunk_size=500)
    chunks: list[Document] = []
    for path in sorted(STARTER_DATA_DIR.glob("*.md")):
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        doc_id = str(metadata.get("doc_id") or path.stem)
        metadata.setdefault("doc_id", doc_id)
        metadata.setdefault("source", str(path.relative_to(PROJECT_ROOT)))
        for index, content in enumerate(chunker.chunk(body)):
            chunk_metadata = dict(metadata)
            chunk_metadata["chunk_index"] = index
            chunks.append(
                Document(
                    id=f"{doc_id}::chunk_{index}",
                    content=content,
                    metadata=chunk_metadata,
                )
            )
    return chunks


def build_starter_store() -> EmbeddingStore:
    """Build a deterministic store from the current K4 corpus."""

    store = EmbeddingStore("tritue_k4_starter", embedding_fn=_mock_embed)
    store.add_documents(load_starter_chunks())
    return store


def evaluate_similarity_pairs() -> list[dict]:
    results = []
    for sentence_a, sentence_b, prediction in SIMILARITY_PAIRS:
        score = compute_similarity(_mock_embed(sentence_a), _mock_embed(sentence_b))
        results.append(
            {
                "sentence_a": sentence_a,
                "sentence_b": sentence_b,
                "prediction": prediction,
                "score": score,
            }
        )
    return results


def extractive_demo_llm(prompt: str) -> str:
    """Select the context sentence with the largest token overlap with the question."""

    context_marker = "NGỮ CẢNH:\n"
    question_marker = "\n\nCÂU HỎI:\n"
    if context_marker not in prompt or question_marker not in prompt:
        return "Không đủ thông tin trong ngữ cảnh truy xuất."

    context_and_question = prompt.split(context_marker, 1)[1]
    context, question_and_tail = context_and_question.split(question_marker, 1)
    question = question_and_tail.split("\n\nTRẢ LỜI:", 1)[0]

    context_without_headers = "\n".join(
        line for line in context.splitlines() if not line.startswith("[Ngữ cảnh ")
    )
    candidates = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", context_without_headers)
        if sentence.strip() and not sentence.lstrip().startswith("#")
    ]
    if not candidates:
        return "Không đủ thông tin trong ngữ cảnh truy xuất."

    stop_words = {
        "ai",
        "bị",
        "có",
        "cần",
        "cho",
        "của",
        "điều",
        "được",
        "gì",
        "khi",
        "không",
        "là",
        "nào",
        "nhận",
        "phải",
        "theo",
        "thì",
        "và",
        "với",
    }

    def meaningful_tokens(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE)
            if token not in stop_words and len(token) > 1
        }

    question_tokens = meaningful_tokens(question)
    best_sentence = max(
        candidates,
        key=lambda sentence: (
            len(meaningful_tokens(sentence) & question_tokens),
            -len(meaningful_tokens(sentence)),
        ),
    )
    return best_sentence


def evaluate_benchmarks(store: EmbeddingStore) -> list[dict]:
    evaluations = []
    for item in BENCHMARK_QUERIES:
        metadata_filter = item.get("metadata_filter")
        if metadata_filter:
            results = store.search_with_filter(
                item["query"], top_k=3, metadata_filter=metadata_filter
            )
        else:
            results = store.search(item["query"], top_k=3)

        top3_relevant = any(
            result["metadata"].get("doc_id") == item["expected_doc_id"]
            for result in results
        )

        agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_demo_llm)
        agent_answer = agent.answer_from_results(item["query"], results)
        top_result = results[0] if results else None
        evaluations.append(
            {
                "query": item["query"],
                "top1_doc_id": (
                    top_result["metadata"].get("doc_id") if top_result else None
                ),
                "top1_content": top_result["content"] if top_result else "",
                "score": top_result["score"] if top_result else 0.0,
                "top3_relevant": top3_relevant,
                "agent_answer": agent_answer,
                "metadata_filter": metadata_filter,
            }
        )
    return evaluations


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=== TRI TUE - LAB 7 PERSONAL DEMO ===")
    print("Cảnh báo: mock embedding chỉ dùng để test, không đo chất lượng ngữ nghĩa.\n")

    sample_text = next(iter(STARTER_DATA_DIR.glob("*.md"))).read_text(encoding="utf-8")
    comparison = ChunkingStrategyComparator().compare(sample_text, chunk_size=200)
    print("Chunking comparator:")
    for strategy, stats in comparison.items():
        print(
            f"- {strategy}: count={stats['count']}, "
            f"avg_length={stats['avg_length']:.2f}"
        )

    print("\nSimilarity predictions:")
    for index, result in enumerate(evaluate_similarity_pairs(), start=1):
        print(
            f"{index}. predicted={result['prediction']}, "
            f"mock_score={result['score']:.6f}"
        )

    store = build_starter_store()
    print(f"\nStarter store: {store.get_collection_size()} chunks")
    print("Benchmark queries:")
    for index, result in enumerate(evaluate_benchmarks(store), start=1):
        print(
            f"{index}. score={result['score']:.6f}, "
            f"top1={result['top1_doc_id']}, "
            f"top3_relevant={result['top3_relevant']}"
        )
        print(f"   agent={result['agent_answer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
