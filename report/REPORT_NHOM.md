# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** C3.2
**Thành viên:** Nguyễn Hoàng Vũ, Trần Minh Anh, Lê Duy Khánh
**Ngày:** 3/8/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Quy định đăng bán sản phẩm dành cho người bán và chính sách đổi trả hàng hóa dành cho người mua trên nền tảng thương mại điện tử.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách đổi trả | https://example.com/chinh-sach/doi-tra | 2026-08-02 / 2026.1 | 1069 | `doc_id: k4-returns-policy`, `customer_role: buyer`, `category: returns`, `language: vi` |
| 2 | Quy định đăng bán | https://example.com/nguoi-ban/dang-ban | 2026-08-02 / 2026.1 | 866 | `doc_id: k4-seller-listing`, `customer_role: seller`, `category: listing`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `"k4-returns-policy"` | Dùng định danh tài liệu gốc để nhóm hoặc xóa tất cả chunk của một tài liệu. |
| `customer_role` | `str` | `"buyer"` | Hỗ trợ lọc đối tượng (buyer/seller) nhằm giảm thiểu nhiễu và trả lời đúng trọng tâm. |
| `category` | `str` | `"returns"` | Phân loại nội dung để thu hẹp phạm vi tìm kiếm ngữ nghĩa theo danh mục. |
| `language` | `str` | `"vi"` | Định rõ ngôn ngữ của tài liệu để định hướng bộ nhúng và mô hình sinh phù hợp. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu chính sách đổi trả `returns-policy.md` (chunk_size=200):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `returns-policy.md` | FixedSizeChunker (`fixed_size`) | 5 | 192.40 | Không tốt (cắt ngang từ ở biên chunk như `retrieved_` và `h/doi-tra`) |
| `returns-policy.md` | SentenceChunker (`by_sentences`) | 3 | 292.33 | Rất tốt (giữ trọn vẹn ngữ nghĩa của từng câu) |
| `returns-policy.md` | RecursiveChunker (`recursive`) | 6 | 145.50 | Tốt (phân rã tự nhiên theo dấu ngắt dòng và đoạn văn) |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Hoàng Vũ**
- **Loại chiến lược:** SentenceChunker
- **Mô tả & lý do chọn cho chủ đề này:** Chọn cách chia nhỏ theo câu (`max_sentences_per_chunk=3`) để đảm bảo RAG agent nhận được thông tin ngữ cảnh đầy đủ, câu văn nguyên vẹn và không bị đứt đoạn ngữ nghĩa ở biên.
- **Code snippet (nếu custom):** Sử dụng `SentenceChunker` mặc định trong package `src`.

**Thành viên 2 — Trần Minh Anh**
- **Loại chiến lược:** RecursiveChunker
- **Mô tả & lý do chọn:** Sử dụng đệ quy phân tách theo cấp độ từ lớn đến nhỏ (`\n\n`, `\n`, `. `, ` `, `""`) giúp giữ nguyên khối tiêu đề và các đoạn văn độc lập trước khi ép theo kích thước tối đa. Điều này rất phù hợp với tài liệu điều khoản Shopee có nhiều đầu mục phân tầng rõ ràng.

