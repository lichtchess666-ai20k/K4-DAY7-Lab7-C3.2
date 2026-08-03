# TriTue Contextual Paragraph Chunker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng, kiểm thử và benchmark chiến lược `ContextualParagraphWindowChunker` của TriTue trên sáu tài liệu Shopee mà không sửa báo cáo nhóm.

**Architecture:** Chunker tách theo khối đoạn ngăn bằng dòng trống, ghép các đoạn lân cận theo ngân sách ký tự và overlap theo đoạn; đoạn đơn lẻ quá dài dùng word-boundary fallback. Runner riêng đọc front matter, tạo chunk documents, chạy đúng năm query nhóm, đánh giá relevance bằng `doc_id + evidence`, rồi render kết quả cá nhân ra Markdown.

**Tech Stack:** Python 3.11-compatible standard library, pytest 9.1.1, package `src.TriTue`, optional sentence-transformers multilingual embedder.

## Global Constraints

- Không sửa `report/REPORT_NHOM.md`.
- Không chia chính theo dòng, câu, heading/điều khoản hoặc loại chính sách.
- Cấu hình mặc định: `chunk_size=900`, `overlap_paragraphs=1`, `word_overlap=20`.
- Mock embedding chỉ dùng smoke test và mọi output mock phải ghi rõ không có ý nghĩa ngữ nghĩa.
- Benchmark dùng đúng năm query hiện có; query thứ hai lọc `customer_role=seller`.
- Relevance yêu cầu đúng cả `doc_id` và evidence trong chunk.

---

### Task 1: ContextualParagraphWindowChunker

**Files:**
- Create: `src/TriTue/custom_chunking.py`
- Modify: `src/TriTue/__init__.py`
- Modify: `tests/test_tritue_solution.py`

**Interfaces:**
- Produces: `ContextualParagraphWindowChunker(chunk_size: int = 900, overlap_paragraphs: int = 1, word_overlap: int = 20)`.
- Produces: `chunk(text: str) -> list[str]`.

- [ ] **Step 1: Viết test đỏ cho packing, overlap, bảng và fallback**

```python
def test_contextual_paragraph_chunker_packs_short_table_cells():
    text = "Hỏa Tốc\n\nInstant\n\n60 x 60 x 60\n\n30"
    chunks = ContextualParagraphWindowChunker(chunk_size=100).chunk(text)
    assert chunks == [text]


def test_contextual_paragraph_chunker_overlaps_last_paragraph():
    text = "A" * 40 + "\n\n" + "B" * 40 + "\n\n" + "C" * 40
    chunks = ContextualParagraphWindowChunker(
        chunk_size=85, overlap_paragraphs=1
    ).chunk(text)
    assert chunks == ["A" * 40 + "\n\n" + "B" * 40, "B" * 40 + "\n\n" + "C" * 40]


def test_contextual_paragraph_chunker_splits_long_paragraph_at_words():
    text = " ".join(f"word{i}" for i in range(80))
    chunks = ContextualParagraphWindowChunker(
        chunk_size=90, overlap_paragraphs=0, word_overlap=3
    ).chunk(text)
    assert len(chunks) > 1
    assert all(len(chunk) <= 90 for chunk in chunks)
    assert chunks[0].split()[-3:] == chunks[1].split()[:3]
```

- [ ] **Step 2: Chạy test và xác nhận API chưa tồn tại**

Run: `python -m pytest tests/test_tritue_solution.py -k contextual_paragraph -v`
Expected: collection error hoặc import failure cho `ContextualParagraphWindowChunker`.

- [ ] **Step 3: Triển khai validation và paragraph packing**

Chuẩn hóa CRLF, split bằng regex `r"\n\s*\n+"`, trim từng block, rồi pack bằng `"\n\n"`. Khi phát chunk, sao chép tối đa số đoạn overlap nhưng bắt buộc index đầu vào tăng ở mỗi vòng.

- [ ] **Step 4: Triển khai oversized-paragraph fallback theo từ**

Tạo cửa sổ từ không vượt `chunk_size`, lùi tối đa `word_overlap` từ sau mỗi chunk, và phát token đơn lẻ nguyên vẹn nếu token dài hơn ngân sách.

- [ ] **Step 5: Chạy test chunker và toàn bộ regression**

Run: `python -m pytest tests/test_tritue_solution.py -v`
Expected: mọi test cá nhân PASS.

---

### Task 2: Corpus loader và benchmark contract

**Files:**
- Create: `src/TriTue/group_benchmark.py`
- Modify: `tests/test_tritue_solution.py`

**Interfaces:**
- Consumes: `Document`, `EmbeddingStore`, `ContextualParagraphWindowChunker`, `LocalEmbedder`, `_mock_embed`, `ingest.parse_front_matter`.
- Produces: `BENCHMARK_QUERIES: list[dict]` gồm đúng năm query.
- Produces: `load_corpus(data_dir: Path, chunker) -> list[Document]`.
- Produces: `is_relevant(result: dict, benchmark: dict) -> bool`.

- [ ] **Step 1: Viết test đỏ cho metadata, năm query, filter và evidence**

