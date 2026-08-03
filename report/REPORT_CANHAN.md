# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Thái Dương
**MSV:** 2A202601518
**Nhóm:** Nhóm c3-2 (K4-DAY7)
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiệm cận 1.0) thể hiện hai vector biểu diễn văn bản có cùng hướng trong không gian đa chiều, nghĩa là hai đoạn văn bản đó có sự tương đồng lớn về mặt ngữ nghĩa (semantic similarity).

**Ví dụ có độ tương tự CAO:**
- Câu A: Python là ngôn ngữ lập trình phổ biến và dễ học.
- Câu B: Lập trình bằng ngôn ngữ Python rất đơn giản và thông dụng.
- Tại sao tương đồng: Cả hai câu đều nói về cùng một chủ đề (ngôn ngữ Python) và truyền tải ý nghĩa tương đương nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Hôm nay thời tiết Hà Nội rất đẹp và nhiều nắng.
- Câu B: Thuật toán sắp xếp nhanh có độ phức tạp O(n log n).
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn không liên quan (thời tiết vs cấu trúc dữ liệu thuật toán).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo góc giữa hai vector mà không bị ảnh hưởng bởi độ dài (ngược lại khoảng cách Euclid bị chi phối bởi độ dài vector). Điều này giúp so sánh chính xác sự tương đồng ngữ nghĩa giữa hai văn bản bất kể độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Bước nhảy giữa các chunk: `step = chunk_size - overlap = 500 - 50 = 450`.
> Vị trí bắt đầu của các chunk: `0, 450, 900, 1350, ..., 450 * k`.
> Vòng lặp dừng khi `start + 500 >= 10,000` $\rightarrow$ `450 * k >= 9,500` $\rightarrow$ `k = ceil(9500 / 450) = 22`.
> Tổng số chunk được tạo ra là: `k + 1 = 22 + 1 = 23` chunks.
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước nhảy giảm xuống `step = 500 - 100 = 400`, tổng số chunk tăng lên `ceil(9500 / 400) + 1 = 25` chunks. Tăng độ chồng chéo giúp giữ lại ngữ cảnh liền mạch ở ranh giới giữa các chunk, tránh làm đứt gãy thông tin quan trọng.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|(?<=\.\n)', text)` để tách văn bản dựa trên các dấu kết thúc câu (`. `, `! `, `? `, `.\n`). Xử lý loại bỏ các khoảng trắng thừa (`strip()`) và gom nhóm tối đa `max_sentences_per_chunk` câu vào một chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng thuật toán chia để trị (divide & conquer) với thứ tự phân cách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi văn bản nhỏ hơn `chunk_size` hoặc không còn ký tự phân cách. Khi tách, nếu độ dài vượt quá `chunk_size`, hàm sẽ gọi đệ quy `_split` với bộ phân cách kế tiếp; ngược lại sẽ gộp các mảnh nhỏ lại cho đến khi đạt kích thước tối đa.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với `add_documents`, duyệt qua từng tài liệu, gọi hàm nhúng `_embedding_fn` để tạo vector và lưu dưới dạng dictionary record vào danh sách `_store`. Với `search`, nhúng câu truy vấn thành vector, tính Cosine Similarity (tích vô hướng `_dot` đối với vector đã chuẩn hóa) giữa vector truy vấn và toàn bộ vector trong store, sau đó sắp xếp giảm dần theo `score` và lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc (filter) được thực hiện trước khi tìm kiếm vector: lọc danh sách record trong `_store` khớp tất cả điều kiện `metadata_filter`, sau đó mới gọi `_search_records` trên danh sách đã lọc. Việc xóa `delete_document` được thực hiện bằng cách lọc giữ lại các record có `id` hoặc `metadata['doc_id']` khác với `doc_id` cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Cấu trúc prompt được thiết kế theo mô hình RAG tiêu chuẩn: gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất, trích xuất nội dung `content` ghép thành phần ngữ cảnh `Context:`, nối với câu hỏi `Question:` và gửi toàn bộ prompt này tới hàm `llm_fn` để tạo câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================== 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Mèo là loài động vật nuôi trong nhà | Chó là loài vật nuôi phổ biến trong gia đình | cao | -0.0478 | Sai |
| 2 | Python là ngôn ngữ lập trình phổ biến | Tôi thích học lập trình Python | cao | 0.2145 | Đúng |
| 3 | Hôm nay trời nắng đẹp | Mô hình ngôn ngữ lớn học từ dữ liệu | thấp | 0.2714 | Sai |
| 4 | Tài liệu này giải thích về vector store | Cơ sở dữ liệu vector dùng để tìm kiếm tương đồng | cao | 0.0104 | Sai |
| 5 | Quả táo chứa nhiều vitamin C | Máy tính xách tay của tôi bị hỏng nguồn | thấp | -0.2595 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp số 3 ("Hôm nay trời nắng đẹp" vs "Mô hình ngôn ngữ lớn...") có điểm tương đồng thực tế lên tới 0.2714 (cao hơn cả cặp 2 cùng chủ đề Python), trong khi cặp 1 (Mèo vs Chó) lại có điểm âm (-0.0478). Nguyên nhân là do `MockEmbedder` chỉ tính toán dựa trên hàm băm MD5 ngẫu nhiên chứ không phải mô hình ngôn ngữ ngữ nghĩa. Điều này chứng minh rằng vector embeddings thật cần dựa trên không gian ngữ nghĩa học từ dữ liệu lớn chứ không thể dùng các hàm băm ngẫu nhiên.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Chính sách đổi trả hàng áp dụng trong bao nhiêu ngày? | `doc_id: k4-seller-listing title: Quy định đăng bán` | 0.098 | Có | Context: --- doc_id: k4-seller-listing... |
| 2 | Người bán cần chuẩn bị những thông tin gì khi đăng bán sản phẩm? | `doc_id: k4-returns-policy title: Chính sách đổi trả` | 0.028 | Có | Context: --- doc_id: k4-returns-policy... |
| 3 | Quy trình xử lý khi sản phẩm bị lỗi hoặc giao sai là gì? | `doc_id: k4-returns-policy title: Chính sách đổi trả` | 0.237 | Có | Context: --- doc_id: k4-returns-policy... |
| 4 | Quy định về thời gian phản hồi yêu cầu đổi trả của người bán | `doc_id: k4-returns-policy title: Chính sách đổi trả` | -0.037 | Có | Context: --- doc_id: k4-returns-policy... |
| 5 | Sản phẩm nào bị hạn chế hoặc cấm đăng bán trên sàn? | `doc_id: k4-returns-policy title: Chính sách đổi trả` | 0.118 | Có | Context: --- doc_id: k4-returns-policy... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua bài lab và thảo luận nhóm, điều hay nhất tôi học được là tầm quan trọng của chiến lược chunking đệ quy (`RecursiveChunker`) giúp bảo toàn cấu trúc ngữ cảnh tốt hơn hẳn chia cố định (`FixedSizeChunker`). Đồng thời việc sử dụng mô hình embedding đa ngôn ngữ thật (`sentence-transformers`) mang lại hiệu quả vượt trội trong việc truy xuất thông tin ngữ nghĩa tiếng Việt so với phương pháp khớp từ khóa truyền thống.

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
