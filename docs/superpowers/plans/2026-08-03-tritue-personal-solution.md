# TriTue Personal Lab Solution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng package cá nhân `src.TriTue` hoàn chỉnh, kiểm thử được độc lập và có báo cáo cá nhân đúng yêu cầu Lab 7.

**Architecture:** Package cá nhân sao chép các API nền đã cho sẵn và tự triển khai chunking, vector store và RAG agent, không phụ thuộc vào các TODO trong package `src` gốc. Bộ test lớp được tái sử dụng qua `LAB_SOLUTION_PACKAGE=src.TriTue`; một file test riêng bảo vệ các edge case và prompt contract.

**Tech Stack:** Python 3.11, standard library, pytest 9.1.1; ChromaDB/sentence-transformers/OpenAI là backend tùy chọn.

## Global Constraints

- Không sửa hành vi hoặc TODO trong các module khung trực tiếp dưới `src/`.
- API công khai của `src.TriTue` phải tương thích với những tên được import trong `tests/test_solution.py`.
- Backend mặc định là mock embedding xác định; đánh giá ngữ nghĩa chỉ có giá trị khi dùng local multilingual embedder.
- Không ghi test là đã pass nếu chưa có output thực tế từ Python 3.11.
- Giữ nguyên `report/REPORT_CANHAN.md`; lời giải cá nhân được lưu ở `report/REPORT_CANHAN_TriTue.md`.

---

### Task 1: Package nền và public API

**Files:**
- Create: `src/TriTue/models.py`
- Create: `src/TriTue/embeddings.py`
- Create: `src/TriTue/__init__.py`
- Test: `tests/test_tritue_solution.py`

**Interfaces:**
- Produces: `Document`, `MockEmbedder`, `LocalEmbedder`, `OpenAIEmbedder`, `_mock_embed` và các hằng model/provider.
- Produces: public imports cho các lớp/hàm ở những task sau.

- [ ] **Step 1: Viết test import package và API nền**

```python
from src.TriTue import Document, MockEmbedder


def test_tritue_document_keeps_metadata():
    doc = Document("d1", "content", {"lang": "vi"})
    assert doc.id == "d1"
    assert doc.metadata == {"lang": "vi"}


def test_tritue_mock_embedder_is_deterministic_and_normalized():
    embedder = MockEmbedder()
    first = embedder("xin chào")
    assert first == embedder("xin chào")
    assert len(first) == 64
    assert sum(value * value for value in first) == pytest.approx(1.0)
```

- [ ] **Step 2: Chạy test và xác nhận fail do package chưa tồn tại**

Run: `py -3.11 -m pytest tests/test_tritue_solution.py -v`
Expected: FAIL với `ModuleNotFoundError: No module named 'src.TriTue'`.

- [ ] **Step 3: Tạo models, embeddings và public exports tương thích package gốc**

`Document` là dataclass với `metadata=field(default_factory=dict)`. Mock embedder dùng MD5 và LCG giống package khung để các test lớp cho kết quả xác định. `__init__.py` import và liệt kê mọi tên public trong `__all__`; các import task sau được thêm khi module tương ứng tồn tại.

- [ ] **Step 4: Chạy test nền**

Run: `py -3.11 -m pytest tests/test_tritue_solution.py -v`
Expected: 2 tests PASS.

---

### Task 2: Các chiến lược chunking và cosine similarity

**Files:**
- Create: `src/TriTue/chunking.py`
- Modify: `src/TriTue/__init__.py`
- Modify: `tests/test_tritue_solution.py`

**Interfaces:**
- Produces: `FixedSizeChunker.chunk(text: str) -> list[str]`.
- Produces: `SentenceChunker.chunk(text: str) -> list[str]`.
- Produces: `RecursiveChunker.chunk(text: str) -> list[str]` và `_split(current_text, remaining_separators)`.
- Produces: `compute_similarity(vec_a: list[float], vec_b: list[float]) -> float`.
- Produces: `ChunkingStrategyComparator.compare(text: str, chunk_size: int = 200) -> dict`.

- [ ] **Step 1: Viết test edge case chunking và similarity**

```python
def test_sentence_chunker_handles_newline_boundaries_and_empty_text():
    chunker = SentenceChunker(max_sentences_per_chunk=2)
    assert chunker.chunk("") == []
    assert chunker.chunk("Một.\nHai! Ba?") == ["Một. Hai!", "Ba?"]


def test_recursive_chunker_preserves_text_when_separator_is_missing():
    chunks = RecursiveChunker(separators=["\n\n"], chunk_size=4).chunk("abcdefghij")
    assert chunks == ["abcd", "efgh", "ij"]


def test_similarity_rejects_mismatched_dimensions():
    with pytest.raises(ValueError, match="same dimension"):
        compute_similarity([1.0], [1.0, 2.0])
```

- [ ] **Step 2: Chạy các test mới và xác nhận fail**

Run: `py -3.11 -m pytest tests/test_tritue_solution.py -v`
Expected: FAIL do chưa có các API chunking.