**Thành viên 3 — Lê Duy Khánh**
- **Loại chiến lược:** FixedSizeChunker
- **Mô tả & lý do chọn:** Sử dụng FixedSize với kích thước chunk 300 và overlap 30 làm baseline so sánh, ưu điểm là cực kỳ đơn giản và tốc độ nhanh.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Hoàng Vũ | SentenceChunker | 9/10 | Ngữ cảnh câu luôn vẹn tròn, mạch lạc | Số lượng chunk lớn nếu tài liệu dài |
| Trần Minh Anh | RecursiveChunker | 9/10 | Giữ cấu trúc tài liệu rất tốt, linh hoạt | Có thể tạo ra các chunk quá nhỏ ở biên |
| Lê Duy Khánh | FixedSizeChunker | 6/10 | Dễ triển khai, phân bố đồng đều | Bị mất ngữ cảnh do cắt biên tùy tiện |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược `RecursiveChunker` kết hợp với `SentenceChunker` mang lại kết quả tốt nhất. Tài liệu TMĐT thường có cấu trúc rõ ràng (tiêu đề mục, danh sách gạch đầu dòng), việc tách đệ quy giúp giữ được sự phân cấp thông tin và hạn chế tối đa việc ngắt nửa câu hay nửa từ, tạo điều kiện tốt nhất cho LLM tổng hợp câu trả lời.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn người mua gửi yêu cầu đổi trả hàng là bao lâu? | Thời hạn được nêu trên trang sản phẩm hoặc theo chính sách của sàn. | `k4-returns-policy::chunk_1` |
| 2 | Người bán cần làm gì khi có yêu cầu đổi trả từ người mua? | Người bán có trách nhiệm phản hồi yêu cầu đổi trả theo quy trình của sàn. | `k4-returns-policy::chunk_1` |
| 3 | Người bán có được đăng bán sản phẩm bị cấm hay không? | Sản phẩm bị hạn chế hoặc bị cấm không được phép đăng bán trên sàn. | `k4-seller-listing::chunk_0` |
| 4 | Trách nhiệm của người bán khi cung cấp thông tin sản phẩm là gì? | Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác, bao gồm giá, mô tả và tình trạng hàng. | `k4-seller-listing::chunk_0` |
| 5 | Yêu cầu đổi trả hàng cần đi kèm tài liệu gì để được chấp nhận? | Yêu cầu đổi trả phải đi kèm bằng chứng phù hợp khi hàng bị lỗi hoặc không đúng mô tả. | `k4-returns-policy::chunk_0` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn người mua gửi yêu cầu đổi trả là bao lâu? | RecursiveChunker | Có (score: 0.0841) | Tìm đúng chunk trong returns-policy |
| 2 | Người bán cần làm gì khi nhận yêu cầu đổi trả? | SentenceChunker | Có (score: 0.0739) | Lọc hiệu quả theo customer_role: buyer |
| 3 | Người bán có được đăng sản phẩm cấm không? | RecursiveChunker | Có (score: 0.3181) | Kết quả score cao nhất nhờ khớp từ khóa cấm |
| 4 | Trách nhiệm người bán khi đăng thông tin? | SentenceChunker | Có (score: 0.0593) | Nhận diện chính xác thông tin đăng bán |
| 5 | Đổi trả hàng cần gửi kèm tài liệu gì? | RecursiveChunker | Có (score: 0.3008) | Khớp chính xác từ khóa bằng chứng/lỗi |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata cực kỳ hiệu quả, cụ thể ở các câu hỏi 2, 3 và 4. Việc giới hạn lọc theo `customer_role` (buyer hoặc seller) giúp loại bỏ nhiễu từ các tài liệu chéo (ví dụ tránh lấy nhầm quy trình đổi trả của buyer áp cho seller), từ đó giảm thiểu tối đa thông tin sai lệch nạp vào LLM.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. Sự khác biệt về chất lượng cắt văn bản ngữ nghĩa của Sentence/Recursive so với FixedSize.
2. Vai trò sống còn của pre-filtering bằng metadata trong hệ thống RAG quy mô lớn để tối ưu hóa không gian vector.
3. Sự hạn chế của MockEmbedder (băm MD5) so với embeddings ngữ nghĩa thực tế.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một tài liệu thô, việc chọn chiến lược chia nhỏ phù hợp quyết định mức độ mạch lạc thông tin nạp cho tác tử LLM. Cắt theo câu giúp giữ ngữ cảnh, trong khi cắt đệ quy giúp tối ưu hóa định dạng phân tầng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ thiết kế dữ liệu Markdown chuẩn hóa hơn ngay từ khâu thu thập (đầy đủ tiêu đề H2/H3 rõ ràng) để RecursiveChunker hoạt động tối đa công suất dựa trên cấu trúc thẻ tiêu đề đó.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
