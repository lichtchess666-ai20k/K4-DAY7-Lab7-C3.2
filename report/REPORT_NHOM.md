# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> *1 câu — ví dụ: đổi trả + điều kiện người bán.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.
>
> **Bản nháp do Claude soạn** dựa trên nội dung thật của 6 tài liệu Shopee trong `data/k4_ecommerce/` — nhóm review, chỉnh sửa/thay câu nếu cần rồi mới chốt để cả nhóm cùng chạy benchmark (Bài tập 3.4).

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng/hoàn tiền kể từ khi đơn hàng giao thành công? Trường hợp nào có thời hạn ngắn hơn? | 15 ngày kể từ khi đơn hàng được cập nhật giao hàng thành công; riêng thực phẩm tươi sống/đông lạnh chỉ có 24 giờ kể từ lúc giao thành công. | `shopee-returns-refund` — mục 3.2 |
| 2 | *(cần `metadata_filter={"customer_role": "seller"}`)* Theo quy định đăng bán sản phẩm, hình ảnh sản phẩm do người bán tự chụp phải chiếm tối thiểu bao nhiêu % diện tích ảnh? | Phải có ít nhất 1 hình ảnh thật do chính Người Bán tự chụp, trong đó diện tích sản phẩm thật phải chiếm tối thiểu 40% diện tích toàn ảnh. | `shopee-seller-listing-rules` — mục C.1.b |
| 3 | Đơn hàng thanh toán bằng Apple Pay trên Shopee cần có giá trị thanh toán cuối cùng trong khoảng nào? | Từ 10.000 VNĐ đến 25.000.000 VNĐ (đã gồm phí vận chuyển và các chi phí phát sinh khác, nếu có). | `shopee-payment-methods` — mục 7. Apple Pay |
| 4 | Kiện hàng vận chuyển theo hình thức Hỏa Tốc (Instant) bị giới hạn kích thước và cân nặng tối đa bao nhiêu? | Tối đa mỗi cạnh (Cao x Dài x Rộng) 60 x 60 x 60 cm, giới hạn cân nặng 30kg. | `shopee-shipping-policy` — bảng giới hạn khối lượng/kích thước, mục C.2.a |
| 5 | Chính sách bảo mật của Shopee áp dụng cho những đối tượng người dùng nào? | Áp dụng cho cả Người Bán và Người Mua đang sử dụng Dịch vụ, trừ khi có tuyên bố rõ ràng ngược lại. | `shopee-privacy-policy` — mục 1.5 |

**Ghi chú thiết kế bộ câu hỏi:**
- Đa dạng loại câu hỏi: thời hạn (Q1), điều kiện/ngưỡng số (Q2, Q3, Q4), phạm vi áp dụng (Q5) — không hỏi 5 câu cùng một dạng.
- Q2 bắt buộc dùng `search_with_filter(metadata_filter={"customer_role": "seller"})` để thỏa yêu cầu K4 (ít nhất 1 câu cần lọc metadata).
- Cả 5 gold answer đều trích trực tiếp từ nội dung tài liệu đã fetch (không bịa), có thể kiểm chứng lại bằng cách mở đúng file `.md` + mục đã ghi.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
