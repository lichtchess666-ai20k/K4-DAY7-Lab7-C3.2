# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** CẦN BỔ SUNG

**Nhóm:** CẦN BỔ SUNG

**Ngày:** CẦN BỔ SUNG

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau trong không gian vector. Với text embedding có chất lượng tốt, điều này thường cho biết hai đoạn văn có nội dung hoặc ý nghĩa tương đồng, dù cách dùng từ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể yêu cầu hoàn tiền trong vòng 30 ngày.
- Câu B: Chính sách đổi trả cho phép hoàn tiền trong 30 ngày.
- Tại sao tương đồng: Cả hai câu đều mô tả cùng một chính sách hoàn tiền và cùng thời hạn 30 ngày.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Khách hàng có thể thanh toán bằng thẻ tín dụng.
- Câu B: Trời hôm nay có mưa lớn ở Hà Nội.
- Tại sao khác: Hai câu thuộc hai chủ đề không liên quan, một câu nói về thanh toán và câu còn lại nói về thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Cosine similarity tập trung vào hướng của vector thay vì độ lớn, nên phù hợp hơn khi cần so sánh ý nghĩa của văn bản. Khoảng cách Euclid bị ảnh hưởng bởi độ lớn vector, trong khi độ lớn này không nhất thiết phản ánh mức độ tương đồng ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

Bước dịch giữa hai chunk là:

```text
step = chunk_size - overlap = 500 - 50 = 450
```

Số chunk là:

```text
1 + ceil((10,000 - 500) / 450)
= 1 + ceil(9,500 / 450)
= 1 + 22
= 23 chunks
```

**Đáp án:** 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

Khi overlap tăng lên 100, `step = 500 - 100 = 400`, nên số chunk là `1 + ceil(9,500 / 400) = 25`. Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa hai chunk và giảm nguy cơ một ý quan trọng bị cắt đôi, nhưng làm tăng số chunk, dung lượng lưu trữ và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` — hướng tiếp cận:**

Tôi dùng regex `(?<=[.!?])(?: |\n)+` để tách sau dấu `.`, `!`, `?` khi gặp khoảng trắng hoặc newline, sau đó loại bỏ khoảng trắng thừa và nhóm tối đa `max_sentences_per_chunk` câu. Hàm trả về danh sách rỗng nếu đầu vào chỉ chứa khoảng trắng và ép số câu mỗi chunk tối thiểu là 1 để tránh cấu hình không hợp lệ.

**`RecursiveChunker.chunk` / `_split` — hướng tiếp cận:**

Thuật toán thử các separator theo thứ tự ưu tiên `"\n\n"`, `"\n"`, `". "`, `" "`, rồi `""`, đồng thời ghép các phần nếu chunk vẫn không vượt quá `chunk_size`. Trường hợp cơ sở là đoạn hiện tại đã đủ ngắn; nếu hết separator hoặc gặp separator rỗng, hàm cắt trực tiếp theo số ký tự để luôn kết thúc và vẫn tạo được chunk.

### Lớp EmbeddingStore

**`add_documents` + `search` — hướng tiếp cận:**

Mỗi `Document` được chuẩn hóa thành một record gồm `doc_id`, `content`, bản sao `metadata` và embedding được tạo bởi hàm embedding đã inject. Khi search, tôi embed query, tính tích vô hướng giữa query embedding và từng record, sắp xếp score giảm dần rồi lấy tối đa `top_k` kết quả; backend mặc định của bài là `_mock_embed` và toàn bộ dữ liệu được lưu trong bộ nhớ.

**`search_with_filter` + `delete_document` — hướng tiếp cận:**

`search_with_filter` lọc metadata trước rồi mới tính score, nhờ đó chỉ xếp hạng các chunk thỏa mãn toàn bộ cặp key-value trong bộ lọc. `delete_document` tạo lại danh sách record, loại tất cả chunk có `metadata["doc_id"]` trùng với ID cần xóa, và trả về `True` nếu kích thước collection giảm, ngược lại trả về `False`.

### Tác tử KnowledgeBaseAgent

**`answer` — hướng tiếp cận:**

Hàm `answer` truy xuất `top_k` chunk liên quan nhất, ghép trường `content` bằng hai ký tự xuống dòng để tạo context, rồi tạo prompt gồm phần hướng dẫn, `Context`, `Question` và vị trí `Answer`. Prompt hoàn chỉnh được truyền vào `llm_fn`, giúp mô hình tạo câu trả lời dựa trên nội dung vừa truy xuất theo quy trình RAG.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

Lệnh kiểm thử:

```bash
pytest tests/ -v
```

Kết quả:

```text
============================= test session starts ==============================
platform linux -- Python 3.11.7, pytest-9.1.1
collected 42 items