- [ ] **Step 3: Triển khai tối thiểu các hành vi chunking**

`SentenceChunker` dùng `re.split(r"(?<=[.!?])(?:[ \t]+|\r?\n+)", text.strip())`, bỏ phần rỗng và ghép từng nhóm bằng một khoảng trắng. `RecursiveChunker` trả ngay đoạn ngắn; nếu không còn separator hoặc separator rỗng thì cắt cứng; nếu có separator thì ghép separator trở lại vào các đoạn trước khi đệ quy để không làm dính từ/câu và không làm mất nội dung. `compute_similarity` kiểm tra số chiều, norm bằng không, rồi áp dụng công thức cosine.

- [ ] **Step 4: Triển khai comparator**

Comparator dùng fixed overlap bằng `min(50, max(0, chunk_size // 5))`, sentence group mặc định 3 và recursive chunk size do caller truyền. Hàm thống kê trả chính xác ba key `fixed_size`, `by_sentences`, `recursive`; `avg_length=0.0` nếu không có chunk.

- [ ] **Step 5: Chạy test cá nhân và nhóm test chunking của lớp**

Run: `py -3.11 -m pytest tests/test_tritue_solution.py tests/test_solution.py -v`
Environment: `$env:LAB_SOLUTION_PACKAGE='src.TriTue'`
Expected: mọi test chunking/similarity/comparator PASS.

---

### Task 3: EmbeddingStore nhất quán giữa in-memory và ChromaDB

**Files:**
- Create: `src/TriTue/store.py`
- Modify: `src/TriTue/__init__.py`
- Modify: `tests/test_tritue_solution.py`

**Interfaces:**
- Consumes: `Document`, `_mock_embed`, `_dot`.
- Produces: `EmbeddingStore.add_documents(docs: list[Document]) -> None`.
- Produces: `search(query: str, top_k: int = 5) -> list[dict]`.
- Produces: `get_collection_size() -> int`.
- Produces: `search_with_filter(query: str, top_k: int = 3, metadata_filter: dict | None = None) -> list[dict]`.
- Produces: `delete_document(doc_id: str) -> bool`.

- [ ] **Step 1: Viết test record, filter nhiều trường và xóa nhiều chunk**

```python
def test_store_copies_metadata_and_adds_doc_id():
    metadata = {"lang": "vi"}
    store = EmbeddingStore("tritue_record", embedding_fn=_mock_embed)
    store.add_documents([Document("d1", "nội dung", metadata)])
    metadata["lang"] = "en"
    result = store.search("nội dung", top_k=1)[0]
    assert result["metadata"] == {"lang": "vi", "doc_id": "d1"}


def test_store_filters_before_search_and_deletes_all_chunks():
    store = EmbeddingStore("tritue_filter", embedding_fn=_mock_embed)
    store.add_documents([
        Document("d1-c0", "đổi trả một", {"doc_id": "d1", "lang": "vi", "category": "return"}),
        Document("d1-c1", "đổi trả hai", {"doc_id": "d1", "lang": "vi", "category": "return"}),
        Document("d2-c0", "shipping", {"doc_id": "d2", "lang": "en", "category": "shipping"}),
    ])
    results = store.search_with_filter("đổi trả", 5, {"lang": "vi", "category": "return"})
    assert len(results) == 2
    assert store.delete_document("d1") is True
    assert store.get_collection_size() == 1
    assert store.delete_document("d1") is False
```

- [ ] **Step 2: Chạy test store và xác nhận fail**

Run: `py -3.11 -m pytest tests/test_tritue_solution.py -v`
Expected: FAIL do `EmbeddingStore` chưa tồn tại.

- [ ] **Step 3: Triển khai normalized record và in-memory operations**

Record gồm `id`, `doc_id`, `content`, `metadata`, `embedding`. `metadata.setdefault("doc_id", doc.id)` trên bản sao dict. `_search_records` trả `id`, `content`, `metadata`, `score` và sắp xếp giảm dần. `top_k <= 0` trả `[]`. Filter yêu cầu mọi cặp key/value khớp chính xác trước khi search. Delete thay danh sách bằng các record không khớp và so sánh kích thước trước/sau.

- [ ] **Step 4: Thêm ChromaDB adapter tùy chọn**

Khởi tạo `chromadb.Client()` và `get_or_create_collection`. Add dùng IDs duy nhất, documents, embeddings và metadata scalar. Search chuyển `distance` cosine thành `score = 1.0 - distance`; filter truyền qua `where`. Delete lấy IDs theo `where={"doc_id": doc_id}` rồi xóa. Bất kỳ lỗi import/khởi tạo nào đều fallback về in-memory; lỗi thao tác sau khi backend đã khởi tạo không bị nuốt im lặng.

- [ ] **Step 5: Chạy test store cá nhân và test lớp**

Run: `$env:LAB_SOLUTION_PACKAGE='src.TriTue'; py -3.11 -m pytest tests/test_tritue_solution.py tests/test_solution.py -v`
Expected: mọi test store PASS.

