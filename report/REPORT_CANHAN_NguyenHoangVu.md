# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Hoàng Vũ
**Nhóm:** C3.2
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector biểu diễn văn bản hướng về cùng một phía trong không gian vector đa chiều (góc giữa chúng rất nhỏ). Điều này biểu thị rằng hai đoạn văn bản đó có mức độ tương đồng lớn về mặt phân bổ từ vựng và ngữ nghĩa, bất chấp sự khác biệt về độ dài của chúng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Hôm nay thời tiết thật đẹp và nhiều nắng."
- Câu B: "Thời tiết hôm nay rất tốt, trời có nắng đẹp."
- Tại sao tương đồng: Cả hai câu cùng diễn đạt một nội dung thời tiết tốt lành và chia sẻ nhiều từ khóa quan trọng đồng nghĩa ("thời tiết", "đẹp", "nắng").

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Cộng hòa Xã hội Chủ nghĩa Việt Nam."
- Câu B: "Trái đất quay quanh mặt trời."
- Tại sao khác: Hai câu đề cập đến hai lĩnh vực hoàn toàn độc lập (chính trị/địa danh và thiên văn học), không có mối tương quan về mặt ngữ nghĩa và không chia sẻ từ vựng chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Vì khoảng cách Euclid đo khoảng cách hình học tuyệt đối nên bị ảnh hưởng rất mạnh bởi độ dài của văn bản (văn bản dài hơn sẽ có vector dài hơn, dẫn đến khoảng cách lớn ngay cả khi chúng cùng chủ đề). Trong khi đó, độ tương tự cosine chuẩn hóa độ dài của vector và chỉ tập trung vào góc giữa chúng, giúp so sánh chính xác hướng ngữ nghĩa của tài liệu bất kể độ dài ngắn khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Áp dụng công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
> `số lượng chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23`
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, phép tính là `làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25`. Số lượng chunk tăng từ 23 lên 25.
> Ta muốn độ chồng chéo nhiều hơn để tránh việc mất mát ngữ cảnh biên của các chunk. Khi thông tin quan trọng bị cắt đôi ở điểm kết thúc của chunk này, overlap lớn sẽ giúp tái tạo trọn vẹn ngữ nghĩa ở chunk kế tiếp, từ đó cải thiện độ chính xác khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Chúng tôi sử dụng `re.split` với biểu thức chính quy `r'(\. |! |\? |\.\n)'` để tách văn bản thành các câu và giữ lại dấu câu biên nhờ dấu ngoặc tròn bắt giữ nhóm. Sau đó duyệt qua mảng kết quả, gộp các phần tử tương ứng để tái dựng câu đầy đủ. Cuối cùng, gom nhóm tối đa `max_sentences_per_chunk` câu lại, ghép nối bằng khoảng trắng và lọc sạch khoảng trống biên thừa.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy duyệt qua danh sách các dấu phân tách theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi văn bản nhỏ hơn `chunk_size` hoặc không còn dấu phân tách nào (hoặc gặp `""`), ta chia nhỏ trực tiếp theo độ dài `chunk_size`. Với đoạn dài hơn, ta phân tách bằng separator hiện tại, gọi đệ quy trên các phần con quá cỡ, rồi gộp các component lại sao cho tổng kích thước (kèm dấu phân tách) không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Trong `add_documents`, hệ thống hỗ trợ cả ChromaDB (sử dụng `collection.add` truyền ids, documents, embeddings, metadatas) và bộ nhớ trong (lưu bản ghi dict qua `self._make_record`). Trong `search`, in-memory tính toán dot product ngữ nghĩa của query vector vs tất cả record vector bằng hàm `_dot()`, xếp hạng giảm dần và lấy top_k kết quả. Đối với ChromaDB, gọi `collection.query` và chuẩn hóa điểm số tương tự bằng công thức `score = 1.0 - distance` (do HNWS đo cosine distance).

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc bằng metadata được thực hiện trước khi tìm kiếm tương tự (pre-filtering). Trong in-memory store, hệ thống lọc danh sách bản ghi thỏa mãn tất cả khóa-giá trị của `metadata_filter` trước khi chạy similarity search. Với ChromaDB, truyền dict lọc vào tham số `where`. Trong `delete_document`, in-memory loại bỏ tất cả các record có ID trùng khớp, bắt đầu bằng tiền tố `doc_id::chunk_`, hoặc có `metadata["doc_id"] == doc_id`. Với ChromaDB, truy quét IDs phù hợp rồi gọi `collection.delete`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Phương thức thực hiện truy xuất top-k chunks liên quan từ store. Tiếp theo, gom nội dung các chunk làm ngữ cảnh và cấu trúc prompt hướng dẫn LLM chỉ trả lời dựa trên ngữ cảnh cung cấp và trả về thông báo lỗi nếu thông tin thiếu hụt. Cuối cùng, gọi hàm LLM `llm_fn` với prompt đã chuẩn bị để tạo ra câu trả lời chuẩn xác nhất.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.1.1, pluggy-1.6.0 -- D:\VinUni-AI20K\K4-DAY7-Lab7-C3.2\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VinUni-AI20K\K4-DAY7-Lab7-C3.2
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Hôm nay thời tiết thật đẹp và nhiều nắng." | "Thời tiết hôm nay rất tốt, trời có nắng đẹp." | cao | 0.2322 | Không |
| 2 | "Quy trình trả hàng và hoàn tiền của Shopee." | "Hướng dẫn đổi trả sản phẩm và nhận lại tiền trên Shopee." | cao | 0.2896 | Không |
| 3 | "Học máy là một lĩnh vực của trí tuệ nhân tạo." | "Machine learning là một nhánh của AI." | cao | -0.1637 | Không |
| 4 | "Tôi muốn ăn phở gà Hà Nội vào buổi sáng." | "Phở bò Nam Định có hương vị rất đặc trưng." | trung bình | -0.0544 | Không |
| 5 | "Cộng hòa Xã hội Chủ nghĩa Việt Nam." | "Trái đất quay quanh mặt trời." | thấp | -0.1916 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là cặp số 3 ("Học máy là một lĩnh vực của trí tuệ nhân tạo" và "Machine learning là một nhánh của AI") trả về điểm âm (-0.1637) mặc dù hai câu đồng nghĩa. Điều này xảy ra do `MockEmbedder` chỉ băm ký tự (MD5) để sinh vector chứ không học ngữ nghĩa. Kết quả này chỉ ra rằng text embeddings ngữ nghĩa thật sự không thể chỉ dựa vào trùng khớp từ khóa hoặc hàm băm chuỗi, mà phải dùng mô hình mạng neural học sâu (như Transformer) huấn luyện trên văn bản lớn để hiểu được các từ đồng nghĩa và từ mượn khác ngôn ngữ.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn người mua gửi yêu cầu đổi trả hàng là bao lâu? | shopee-privacy-policy::chunk_33 (Về kỹ thuật, Shopee sử dụng Tính Năng Livestream YouTube...) | 0.4107 | Không | Người mua có thể gửi yêu cầu Trả hàng/Hoàn tiền trong thời hạn quy định (3 ngày hoặc 7 ngày đối với Shopee Mall) kể từ khi đơn hàng giao thành công. |
| 2 | Người bán cần làm gì khi có yêu cầu đổi trả từ người mua? | shopee-returns-refund::chunk_29 (Shopee sẽ thông báo đến Người Bán...) | 0.2385 | Có | Người bán cần phản hồi yêu cầu trả hàng từ người mua trong thời gian quy định (1-3 ngày), nếu không sẽ tự động hoàn tiền. |
| 3 | Người bán có được đăng bán sản phẩm bị cấm hay không? | shopee-seller-listing-rules::chunk_8 (Động vật và chế phẩm từ động vật...) | 0.4711 | Có | Người bán không được phép đăng bán các mặt hàng nằm trong danh sách cấm hoặc hạn chế của Shopee, nếu vi phạm tài khoản có thể bị phạt. |
| 4 | Trách nhiệm của người bán khi cung cấp thông tin sản phẩm là gì? | shopee-seller-listing-rules::chunk_58 (Giá sản phẩm phải được phân loại rõ ràng...) | 0.3601 | Có | Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác, đầy đủ bao gồm giá cả, mô tả, hình ảnh và tồn kho thực tế. |
| 5 | Yêu cầu đổi trả hàng cần đi kèm tài liệu gì để được chấp nhận? | shopee-returns-refund::chunk_7 (Người Mua có thể gửi yêu cầu trong vòng 15 ngày...) | 0.2036 | Một phần | Người mua cần cung cấp bằng chứng rõ ràng (như hình ảnh lỗi, video khui hộp, vận đơn) để Shopee xem xét yêu cầu trả hàng. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được từ các thành viên khác cách họ thiết kế dấu phân tách tùy biến dựa trên cấu trúc các tài liệu đặc thù tiếng Việt (ví dụ định dạng FAQ hoặc danh mục). Việc kết cấu cấu trúc tài liệu sạch sẽ giúp các chunker đệ quy cắt phân mảnh thông tin rất trọn vẹn và tăng rõ rệt chất lượng câu trả lời từ RAG Agent.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
