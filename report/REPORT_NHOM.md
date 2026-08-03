# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** C3.2 (K4-DAY7)
**Thành viên & Phân công công việc:**
1. **Nguyễn Hoàng Vũ** — Lập trình mã nguồn cốt lõi gói `src` (`chunking.py`, `store.py`, `agent.py`), cấu trúc RAG Agent prompt và bộ lọc siêu dữ liệu (`SentenceChunker` 3 câu).
2. **Hoàng Thái Dương** (MSV: 2A202601518) — Đánh giá hiệu năng `SentenceChunker` (2 câu), tối ưu hóa tham số cắt ngắt để hạn chế token rác và phân tích chất lượng bộ lọc metadata.
3. **Lương Đức Thắng** — Thu thập (crawl) 6 tài liệu chính sách Shopee.vn, gán metadata YAML chuẩn K4, lập file `sources.csv`, tích hợp `FPTEmbedder` (`Vietnamese_Embedding` từ FPT AI Marketplace) & `Llama-3.3-70B-Instruct`.
4. **Lương Trí Tuệ** — Thử nghiệm chiến lược `RecursiveChunker`, bổ sung bộ kiểm thử mở rộng 26 unit tests (`tests/test_tritue_solution.py`), phân tích ảnh hưởng của cấu trúc tài liệu đến đệ quy.
5. **Phùng Đình Đạt** — Phân tích kỹ thuật regex tách câu nâng cao, kiểm thử biên dịch `python -m compileall`, tối ưu hóa ranh giới ngắt câu và phân tích toán học độ chồng chéo (overlap).

**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Bộ quy chế hoạt động, quy định đăng bán sản phẩm của người bán, phương thức thanh toán, chính sách vận chuyển, chính sách trả hàng hoàn tiền và chính sách bảo mật thông tin được thu thập chính thức từ sàn thương mại điện tử Shopee.vn.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy chế hoạt động sàn Shopee.vn | https://help.shopee.vn/portal/4/article/77245 | 2026-08-03 / not-stated | 77,625 | `doc_id: shopee-marketplace-terms`, `customer_role: both`, `category: general-terms`, `language: vi` |
| 2 | Phương thức thanh toán trên Shopee | https://help.shopee.vn/portal/4/article/79198-... | 2026-08-03 / not-stated | 5,817 | `doc_id: shopee-payment-methods`, `customer_role: buyer`, `category: payment`, `language: vi` |
| 3 | Chính sách bảo mật Shopee | https://help.shopee.vn/portal/4/article/77244-... | 2026-08-03 / not-stated | 42,934 | `doc_id: shopee-privacy-policy`, `customer_role: both`, `category: privacy`, `language: vi` |
| 4 | Chính sách trả hàng hoàn tiền Shopee | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 / not-stated | 19,410 | `doc_id: shopee-returns-refund`, `customer_role: buyer`, `category: returns`, `language: vi` |
| 5 | Quy định về đăng bán sản phẩm trên Shopee | https://help.shopee.vn/portal/4/article/77246-... | 2026-08-03 / not-stated | 21,315 | `doc_id: shopee-seller-listing-rules`, `customer_role: seller`, `category: seller-terms`, `language: vi` |
| 6 | Chính sách vận chuyển Shopee | https://help.shopee.vn/portal/4/article/77250-... | 2026-08-03 / not-stated | 24,370 | `doc_id: shopee-shipping-policy`, `customer_role: both`, `category: shipping`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `"shopee-returns-refund"` | Định danh duy nhất giúp quản lý vòng đời tài liệu và xóa chính xác các chunk liên quan. |
| `customer_role` | `str` | `"seller"` | Lọc đối tượng áp dụng (buyer/seller/both) để loại bỏ nhiễu từ tài liệu chéo vai trò. |
| `category` | `str` | `"payment"` | Phân loại danh mục nội dung giúp thu hẹp phạm vi tìm kiếm vector trước khi tính similarity. |
| `language` | `str` | `"vi"` | Định rõ ngôn ngữ văn bản để lựa chọn mô hình nhúng đa ngữ hoặc mô hình riêng cho tiếng Việt. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu chính sách trả hàng `shopee-returns-refund.md` (chunk_size=500):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-returns-refund.md` | FixedSizeChunker (`fixed_size`) | 44 | 495.91 | Cắt theo độ dài cố định, bị ngắt từ ở biên chunk nhưng kích thước rất đồng đều. |
| `shopee-returns-refund.md` | SentenceChunker (`by_sentences`) | 21 | 932.19 | Giữ trọn vẹn ngữ nghĩa từng câu, không đứt đoạn câu nhưng kích thước chunk khá lớn. |
| `shopee-returns-refund.md` | RecursiveChunker (`recursive`) | 54 | 362.26 | Tốt nhất về mặt cấu trúc (phân tách theo mục lục, đoạn văn rồi mới đến câu). |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Hoàng Vũ**
- **Công việc phụ trách:** Lập trình gói mã nguồn cốt lõi `src` (`chunking.py`, `store.py`, `agent.py`), thiết kế prompt RAG Agent và cơ chế lọc `search_with_filter`.
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn cho chủ đề này:** Phân chia văn bản theo ranh giới câu giúp câu văn luôn trọn vẹn ngữ nghĩa, tránh tình trạng câu bị cắt đôi ở điểm ranh giới chunk làm giảm khả năng hiểu của LLM.

**Thành viên 2 — Hoàng Thái Dương (MSV: 2A202601518)**
- **Công việc phụ trách:** Phân tích hiệu năng `SentenceChunker`, tối ưu hóa tham số gom nhóm câu và đánh giá bộ lọc metadata pre-filtering.
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=2`)
- **Mô tả & lý do chọn:** Giới hạn 2 câu mỗi chunk giúp thông tin trích xuất ngắn gọn và tập trung đúng trọng tâm câu hỏi, giảm số lượng token không cần thiết nạp vào prompt của LLM.