---

### Task 4: KnowledgeBaseAgent và prompt grounding

**Files:**
- Create: `src/TriTue/agent.py`
- Modify: `src/TriTue/__init__.py`
- Modify: `tests/test_tritue_solution.py`

**Interfaces:**
- Consumes: `EmbeddingStore.search(question, top_k)`.
- Produces: `KnowledgeBaseAgent(store, llm_fn)` và `answer(question: str, top_k: int = 3) -> str`.

- [ ] **Step 1: Viết test prompt chứa context và câu hỏi**

```python
def test_agent_injects_ranked_context_and_question_into_prompt():
    store = EmbeddingStore("tritue_agent", embedding_fn=_mock_embed)
    store.add_documents([Document("d1", "Khách hàng có 7 ngày để đổi trả.", {})])
    captured = {}

    def fake_llm(prompt):
        captured["prompt"] = prompt
        return "7 ngày"

    answer = KnowledgeBaseAgent(store, fake_llm).answer("Được đổi trả trong bao lâu?", top_k=1)
    assert answer == "7 ngày"
    assert "Khách hàng có 7 ngày để đổi trả." in captured["prompt"]
    assert "Được đổi trả trong bao lâu?" in captured["prompt"]
```

- [ ] **Step 2: Chạy test agent và xác nhận fail**

Run: `py -3.11 -m pytest tests/test_tritue_solution.py -v`
Expected: FAIL do `KnowledgeBaseAgent` chưa tồn tại.

- [ ] **Step 3: Triển khai constructor và answer**

Constructor giữ nguyên `store` và `llm_fn`. `answer` tạo context đánh số từ kết quả `search`; nếu rỗng dùng câu `Không tìm thấy ngữ cảnh phù hợp trong kho tri thức.`. Prompt có chỉ dẫn không bịa thông tin, mục `NGỮ CẢNH`, mục `CÂU HỎI`, và yêu cầu trả lời ngắn gọn bằng ngôn ngữ của câu hỏi.

- [ ] **Step 4: Chạy toàn bộ test lớp bằng package cá nhân**

Run: `$env:LAB_SOLUTION_PACKAGE='src.TriTue'; py -3.11 -m pytest tests/ -v`
Expected: toàn bộ test PASS; số lượng lấy từ output thực tế.

---

### Task 5: Báo cáo cá nhân, benchmark mẫu và hướng dẫn chạy

**Files:**
- Create: `report/REPORT_CANHAN_TriTue.md`
- Create: `src/TriTue/__main__.py`
- Modify: `tests/test_tritue_solution.py`

**Interfaces:**
- Consumes: toàn bộ public API của `src.TriTue`.
- Produces: `py -3.11 -m src.TriTue` để chạy self-check, comparator và năm query K4 mẫu.

- [ ] **Step 1: Viết smoke test cho entrypoint helper**

```python
def test_personal_demo_defines_exactly_five_queries():
    from src.TriTue.__main__ import BENCHMARK_QUERIES
    assert len(BENCHMARK_QUERIES) == 5
    assert any(item.get("metadata_filter") for item in BENCHMARK_QUERIES)
```

- [ ] **Step 2: Tạo entrypoint benchmark package cá nhân**

Entrypoint tự đọc file K4 bằng parser front matter tương thích, dùng `RecursiveChunker(chunk_size=500)`, tạo `EmbeddingStore`, chạy comparator, năm cặp similarity và đúng năm query. Ít nhất một query gọi `search_with_filter`. Demo mặc định dùng `_mock_embed` và in cảnh báo rõ mock không đo chất lượng ngữ nghĩa.

- [ ] **Step 3: Chạy demo và lưu output thực tế**

Run: `py -3.11 -m src.TriTue`
Expected: self-check thành công, có thống kê ba chiến lược, năm similarity result và năm retrieval result.

- [ ] **Step 4: Hoàn thiện báo cáo cá nhân**

Điền warm-up, phép tính `ceil((10000-50)/(500-50)) = 23` và `ceil((10000-100)/(500-100)) = 25`, hướng tiếp cận khớp code, năm dự đoán, kết quả thực tế và năm query. Họ tên/nhóm để ở nhãn cần người học xác nhận. Phần học từ thành viên khác ghi là dữ liệu cần bổ sung sau buổi so sánh, không tự bịa.

- [ ] **Step 5: Xác minh cuối**

Run: `$env:LAB_SOLUTION_PACKAGE='src.TriTue'; py -3.11 -m pytest tests/ -v`
Run: `rg -n "TODO|NotImplementedError" src/TriTue`
Run: `git diff --check`
Expected: tests PASS; không có TODO/NotImplementedError trong package cá nhân; diff check sạch.

- [ ] **Step 6: Ghi hướng dẫn bàn giao**

Hướng dẫn phải có lệnh cài Python 3.11/requirements, lệnh test với biến môi trường PowerShell, lệnh demo, các file cần nộp, và danh sách trường báo cáo người học phải tự thay bằng dữ liệu thật của nhóm.