```python
def test_group_benchmark_contract_has_five_queries_and_seller_filter():
    assert len(BENCHMARK_QUERIES) == 5
    assert BENCHMARK_QUERIES[1]["metadata_filter"] == {
        "customer_role": "seller"
    }


def test_group_relevance_requires_document_and_all_evidence_groups():
    benchmark = {
        "expected_doc_id": "returns",
        "evidence_groups": [("15 ngày",), ("24 giờ",)],
    }
    wrong_content = {"content": "15 ngày", "metadata": {"doc_id": "returns"}}
    right = {
        "content": "thời hạn 15 ngày, riêng thực phẩm là 24 giờ",
        "metadata": {"doc_id": "returns"},
    }
    assert not is_relevant(wrong_content, benchmark)
    assert is_relevant(right, benchmark)
```

- [ ] **Step 2: Chạy test và xác nhận benchmark API chưa tồn tại**

Run: `python -m pytest tests/test_tritue_solution.py -k group_benchmark -v`
Expected: import failure cho `src.TriTue.group_benchmark`.

- [ ] **Step 3: Khai báo năm benchmark query và evidence groups**

Mỗi entry chứa `query`, `gold_answer`, `expected_doc_id`, `evidence_groups`, và optional `metadata_filter`. Evidence groups cho phép các biến thể viết số/chữ nhưng yêu cầu mọi nhóm ý chính xuất hiện.

- [ ] **Step 4: Triển khai corpus loader**

Đọc đúng sáu `.md`, parse front matter, tạo một `Document` cho từng chunk với ID `<doc_id>::contextual_<index>` và metadata bổ sung `chunk_index`, `chunking_strategy="contextual_paragraph_window"`.

- [ ] **Step 5: Chạy test contract và loader**

Run: `python -m pytest tests/test_tritue_solution.py -k "group_benchmark or corpus" -v`
Expected: mọi test được chọn PASS.

---

### Task 3: Chạy retrieval và render bàn giao

**Files:**
- Modify: `src/TriTue/group_benchmark.py`
- Create: `src/TriTue/GROUP_CONTRIBUTION.md` (generated benchmark handoff)
- Modify: `tests/test_tritue_solution.py`

**Interfaces:**
- Produces: `run_benchmark(embedding_fn, data_dir, top_k=3) -> dict`.
- Produces: `render_markdown(summary: dict) -> str`.
- Produces CLI: `python -m src.TriTue.group_benchmark [--mock] [--output PATH]`.

- [ ] **Step 1: Viết test đỏ cho top-3, filter path và Markdown disclosure**

```python
def test_rendered_mock_benchmark_discloses_semantic_limitation():
    summary = run_benchmark(_mock_embed, DATA_DIR, embedding_label="mock")
    markdown = render_markdown(summary)
    assert "không có ý nghĩa ngữ nghĩa" in markdown
    assert "ContextualParagraphWindowChunker" in markdown
    assert len(summary["queries"]) == 5
```

- [ ] **Step 2: Chạy test và xác nhận runner chưa hoàn chỉnh**

Run: `python -m pytest tests/test_tritue_solution.py -k rendered_mock_benchmark -v`
Expected: import/attribute failure cho runner hoặc renderer.

- [ ] **Step 3: Triển khai benchmark summary**

Summary chứa embedder label, chunk config, tổng chunk, avg length, từng query với top-3, rank đầu tiên relevant, top-3 relevance và filter đã dùng. Không dùng gold answer để tạo câu trả lời giả.

- [ ] **Step 4: Triển khai Markdown renderer và CLI**

CLI mặc định khởi tạo `LocalEmbedder`; lỗi dependency/model in hướng dẫn `pip install -r requirements-local.txt` và trả exit code khác 0. `--mock` dùng `_mock_embed`. `--output` chỉ ghi file được chỉ định; mặc định in stdout.

- [ ] **Step 5: Chạy smoke benchmark mock và ghi file bàn giao**

Run: `python -m src.TriTue.group_benchmark --mock --output src/TriTue/GROUP_CONTRIBUTION.md`
Expected: file có thống kê chunk, bảng năm query, top-3 relevance, failure case và cảnh báo mock.

---

### Task 4: Xác minh và bàn giao

**Files:**
- Modify: `src/TriTue/README.md`
- Verify only: `report/REPORT_NHOM.md`

**Interfaces:**
- Documents: lệnh test, benchmark local, benchmark mock và file gửi nhóm trưởng.

- [ ] **Step 1: Cập nhật README cá nhân**

Thêm lệnh:

```powershell
python -m pip install -r requirements-local.txt
python -m src.TriTue.group_benchmark --output src/TriTue/GROUP_CONTRIBUTION.md
```

Ghi rõ `REPORT_NHOM.md` thuộc nhóm trưởng và không được runner sửa.

- [ ] **Step 2: Chạy toàn bộ test**

Run: `$env:LAB_SOLUTION_PACKAGE='src.TriTue'; python -m pytest tests/ -v`
Expected: 42 test gốc và toàn bộ test bổ sung PASS.

- [ ] **Step 3: Kiểm tra chất lượng thay đổi**

Run: `python -m compileall -q src/TriTue`
Run: `rg -n "TODO|NotImplementedError" src/TriTue -g "*.py"`
Run: `git diff --check`
Expected: compile exit 0, không còn marker chưa triển khai, diff sạch.

- [ ] **Step 4: Chứng minh báo cáo nhóm không bị sửa**

Run: `git diff ec70eec -- report/REPORT_NHOM.md`
Expected: không có output.

- [ ] **Step 5: Commit implementation**

```powershell
git add src/TriTue tests/test_tritue_solution.py docs/superpowers/plans/2026-08-03-tritue-contextual-paragraph-chunker.md
git commit -m "feat: add TriTue contextual paragraph benchmark"
```