**Thành viên 3 — Lương Đức Thắng**
- **Công việc phụ trách:** Crawl toàn bộ 6 tài liệu Shopee.vn, gán YAML Front Matter, lập `sources.csv`, tích hợp mô hình nhúng tiếng Việt thật (`FPTEmbedder` - model `Vietnamese_Embedding` từ FPT AI Marketplace) và LLM `Llama-3.3-70B-Instruct`.
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=500, overlap=50`)
- **Mô tả & lý do chọn:** Thử nghiệm FixedSize làm baseline chuẩn đồng thời chứng minh rằng chất lượng mô hình nhúng thật quyết định phần lớn độ chính xác truy xuất (đưa score từ mức ngẫu nhiên 0.01 lên 0.5 - 0.9).

**Thành viên 4 — Lương Trí Tuệ**
- **Công việc phụ trách:** Thiết kế chiến lược `RecursiveChunker`, bổ sung bộ test suite 26 unit tests (`tests/test_tritue_solution.py`), phân tích ảnh hưởng của cấu trúc tài liệu đến chia đệ quy.
- **Loại chiến lược:** RecursiveChunker (`chunk_size=500`)
- **Mô tả & lý do chọn:** Phân tách đệ quy dựa trên thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]` giúp bảo tồn tự nhiên các khối tiêu đề và điều khoản phân tầng trong quy chế Shopee.

