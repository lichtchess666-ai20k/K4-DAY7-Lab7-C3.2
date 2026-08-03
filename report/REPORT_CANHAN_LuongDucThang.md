# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lương Đức Thắng
**Nhóm:** [C3.2]
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding trỏ gần như cùng hướng trong không gian nhiều chiều (góc giữa chúng gần 0°), bất kể độ dài vector — nghĩa là hai đoạn văn bản mang ý nghĩa/ngữ nghĩa gần giống nhau, dù cách diễn đạt câu chữ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Con mèo đang ngủ trên ghế sofa."
- Câu B: "Con mèo nằm ngủ trên chiếc ghế."
- Tại sao tương đồng: cùng chủ thể (con mèo), cùng hành động (ngủ), cùng bối cảnh (ghế) — chỉ khác từ ngữ diễn đạt, embedding thật (không phải mock) sẽ đặt hai câu này rất gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi thích lập trình Python vào buổi sáng."
- Câu B: "Hôm nay trời mưa rất to ở Hà Nội."
- Tại sao khác: chủ đề (lập trình vs. thời tiết), chủ thể và hành động hoàn toàn không liên quan — không có điểm chung về ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến *hướng* của vector, không bị ảnh hưởng bởi độ lớn (magnitude) — điều này quan trọng vì độ dài văn bản khác nhau có thể làm embedding "dài" hơn dù ngữ nghĩa không đổi. Euclidean distance lại nhạy với magnitude, nên hai câu cùng ý nghĩa nhưng độ dài khác nhau có thể bị tính là "xa nhau" một cách sai lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính:
> `số chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23`
> Đã kiểm chứng lại bằng cách chạy trực tiếp `FixedSizeChunker(chunk_size=500, overlap=50).chunk("a" * 10000)` → kết quả thực tế cũng ra đúng **23 chunks**.
>
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng lên: `làm_tròn_lên((10000-100)/(500-100)) = làm_tròn_lên(9900/400) = 25 chunks` (đã kiểm chứng bằng code, khớp kết quả thực tế). Tăng overlap làm bước nhảy (`chunk_size - overlap`) nhỏ lại nên cần nhiều chunk hơn để phủ hết văn bản. Lý do muốn overlap lớn hơn: tránh việc một câu/ý quan trọng bị cắt đúng ngay ranh giới giữa hai chunk — phần overlap giúp giữ ngữ cảnh liên tục qua các chunk, cải thiện chất lượng truy xuất (retrieval) dù phải đánh đổi bằng việc lưu trữ và tính embedding nhiều hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+` (lookbehind: tách ngay sau dấu `.`/`!`/`?` và theo sau là khoảng trắng) — tổng quát hơn yêu cầu gốc (chỉ ". ", "! ", "? ", ".\n") vì `\s+` bao trùm cả xuống dòng lẫn nhiều khoảng trắng liên tiếp. Sau khi tách câu, nhóm từng `max_sentences_per_chunk` câu liên tiếp rồi `" ".join()` lại. Edge case: text rỗng trả về `[]`; các câu rỗng sau `strip()` bị lọc bỏ để tránh chunk trống khi văn bản có khoảng trắng thừa.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Đệ quy thử lần lượt từng separator theo thứ tự ưu tiên (`\n\n` → `\n` → `. ` → ` ` → `""`). Base case: nếu đoạn text hiện tại đã `<= chunk_size` thì trả về nguyên vẹn (không cắt tiếp). Với mỗi separator, tách text thành các phần rồi ghép dần lại (dùng lại chính separator đó để nối) cho đến khi sắp vượt `chunk_size` thì chốt chunk hiện tại và bắt đầu chunk mới; nếu một phần đơn lẻ vẫn dài hơn `chunk_size`, gọi đệ quy `_split` với separator kế tiếp trong danh sách. Nếu hết separator mà văn bản vẫn dài (`remaining_separators` rỗng), fallback cắt cứng theo `chunk_size` để đảm bảo luôn có kết quả.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` embed toàn bộ `content` của từng `Document` (việc chia chunk đã được thực hiện trước đó ở bước ingest, `EmbeddingStore` chỉ lưu trữ), tạo record `{doc_id, content, metadata, embedding}` rồi append vào danh sách trong bộ nhớ `self._store`; nếu import được `chromadb`, đồng thời ghi thêm vào collection để có thể dùng persistence thật (bonus, không bắt buộc cho checkpoint). `search` embed câu truy vấn rồi tính **dot product** giữa vector truy vấn và từng embedding đã lưu — vì `MockEmbedder` đã chuẩn hóa vector về norm=1 nên dot product ở đây tương đương cosine similarity, sắp xếp giảm dần theo score và cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc **trước** theo metadata (dùng `all()` để khớp mọi cặp key-value trong `metadata_filter`) trên `self._store`, sau đó mới chạy hàm search nội bộ (`_search_records`) trên tập đã lọc — tránh tính embedding/similarity cho các bản ghi chắc chắn không khớp filter, giúp truy xuất chính xác hơn khi biết trước ngữ cảnh (ví dụ phòng ban, ngôn ngữ). `delete_document` duyệt `self._store`, giữ lại các record có `doc_id` khác id cần xóa, so sánh độ dài trước/sau để trả về `True`/`False` (đồng thời thử xóa trên ChromaDB nếu đang dùng, bọc trong `try/except` vì đây là thao tác best-effort).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k)` lấy các chunk liên quan nhất, nối nội dung (`content`) của các chunk bằng `"\n\n"` để tạo phần **Context**, dựng prompt dạng: hướng dẫn agent chỉ trả lời dựa trên context được cung cấp, kèm theo Context và Question, rồi gọi `llm_fn(prompt)` và trả về kết quả trực tiếp — giữ agent đơn giản (không tự parse/hậu xử lý output của LLM) để có thể cắm bất kỳ `llm_fn` nào (mock, OpenAI, v.v.) khi test.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
...
42 passed, 179 warnings in 1.56s

Tất cả các nhóm test đều PASSED:
- TestProjectStructure (2/2)
- TestClassBasedInterfaces (2/2)
- TestFixedSizeChunker (7/7)
- TestSentenceChunker (4/4)
- TestRecursiveChunker (4/4)
- TestEmbeddingStore (8/8)
- TestKnowledgeBaseAgent (2/2)
- TestComputeSimilarity (4/4)
- TestCompareChunkingStrategies (3/3)
- TestEmbeddingStoreSearchWithFilter (3/3)
- TestEmbeddingStoreDeleteDocument (3/3)
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Dùng `_mock_embed` (trình nhúng giả lập mặc định, chưa cài `sentence-transformers`/local embedder). Dự đoán được đưa ra dựa trên ngữ nghĩa thật của câu, **trước khi** chạy `compute_similarity()`.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Con mèo đang ngủ trên ghế sofa. | Con mèo nằm ngủ trên chiếc ghế. | cao | 0.0167 | ✗ (gần 0, không cao như kỳ vọng) |
| 2 | Chính sách đổi trả hàng trong 7 ngày. | Quy định hoàn tiền áp dụng trong vòng một tuần. | cao | -0.1566 | ✗ (ngược lại, ra âm) |
| 3 | Tôi thích lập trình Python vào buổi sáng. | Hôm nay trời mưa rất to ở Hà Nội. | thấp | 0.1338 | ✗ (cao nhất trong 5 cặp, dù chủ đề không liên quan) |
| 4 | Giao hàng miễn phí cho đơn từ 200.000đ. | Giao hàng miễn phí cho đơn từ 500.000đ. | cao | 0.0727 | ✗ (đúng dấu dương nhưng không cao rõ rệt) |
| 5 | Ngân hàng trung ương tăng lãi suất. | Con mèo đang ngủ trên ghế sofa. | thấp | -0.0096 | ✓ (gần 0/âm nhẹ, khớp dự đoán) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 3: hai câu hoàn toàn không liên quan về chủ đề ("lập trình Python" vs "trời mưa ở Hà Nội") lại có điểm cao nhất (0.1338) trong khi cặp 1 — gần như là một câu paraphrase của câu kia ("con mèo ngủ trên ghế") — lại chỉ đạt 0.0167, gần như không tương quan. Điều này minh chứng rõ cảnh báo trong README: `MockEmbedder` sinh vector từ **hash MD5 của chuỗi ký tự** (`hashlib.md5(text.encode())`) làm seed cho một bộ sinh số giả-ngẫu nhiên (LCG), hoàn toàn không mã hoá ngữ nghĩa — nó chỉ đảm bảo tính xác định (cùng input → cùng output) chứ không phản ánh việc hai câu có ý nghĩa gần nhau hay không. Bài học: **cosine similarity chỉ có ý nghĩa khi embedding model thực sự học được biểu diễn ngữ nghĩa** (như `sentence-transformers` hay OpenAI embeddings); mock embedder chỉ nên dùng để kiểm thử logic (đúng shape, đúng công thức toán), tuyệt đối không dùng để so sánh/kết luận chất lượng chunking hay retrieval tiếng Việt — đúng như lưu ý trong `README.md` và `exercises.md`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Chưa thực hiện được** — phần này phụ thuộc vào Bài tập 3.0–3.2 (Giai đoạn 2, nhóm): nhóm cần thống nhất bộ tài liệu chung và 5 câu hỏi đánh giá (`REPORT_NHOM.md`) trước khi mỗi thành viên có thể chạy benchmark cá nhân. Sẽ cập nhật bảng bên dưới ngay sau khi nhóm chốt xong 5 câu hỏi (Bài tập 3.4).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | *(chờ nhóm chốt câu hỏi)* | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5 *(chưa thực hiện)*

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(cập nhật sau buổi demo nhóm)*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 0 / 10 *(chờ Giai đoạn 2 nhóm)* |
| **Tổng phần cá nhân** | **50 / 60** |