tests/test_solution.py ..........................................        [100%]

============================== 42 passed in 0.05s ==============================
```

Ngoài ra, mã nguồn đã vượt qua kiểm tra biên dịch `python -m compileall -q src` và `git diff --check` không phát hiện lỗi whitespace.

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi dự đoán trước theo ý nghĩa của câu, sau đó tính score bằng `_mock_embed` mặc định và hàm `compute_similarity`. Để đánh dấu cột “Đúng?”, tôi dùng ngưỡng minh họa `score >= 0.5` là cao và `score < 0.5` là thấp.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-------|-------|---------|--------------|-------|
| 1 | Chính sách đổi trả cho phép hoàn tiền trong 30 ngày. | Khách hàng có thể yêu cầu hoàn tiền trong vòng 30 ngày. | cao | -0.0025 | Không |
| 2 | Đơn hàng sẽ được giao trong ba ngày làm việc. | Thời gian vận chuyển dự kiến là ba ngày làm việc. | cao | 0.1933 | Không |
| 3 | Người bán phải bảo vệ dữ liệu cá nhân của khách hàng. | Cửa hàng có trách nhiệm giữ an toàn thông tin người mua. | cao | -0.0324 | Không |
| 4 | Khách hàng có thể thanh toán bằng thẻ tín dụng. | Trời hôm nay có mưa lớn ở Hà Nội. | thấp | 0.0923 | Có |
| 5 | Sản phẩm lỗi được hỗ trợ đổi mới. | Cách trồng rau sạch trên ban công. | thấp | 0.0057 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Cặp 1 bất ngờ nhất vì hai câu gần như cùng nghĩa nhưng score lại là `-0.0025`. Kết quả này không cho thấy embedding ngữ nghĩa hoạt động sai; nó cho thấy `_mock_embed` của bài chỉ tạo vector xác định để kiểm thử luồng code và gần như ngẫu nhiên theo toàn chuỗi, vì vậy muốn đánh giá ý nghĩa thật cần dùng local multilingual embedder hoặc OpenAI embedder.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Phần này cần chạy đúng **5 câu hỏi đánh giá chung của nhóm** trên cùng corpus. Hiện nhóm chưa cung cấp 5 câu hỏi benchmark và corpus tương ứng, nên tôi chưa điền score hoặc tự tạo kết quả giả.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-----------------|--------------------------------------|------------|----------------------------------|---------------------------------|
| 1 | CẦN BỔ SUNG TỪ NHÓM | Chưa chạy | Chưa có | Chưa đánh giá | Chưa chạy |
| 2 | CẦN BỔ SUNG TỪ NHÓM | Chưa chạy | Chưa có | Chưa đánh giá | Chưa chạy |
| 3 | CẦN BỔ SUNG TỪ NHÓM | Chưa chạy | Chưa có | Chưa đánh giá | Chưa chạy |
| 4 | CẦN BỔ SUNG TỪ NHÓM | Chưa chạy | Chưa có | Chưa đánh giá | Chưa chạy |
| 5 | CẦN BỔ SUNG TỪ NHÓM | Chưa chạy | Chưa có | Chưa đánh giá | Chưa chạy |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** Chưa đánh giá / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

CẦN BỔ SUNG SAU BUỔI DEMO. Nội dung này phải phản ánh điều thực tế học được từ chiến lược chunking, metadata hoặc kết quả retrieval của thành viên khác, nên không thể kết luận trước khi nhóm chạy và so sánh benchmark.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | Chưa tự đánh giá / 10 |
| **Tổng phần cá nhân hiện đã hoàn thành** | **50 / 60** |

## Nội dung cần bổ sung trước khi nộp

1. Họ tên, tên nhóm và ngày nộp ở đầu báo cáo.
2. Năm câu hỏi benchmark chung của nhóm, kết quả top-1/top-3, score và câu trả lời Agent trong Mục 5.
3. Điều học được từ thành viên hoặc nhóm khác sau phần demo.