**Thành viên 5 — Phùng Đình Đạt**
- **Công việc phụ trách:** Phân tích kỹ thuật regex tách câu nâng cao `(?<=[.!?])(?: |\n)+`, kiểm thử biên dịch mã nguồn (`python -m compileall`), tối ưu hóa ranh giới ngắt câu và phân tích toán học độ chồng chéo (overlap).
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3` dùng regex nâng cao)
- **Mô tả & lý do chọn:** Cắt văn bản theo câu dựa trên regex tối ưu giúp tách chính xác các dấu ngắt câu tiếng Việt trong điều khoản Shopee mà không làm mất khoảng trắng biên hay dấu xuống dòng.

### So Sánh Giữa Các Thành Viên

| Thành viên | Phụ trách / Chiến lược | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Hoàng Vũ | Lập trình `src` / `SentenceChunker` (3 câu) | 8/10 | Câu văn trọn vẹn, không bị đứt đoạn | Kích thước chunk có thể hơi lớn |
| Hoàng Thái Dương | Đánh giá & Tối ưu / `SentenceChunker` (2 câu) | 8/10 | Ngắn gọn, tập trung đúng trọng tâm | Có thể chia tách 2 câu liên quan mật thiết |
| Lương Đức Thắng | Crawl dữ liệu & API Embedder / `FixedSizeChunker` + FPTEmbedder | 9/10 | Điểm tương đồng rất cao (0.5 - 0.9) nhờ Embedder thật | Bị ngắt từ ở ranh giới biên chunk |
| Lương Trí Tuệ | Extended Testing / `RecursiveChunker` | 9/10 | Giữ cấu trúc tiêu đề/đoạn văn phân tầng | Chunk ở biên cuối có thể quá nhỏ |
| Phùng Đình Đạt | Regex Testing / `SentenceChunker` (Regex) | 8/10 | Tách chính xác dấu câu tiếng Việt | Phụ thuộc vào quy tắc biểu thức chính quy |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược `RecursiveChunker` kết hợp với `SentenceChunker` cho kết quả tốt nhất. Các điều khoản Shopee có kết cấu tiêu đề phân tầng rõ rệt, việc phân tách đệ quy giúp bảo toàn sự liên kết giữa các mục lớn và mục nhỏ, trong khi việc cắt theo ranh giới câu đảm bảo thông tin không bị gãy đoạn ngữ nghĩa ở biên.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn người mua gửi yêu cầu trả hàng/hoàn tiền là bao lâu? | Trong vòng 15 ngày kể từ khi đơn hàng được cập nhật giao hàng thành công; riêng thực phẩm tươi sống/đông lạnh là 24 giờ. | `shopee-returns-refund` |
| 2 | Diện tích ảnh sản phẩm thật tối thiểu phải chiếm bao nhiêu %? | Tối thiểu 40% diện tích toàn ảnh. | `shopee-seller-listing-rules` (Lọc: seller) |
| 3 | Khoảng giá trị giao dịch tối thiểu và tối đa được Apple Pay hỗ trợ là bao nhiêu? | Tối thiểu từ 10.000 VNĐ và tối đa đến 25.000.000 VNĐ. | `shopee-payment-methods` (Lọc: buyer) |
| 4 | Kênh vận chuyển Hỏa Tốc của Shopee quy định giới hạn kích thước và cân nặng thế nào? | Cân nặng tối đa 30kg, kích thước tối đa 60x60x60cm. | `shopee-shipping-policy` |
| 5 | Chính sách bảo mật của Shopee thu thập những thông tin cá nhân nào của người dùng? | Họ tên, địa chỉ email, số điện thoại, ngày sinh, địa chỉ giao hàng và thông tin thanh toán (bao gồm cả Người Bán và Người Mua). | `shopee-privacy-policy` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Bao nhiêu ngày để yêu cầu trả hàng/hoàn tiền? | SentenceChunker / Recursive | Có (score: 0.6164) | Khớp chính xác thời hạn 15 ngày |
| 2 | % diện tích ảnh sản phẩm tối thiểu? *(filter seller)* | RecursiveChunker | Có (score: 0.5016) | Bộ lọc seller hoạt động hoàn hảo |
| 3 | Khoảng giá trị dùng được Apple Pay? *(filter buyer)* | SentenceChunker | Có (score: 0.6023) | Chunk trích xuất đúng nhưng LLM nhầm với Google Pay (120tr) |
| 4 | Giới hạn kích thước/cân nặng kênh Hỏa Tốc? | SentenceChunker | Có (score: 0.4449) | Tìm thấy đúng bảng giới hạn Hỏa Tốc |
| 5 | Chính sách bảo mật áp dụng đối tượng nào? | RecursiveChunker | Có (score: 0.5662) | Truy xuất đúng đoạn bảo mật thông tin |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có giúp ích rất nhiều, đặc biệt ở câu số 2 và 3. Việc lọc theo `customer_role` (`seller` hoặc `buyer`) loại bỏ hoàn toàn các tài liệu không liên quan (tránh lấy nhầm quy định người mua áp cho người bán), từ đó tăng độ chính xác tìm kiếm.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. Tác động rõ rệt của chất lượng Embedding: sử dụng mô hình thật (như `Vietnamese_Embedding` của FPT AI Marketplace) đưa điểm cosine từ ngẫu nhiên lên mức 0.5 - 0.9, phản ánh chính xác ngữ nghĩa tiếng Việt.
2. Tác dụng của metadata pre-filtering trong việc thu hẹp không gian tìm kiếm vector và giải quyết triệt để lỗi nhiễu thông tin chéo đối tượng.
3. Phân tích lỗi RAG: Retrieval đúng không đồng nghĩa với việc Agent sẽ trả lời đúng (LLM vẫn có thể bị ảo giác/nhầm lẫn số liệu kế cận như ca Apple Pay vs Google Pay).

**Bài học rút ra khi so sánh trong nhóm:**
> Lựa chọn chiến lược chunking phụ thuộc rất lớn vào định dạng tài liệu nguồn. Tài liệu cấu trúc phân tầng (như quy chế) cần Recursive, tài liệu phẳng/liền mạch nên dùng Sentence. Ngoài ra, tinh chỉnh tham số `chunk_size` và `overlap` đóng vai trò then chốt trong tối ưu hóa ngữ cảnh biên.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn bị dữ liệu có cấu trúc thẻ Markdown phân cấp H1/H2/H3 chặt chẽ hơn và viết thêm Custom Chunker định hướng tiêu đề (Heading-based Chunker) để tăng độ hội tụ thông tin trong từng chunk.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
