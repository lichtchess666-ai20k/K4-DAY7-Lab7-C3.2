"""Additional contract tests for Tri Tue's individual Lab 7 package."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.TriTue import (
    ChunkingStrategyComparator,
    ContextualParagraphWindowChunker,
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    MockEmbedder,
    RecursiveChunker,
    SentenceChunker,
    _mock_embed,
    compute_similarity,
)


def test_contextual_paragraph_chunker_packs_short_table_cells():
    text = "Hỏa Tốc\n\nInstant\n\n60 x 60 x 60\n\n30"

    chunks = ContextualParagraphWindowChunker(chunk_size=100).chunk(text)

    assert chunks == [text]


def test_contextual_paragraph_chunker_overlaps_last_paragraph():
    text = "A" * 40 + "\n\n" + "B" * 40 + "\n\n" + "C" * 40

    chunks = ContextualParagraphWindowChunker(
        chunk_size=85, overlap_paragraphs=1
    ).chunk(text)

    assert chunks == [
        "A" * 40 + "\n\n" + "B" * 40,
        "B" * 40 + "\n\n" + "C" * 40,
    ]


def test_contextual_paragraph_chunker_splits_long_paragraph_at_words():
    text = " ".join(f"word{index}" for index in range(80))

    chunks = ContextualParagraphWindowChunker(
        chunk_size=90, overlap_paragraphs=0, word_overlap=3
    ).chunk(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= 90 for chunk in chunks)
    assert chunks[0].split()[-3:] == chunks[1].split()[:3]


def test_contextual_paragraph_chunker_validates_configuration_and_empty_text():
    assert ContextualParagraphWindowChunker().chunk(" \r\n\t") == []

    with pytest.raises(ValueError, match="chunk_size"):
        ContextualParagraphWindowChunker(chunk_size=0)
    with pytest.raises(ValueError, match="overlap_paragraphs"):
        ContextualParagraphWindowChunker(overlap_paragraphs=-1)
    with pytest.raises(ValueError, match="word_overlap"):
        ContextualParagraphWindowChunker(word_overlap=-1)


def test_contextual_paragraph_chunker_preserves_a_single_oversized_token():
    token = "x" * 120

    chunks = ContextualParagraphWindowChunker(
        chunk_size=20, overlap_paragraphs=0, word_overlap=5
    ).chunk(token)

    assert chunks == [token]


def test_contextual_paragraph_chunker_preserves_repeated_paragraphs_without_overlap():
    chunks = ContextualParagraphWindowChunker(
        chunk_size=2,
        overlap_paragraphs=0,
    ).chunk("AA\n\nAA")

    assert chunks == ["AA", "AA"]


def test_group_benchmark_contract_has_five_queries_and_seller_filter():
    from src.TriTue.group_benchmark import BENCHMARK_QUERIES

    assert len(BENCHMARK_QUERIES) == 5
    assert BENCHMARK_QUERIES[1]["metadata_filter"] == {
        "customer_role": "seller"
    }
    assert all(
        benchmark["query"]
        and benchmark["gold_answer"]
        and benchmark["expected_doc_id"]
        and benchmark["evidence_groups"]
        for benchmark in BENCHMARK_QUERIES
    )


def test_group_relevance_requires_document_and_all_evidence_groups():
    from src.TriTue.group_benchmark import is_relevant

    benchmark = {
        "expected_doc_id": "returns",
        "evidence_groups": [("15 ngày",), ("24 giờ",)],
    }
    wrong_document = {
        "content": "thời hạn 15 ngày, riêng thực phẩm là 24 giờ",
        "metadata": {"doc_id": "shipping"},
    }
    incomplete_content = {
        "content": "thời hạn 15 ngày",
        "metadata": {"doc_id": "returns"},
    }
    relevant = {
        "content": "Thời hạn 15 NGÀY, riêng thực phẩm là 24 GIỜ.",
        "metadata": {"doc_id": "returns"},
    }

    assert not is_relevant(wrong_document, benchmark)
    assert not is_relevant(incomplete_content, benchmark)
    assert is_relevant(relevant, benchmark)


def test_group_corpus_loader_reads_six_files_and_preserves_metadata():
    from src.TriTue.group_benchmark import load_corpus

    data_dir = Path(__file__).resolve().parents[1] / "data" / "k4_ecommerce"
    chunks = load_corpus(data_dir, ContextualParagraphWindowChunker())

    assert {chunk.metadata["doc_id"] for chunk in chunks} == {
        "shopee-marketplace-terms",
        "shopee-payment-methods",
        "shopee-privacy-policy",
        "shopee-returns-refund",
        "shopee-seller-listing-rules",
        "shopee-shipping-policy",
    }
    assert all(chunk.metadata["source_url"] for chunk in chunks)
    assert all(chunk.metadata["chunking_strategy"] == "contextual_paragraph_window" for chunk in chunks)
    assert all(isinstance(chunk.metadata["chunk_index"], int) for chunk in chunks)
    assert all(chunk.id.endswith(str(chunk.metadata["chunk_index"])) for chunk in chunks)


def test_every_group_benchmark_has_matching_evidence_in_the_real_corpus():
    from src.TriTue.group_benchmark import (
        BENCHMARK_QUERIES,
        is_relevant,
        load_corpus,
    )

    data_dir = Path(__file__).resolve().parents[1] / "data" / "k4_ecommerce"
    chunks = load_corpus(data_dir, ContextualParagraphWindowChunker())

    for benchmark in BENCHMARK_QUERIES:
        assert any(
            is_relevant(
                {"content": chunk.content, "metadata": chunk.metadata},
                benchmark,
            )
            for chunk in chunks
        ), benchmark["expected_doc_id"]


def test_rendered_mock_benchmark_discloses_semantic_limitation():
    from src.TriTue.group_benchmark import render_markdown, run_benchmark

    data_dir = Path(__file__).resolve().parents[1] / "data" / "k4_ecommerce"
    summary = run_benchmark(
        _mock_embed,
        data_dir,
        embedding_label="mock",
    )
    markdown = render_markdown(summary)

    assert "không có ý nghĩa ngữ nghĩa" in markdown
    assert "ContextualParagraphWindowChunker" in markdown
    assert len(summary["queries"]) == 5
    assert summary["queries"][1]["metadata_filter"] == {
        "customer_role": "seller"
    }
    assert all(len(item["results"]) == 3 for item in summary["queries"])


def test_group_benchmark_marks_relevance_without_generating_fake_answers():
    from src.TriTue.group_benchmark import render_markdown

    summary = {
        "embedding_label": "unit-test",
        "chunker": {
            "name": "ContextualParagraphWindowChunker",
            "chunk_size": 900,
            "overlap_paragraphs": 1,
            "word_overlap": 20,
        },
        "total_chunks": 1,
        "average_chunk_length": 42.0,
        "top_k": 3,
        "queries": [
            {
                "number": 1,
                "query": "Câu hỏi kiểm thử?",
                "gold_answer": "Đáp án chỉ để đối chiếu.",
                "expected_doc_id": "expected-demo",
                "metadata_filter": None,
                "first_relevant_rank": 1,
                "top_k_relevant": True,
                "results": [
                    {
                        "rank": 1,
                        "content": "Bằng chứng truy xuất thật.",
                        "metadata": {"doc_id": "demo"},
                        "score": 0.9,
                        "relevant": True,
                    }
                ],
            }
        ],
    }

    markdown = render_markdown(summary)

    assert "Bằng chứng truy xuất thật" in markdown
    assert "Đáp án chỉ để đối chiếu" not in markdown
    assert "Expected document: `expected-demo`" in markdown


def test_group_benchmark_cli_handles_windows_cp1252_stdout(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "benchmark.md"
    environment = dict(os.environ)
    environment["PYTHONIOENCODING"] = "cp1252"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.TriTue.group_benchmark",
            "--mock",
            "--output",
            str(output_path),
        ],
        cwd=project_root,
        env=environment,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    assert output_path.is_file()


def test_group_benchmark_cli_refuses_to_write_the_group_report(monkeypatch):
    import src.TriTue.group_benchmark as group_benchmark

    group_report = Path(__file__).resolve().parents[1] / "report" / "REPORT_NHOM.md"

    def must_not_run(*args, **kwargs):
        raise AssertionError("benchmark must stop before writing the group report")

    monkeypatch.setattr(group_benchmark, "run_benchmark", must_not_run)

    exit_code = group_benchmark.main(
        ["--mock", "--output", str(group_report)]
    )

    assert exit_code == 2


def test_tritue_document_keeps_metadata():
    doc = Document("d1", "content", {"lang": "vi"})

    assert doc.id == "d1"
    assert doc.content == "content"
    assert doc.metadata == {"lang": "vi"}


def test_tritue_document_uses_independent_metadata_defaults():
    first = Document("d1", "first")
    second = Document("d2", "second")

    first.metadata["lang"] = "vi"

    assert second.metadata == {}


def test_tritue_mock_embedder_is_deterministic_and_normalized():
    embedder = MockEmbedder()

    first = embedder("xin chào")

    assert first == embedder("xin chào")
    assert len(first) == 64
    assert sum(value * value for value in first) == pytest.approx(1.0)


def test_sentence_chunker_handles_newline_boundaries_and_empty_text():
    chunker = SentenceChunker(max_sentences_per_chunk=2)

    assert chunker.chunk("") == []
    assert chunker.chunk("Một.\nHai! Ba?") == ["Một. Hai!", "Ba?"]


def test_sentence_chunker_enforces_at_least_one_sentence_per_chunk():
    chunks = SentenceChunker(max_sentences_per_chunk=0).chunk("Một. Hai.")

    assert chunks == ["Một.", "Hai."]


def test_recursive_chunker_preserves_text_when_separator_is_missing():
    chunks = RecursiveChunker(separators=["\n\n"], chunk_size=4).chunk("abcdefghij")

    assert chunks == ["abcd", "efgh", "ij"]


def test_recursive_chunker_uses_structural_boundaries_when_possible():
    text = "đoạn một\n\nđoạn hai\n\nđoạn ba"

    chunks = RecursiveChunker(chunk_size=18).chunk(text)

    assert chunks == ["đoạn một\n\nđoạn hai", "\n\nđoạn ba"]
    assert "".join(chunks) == text


def test_recursive_chunker_packs_words_without_losing_content():
    text = "word " * 200

    chunks = RecursiveChunker(chunk_size=100).chunk(text)

    assert "".join(chunks) == text
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert len(chunks) <= 11


def test_similarity_rejects_mismatched_dimensions():
    with pytest.raises(ValueError, match="same dimension"):
        compute_similarity([1.0], [1.0, 2.0])


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ([1.0, 0.0], [1.0, 0.0], 1.0),
        ([1.0, 0.0], [0.0, 1.0], 0.0),
        ([1.0, 0.0], [-1.0, 0.0], -1.0),
        ([0.0, 0.0], [1.0, 2.0], 0.0),
    ],
)
def test_similarity_handles_standard_vector_relationships(left, right, expected):
    assert compute_similarity(left, right) == pytest.approx(expected)


def test_comparator_returns_required_stats_for_all_strategies():
    result = ChunkingStrategyComparator().compare("Một câu. Hai câu. Ba câu.", chunk_size=12)

    assert set(result) == {"fixed_size", "by_sentences", "recursive"}
    for stats in result.values():
        assert stats["count"] == len(stats["chunks"])
        assert stats["count"] > 0
        assert stats["avg_length"] == pytest.approx(
            sum(len(chunk) for chunk in stats["chunks"]) / stats["count"]
        )


def test_fixed_size_chunker_rejects_non_advancing_windows():
    with pytest.raises(ValueError, match="overlap"):
        FixedSizeChunker(chunk_size=10, overlap=10)


def test_store_copies_metadata_and_adds_doc_id():
    metadata = {"lang": "vi"}
    store = EmbeddingStore("tritue_record", embedding_fn=_mock_embed)

    store.add_documents([Document("d1", "nội dung", metadata)])
    metadata["lang"] = "en"
    result = store.search("nội dung", top_k=1)[0]

    assert result["metadata"] == {"lang": "vi", "doc_id": "d1"}


def test_store_filters_before_search_and_deletes_all_chunks():
    store = EmbeddingStore("tritue_filter", embedding_fn=_mock_embed)
    store.add_documents(
        [
            Document(
                "d1-c0",
                "đổi trả một",
                {"doc_id": "d1", "lang": "vi", "category": "return"},
            ),
            Document(
                "d1-c1",
                "đổi trả hai",
                {"doc_id": "d1", "lang": "vi", "category": "return"},
            ),
            Document(
                "d2-c0",
                "shipping",
                {"doc_id": "d2", "lang": "en", "category": "shipping"},
            ),
        ]
    )

    results = store.search_with_filter(
        "đổi trả", top_k=5, metadata_filter={"lang": "vi", "category": "return"}
    )

    assert len(results) == 2
    assert all(result["metadata"]["doc_id"] == "d1" for result in results)
    assert store.delete_document("d1") is True
    assert store.get_collection_size() == 1
    assert store.delete_document("d1") is False


def test_store_search_is_sorted_and_handles_non_positive_top_k():
    vectors = {
        "query": [1.0, 0.0],
        "best": [1.0, 0.0],
        "middle": [0.5, 0.5],
        "last": [0.0, 1.0],
    }
    store = EmbeddingStore("tritue_ranking", embedding_fn=vectors.__getitem__)
    store.add_documents(
        [
            Document("last", "last"),
            Document("best", "best"),
            Document("middle", "middle"),
        ]
    )

    results = store.search("query", top_k=3)

    assert [result["content"] for result in results] == ["best", "middle", "last"]
    assert [result["score"] for result in results] == sorted(
        [result["score"] for result in results], reverse=True
    )
    assert store.search("query", top_k=0) == []


def test_empty_store_operations_are_safe():
    store = EmbeddingStore("tritue_empty", embedding_fn=_mock_embed)

    assert store.search("anything") == []
    assert store.search_with_filter("anything", metadata_filter={"lang": "vi"}) == []
    assert store.get_collection_size() == 0
    assert store.delete_document("missing") is False


def test_agent_injects_ranked_context_and_question_into_prompt():
    store = EmbeddingStore("tritue_agent", embedding_fn=_mock_embed)
    store.add_documents([Document("d1", "Khách hàng có 7 ngày để đổi trả.", {})])
    captured = {}

    def fake_llm(prompt):
        captured["prompt"] = prompt
        return "7 ngày"

    answer = KnowledgeBaseAgent(store, fake_llm).answer(
        "Được đổi trả trong bao lâu?", top_k=1
    )

    assert answer == "7 ngày"
    assert "Khách hàng có 7 ngày để đổi trả." in captured["prompt"]
    assert "Được đổi trả trong bao lâu?" in captured["prompt"]
    assert "chỉ" in captured["prompt"].lower()


def test_agent_tells_llm_when_no_context_is_available():
    store = EmbeddingStore("tritue_agent_empty", embedding_fn=_mock_embed)
    captured = {}

    def fake_llm(prompt):
        captured["prompt"] = prompt
        return "Không đủ thông tin."

    answer = KnowledgeBaseAgent(store, fake_llm).answer("Câu hỏi không có dữ liệu")

    assert answer == "Không đủ thông tin."
    assert "Không tìm thấy ngữ cảnh phù hợp" in captured["prompt"]


def test_agent_can_answer_from_the_exact_retrieved_results():
    class StoreThatMustNotSearch:
        def search(self, question, top_k):
            raise AssertionError("answer_from_results must not perform another search")

    captured = {}

    def fake_llm(prompt):
        captured["prompt"] = prompt
        return "Đã dùng đúng context."

    results = [
        {
            "content": "Chỉ context đã lọc được phép xuất hiện.",
            "metadata": {"source_url": "https://example.com/filtered"},
            "score": 0.9,
        }
    ]

    answer = KnowledgeBaseAgent(StoreThatMustNotSearch(), fake_llm).answer_from_results(
        "Câu hỏi", results
    )

    assert answer == "Đã dùng đúng context."
    assert "Chỉ context đã lọc" in captured["prompt"]


def test_personal_demo_defines_exactly_five_k4_queries():
    from src.TriTue.__main__ import BENCHMARK_QUERIES

    assert len(BENCHMARK_QUERIES) == 5
    assert any(
        item.get("metadata_filter") == {"customer_role": "seller"}
        for item in BENCHMARK_QUERIES
    )
    assert all(item["gold_answer"] and item["expected_doc_id"] for item in BENCHMARK_QUERIES)


def test_personal_demo_chunks_the_current_corpus_at_500_characters():
    from src.TriTue.__main__ import build_starter_store, load_starter_chunks

    chunks = load_starter_chunks()
    store = build_starter_store()

    assert {chunk.metadata["doc_id"] for chunk in chunks} == {
        "shopee-marketplace-terms",
        "shopee-payment-methods",
        "shopee-privacy-policy",
        "shopee-returns-refund",
        "shopee-seller-listing-rules",
        "shopee-shipping-policy",
    }
    assert all(len(chunk.content) <= 500 for chunk in chunks)
    assert store.get_collection_size() == len(chunks)


def test_extractive_demo_llm_selects_evidence_without_gold_answer_access():
    from src.TriTue.__main__ import extractive_demo_llm

    prompt = (
        "NGỮ CẢNH:\n"
        "[Ngữ cảnh 1 | nguồn: demo]\n"
        "Người mua cần bằng chứng khi đổi trả. "
        "Sản phẩm bị cấm không được đăng bán.\n\n"
        "CÂU HỎI:\nSản phẩm bị cấm có được đăng bán không?\n\n"
        "TRẢ LỜI:"
    )

    assert extractive_demo_llm(prompt) == "Sản phẩm bị cấm không được đăng bán."


def test_personal_demo_handles_windows_cp1252_stdout():
    project_root = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    environment["PYTHONIOENCODING"] = "cp1252"

    completed = subprocess.run(
        [sys.executable, "-m", "src.TriTue"],
        cwd=project_root,
        env=environment,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
