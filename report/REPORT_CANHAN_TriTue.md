# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Tri Tuệ (cần xác nhận cách ghi đúng theo danh sách lớp)

**Nhóm:** Cần bổ sung tên nhóm

**Ngày:** 2026-08-03

**Nhánh mã nguồn:** `TriTue`

**Package cá nhân:** `src.TriTue`

> Báo cáo này hoàn thành phần lập trình và chạy thử bằng corpus khởi động K4. Trước khi nộp, cần thay kết quả ở Phần 5 bằng cùng corpus 5–10 tài liệu và cùng năm câu hỏi mà nhóm đã thống nhất.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Hai embedding có cosine similarity cao khi chúng hướng gần giống nhau trong không gian vector. Với text embedding có chất lượng, điều này thường biểu thị hai đoạn văn có ý nghĩa hoặc ngữ cảnh gần nhau dù cách dùng từ không hoàn toàn giống nhau.

**Ví dụ có độ tương tự cao:**

- Câu A: “Tôi muốn trả lại sản phẩm bị lỗi.”
- Câu B: “Hướng dẫn đổi trả hàng không đúng mô tả.”
- Tại sao tương đồng: Cả hai cùng nói về nhu cầu đổi trả do sản phẩm có vấn đề.

**Ví dụ có độ tương tự thấp:**

- Câu A: “Khách hàng gửi yêu cầu hoàn tiền.”
- Câu B: “Hôm nay thời tiết có mưa.”
- Tại sao khác: Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**

Cosine similarity tập trung vào hướng của vector nên ít bị ảnh hưởng bởi độ lớn, trong khi Euclidean distance thay đổi theo cả hướng lẫn độ lớn. Hướng vector thường phản ánh quan hệ ngữ nghĩa phù hợp hơn, đặc biệt khi các embedding đã được chuẩn hóa.

### Bài toán Chunking (Bài tập 1.2)

Với `document_length=10,000`, `chunk_size=500`, `overlap=50`:

```text
step = 500 - 50 = 450
chunk_count = ceil((10,000 - 50) / 450)
            = ceil(9,950 / 450)
            = ceil(22.111...)
            = 23 chunks
```

Nếu `overlap=100`:

```text
step = 500 - 100 = 400
chunk_count = ceil((10,000 - 100) / 400)
            = ceil(9,900 / 400)
            = ceil(24.75)
            = 25 chunks
```

Overlap tăng làm bước trượt nhỏ hơn nên số chunk tăng từ 23 lên 25. Overlap lớn hơn giúp thông tin nằm sát ranh giới không bị mất ngữ cảnh, nhưng làm tăng dung lượng lưu trữ và chi phí embedding/search.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ

**`SentenceChunker.chunk`:**

Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\r?\n+)` để nhận diện khoảng trắng hoặc xuống dòng sau dấu `.`, `!`, `?`. Các câu được chuẩn hóa khoảng trắng rồi gom tối đa theo `max_sentences_per_chunk`; text rỗng trả `[]` và tham số nhỏ hơn 1 được nâng lên 1.

**`RecursiveChunker.chunk` / `_split`:**

Thuật toán thử separator theo thứ tự `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là chuỗi rỗng. Base case là đoạn rỗng hoặc đoạn không vượt `chunk_size`; nếu hết separator mà đoạn vẫn dài, hàm cắt cứng để bảo đảm kết thúc và không bỏ mất nội dung.

**`compute_similarity` và comparator:**

Cosine similarity được tính bằng tích vô hướng chia cho tích hai norm; vector zero trả `0.0`, còn hai vector lệch số chiều gây `ValueError` để tránh `zip` âm thầm cắt dữ liệu. Comparator chạy đủ ba chiến lược và trả số chunk, độ dài trung bình và danh sách chunk.

### Lớp EmbeddingStore

**`add_documents` + `search`:**

Mỗi `Document` được chuyển thành record có ID nội bộ duy nhất, content, bản sao metadata, `doc_id` và embedding. Backend mặc định lưu trong bộ nhớ; nếu ChromaDB có sẵn thì tạo collection cosine riêng. Query được embedding một lần, chấm điểm bằng dot product và sắp xếp giảm dần.

**`search_with_filter` + `delete_document`:**

Metadata filter được áp dụng trước khi tính similarity để giảm nhiễu và tránh xếp hạng tài liệu ngoài phạm vi. `delete_document` xóa tất cả chunk có cùng `metadata['doc_id']` và trả `False` nếu không có record nào phù hợp.

### Tác tử KnowledgeBaseAgent

**`answer`:**

Agent gọi `store.search()`, đánh số các chunk theo thứ hạng và đưa content cùng nguồn vào mục `NGỮ CẢNH`. Prompt yêu cầu LLM chỉ trả lời từ ngữ cảnh, không bịa dữ kiện và nói rõ khi thông tin không đủ; câu hỏi được đặt trong mục riêng để phân biệt với evidence.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Lệnh đã chạy trên Python 3.13.7 trong môi trường hiện có:

```powershell
$env:LAB_SOLUTION_PACKAGE='src.TriTue'
python -m pytest tests/ -v
```

Kết quả tóm tắt:

```text
collected 68 items
68 passed in 0.54s
```

- Bộ test chính thức trong `tests/test_solution.py`: **42/42 pass**.
- Test bổ sung trong `tests/test_tritue_solution.py`: **26/26 pass**.
- Tổng: **68/68 pass**.
- Trước khi nộp nên chạy lại cùng lệnh bằng Python 3.11 đúng phiên bản chuẩn của lab.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các điểm dưới đây dùng `_mock_embed`. Tôi quy ước điểm `>= 0.5` là “cao” chỉ để đối chiếu bảng; mock embedder dựa trên hash nên không thể dùng để đánh giá ngữ nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Tôi muốn trả lại sản phẩm bị lỗi. | Hướng dẫn đổi trả hàng không đúng mô tả. | cao | 0.138373 | Không |
| 2 | Người bán phải mô tả sản phẩm chính xác. | Thông tin đăng bán cần đúng với tình trạng hàng. | cao | -0.071941 | Không |
| 3 | Khách hàng gửi yêu cầu hoàn tiền. | Hôm nay thời tiết có mưa. | thấp | -0.080600 | Có |
| 4 | Chính sách giao hàng áp dụng toàn quốc. | Quy định thanh toán bằng thẻ tín dụng. | thấp | 0.033635 | Có |
| 5 | Không được đăng bán sản phẩm bị cấm. | Hàng hóa thuộc danh mục cấm phải bị gỡ khỏi sàn. | cao | -0.020978 | Không |

**Kết quả bất ngờ nhất và phản ngẫm:**

Cặp 2 và cặp 5 gần nhau rõ ràng về nghĩa nhưng nhận điểm âm. Đây không phải bằng chứng rằng cosine similarity không hiệu quả; nó cho thấy `_mock_embed` sinh vector xác định từ hash của cả chuỗi và gần như ngẫu nhiên về mặt ngữ nghĩa. Muốn đánh giá tiếng Việt đúng mục đích bài, cần chạy lại với `LocalEmbedder` đa ngữ.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Phạm vi chạy thử

Kết quả dưới đây dùng hai tài liệu khởi động trong `data/k4_ecommerce/`, `RecursiveChunker(chunk_size=500)` và `_mock_embed`. Hai tài liệu tạo thành ba chunk. Agent dùng một hàm trích xuất trung lập: chọn câu trong đúng tập chunk đã truy xuất có nhiều token chung nhất với câu hỏi; hàm này không được truy cập gold answer. Đây là kiểm tra kỹ thuật cho pipeline cá nhân, chưa phải benchmark nhóm cuối vì đề yêu cầu corpus 5–10 tài liệu nguồn thật.

| # | Câu hỏi | Top-1 chunk truy xuất được | Score | Có liên quan không? | Câu trả lời của Agent |
|---|---|---|---:|---|---|
| 1 | Khi hàng bị lỗi hoặc không đúng mô tả, yêu cầu đổi trả cần kèm gì? | Chính sách đổi trả (`k4-returns-policy`) | 0.169408 | Có | Yêu cầu phải kèm bằng chứng phù hợp khi hàng bị lỗi hoặc không đúng mô tả. |
| 2 | Người bán có trách nhiệm gì khi nhận yêu cầu đổi trả? | Chính sách đổi trả (`k4-returns-policy`) | 0.077065 | Có, nhưng câu trả lời lệch ý | Người mua cần gửi yêu cầu đổi trả trong thời hạn được nêu trên trang sản phẩm hoặc chính sách của sàn. |
| 3 | Thông tin nào về sản phẩm phải được người bán cung cấp chính xác? | Chính sách đổi trả (`k4-returns-policy`) | 0.090975 | Top-1: Không; top-3: Có | Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác, gồm giá, mô tả và tình trạng hàng. |
| 4 | Sản phẩm bị hạn chế hoặc bị cấm có được đăng bán không? | Quy định đăng bán (`k4-seller-listing`) | 0.029955 | Có | Sản phẩm bị hạn chế hoặc bị cấm không được đăng bán. |
| 5 | Người bán cần tuân thủ điều gì khi đăng bán sản phẩm? | Quy định đăng bán (`k4-seller-listing`), lọc `customer_role=seller` | 0.000779 | Có, câu trả lời thiếu một ý | Sản phẩm bị hạn chế hoặc bị cấm không được đăng bán. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5/5**.

Kết quả 5/5 cần được hiểu thận trọng: corpus chỉ có ba chunk nên top-3 gần như luôn chứa toàn bộ dữ liệu. Top-1 đúng tài liệu 4/5, nhưng score rất thấp và câu 2 vẫn tạo câu trả lời sai trọng tâm; điều này cho thấy mock embedding và bộ trích xuất đơn giản không đủ để đánh giá chất lượng ngữ nghĩa. Metadata filter ở câu 5 loại bỏ tài liệu dành cho người mua và đưa đúng tài liệu người bán lên top-1, dù câu trả lời mới nêu một trong hai nghĩa vụ.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác:**

Phần này cần cập nhật sau buổi demo và so sánh thật với các thành viên. Khi thảo luận, tôi sẽ tập trung ghi lại chiến lược chunking/metadata nào cải thiện top-1, câu hỏi nào chiến lược của tôi thất bại và nguyên nhân dựa trên evidence thay vì chỉ so sánh score.

---

## Tự đánh giá phần cá nhân

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận của tôi | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 7 / 10 — chờ corpus/câu hỏi chung của nhóm |
| **Tổng phần cá nhân hiện tại** | **57 / 60** |

## Các mục phải cập nhật trước khi nộp

1. Xác nhận họ tên và điền tên nhóm.
2. Thay corpus khởi động bằng 5–10 tài liệu công khai có metadata bắt buộc.
3. Thay năm query mẫu bằng đúng năm query/gold answer chung của nhóm.
4. Chạy retrieval với `EMBEDDING_PROVIDER=local` và cập nhật bảng Phần 4–5.
5. Bổ sung bài học thật sau khi so sánh với thành viên khác.
