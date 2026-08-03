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
> Chính sách vận hành sàn TMĐT Shopee dành cho người mua và người bán: đổi trả/hoàn tiền, vận chuyển, thanh toán, điều kiện đăng bán sản phẩm, và bảo mật/quyền riêng tư — 6 tài liệu chính thức từ `help.shopee.vn`.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền | [help.shopee.vn/.../77251](https://help.shopee.vn/portal/4/article/77251) | 2026-08-03 / not-stated (nội dung nêu hiệu lực 11/3/2026) | 19.410 | `customer_role: buyer`, `category: returns`, `language: vi` |
| 2 | Chính sách vận chuyển Shopee | [help.shopee.vn/.../77250](https://help.shopee.vn/portal/4/article/77250-CH%C3%8DNH-S%C3%81CH-V%E1%BA%ACN-CHUY%E1%BB%82N-SHOPEE) | 2026-08-03 / not-stated (nội dung nêu đăng tải 20/3/2026) | 24.370 | `customer_role: both`, `category: shipping`, `language: vi` |
| 3 | Phương thức thanh toán trên Shopee | [help.shopee.vn/.../79198](https://help.shopee.vn/portal/4/article/79198-%5BTh%C3%A0nh-vi%C3%AAn-m%E1%BB%9Bi%5D-Shopee-hi%E1%BB%87n-%C4%91ang-c%C3%B3-nh%E1%BB%AFng-ph%C6%B0%C6%A1ng-th%E1%BB%A9c-thanh-to%C3%A1n-n%C3%A0o) | 2026-08-03 / not-stated | 5.817 | `customer_role: buyer`, `category: payment`, `language: vi` |
| 4 | Quy định về đăng bán sản phẩm trên Shopee | [help.shopee.vn/.../77246](https://help.shopee.vn/portal/4/article/77246-QUY-%C4%90%E1%BB%8ANH-V%E1%BB%80-%C4%90%C4%82NG-B%C3%81N-S%E1%BA%A2N-PH%E1%BA%A8M-TR%C3%8AN-SHOPEE) | 2026-08-03 / not-stated (nội dung nêu công bố 14/8/2024) | 21.315 | `customer_role: seller`, `category: seller-terms`, `language: vi` |
| 5 | Chính sách bảo mật | [help.shopee.vn/.../77244](https://help.shopee.vn/portal/4/article/77244-CH%C3%8DNH-S%C3%81CH-B%E1%BA%A2O-M%E1%BA%ACT) | 2026-08-03 / not-stated (nội dung nêu cập nhật 04/6/2026) | 42.934 | `customer_role: both`, `category: privacy`, `language: vi` |
| 6 | Quy chế hoạt động sàn TMĐT Shopee.vn | [help.shopee.vn/.../77245](https://help.shopee.vn/portal/4/article/77245) | 2026-08-03 / not-stated (nội dung nêu cập nhật 03/01/2025) | 77.625 | `customer_role: both`, `category: general-terms`, `language: vi` |

> `document_version` ghi `not-stated` vì trang Trung tâm trợ giúp Shopee không có số phiên bản riêng biệt — mỗi tài liệu tự nêu ngày cập nhật/hiệu lực trong nội dung (đã ghi chú ở cột trên) để phục vụ truy vết.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ. (Lấy từ Trung tâm trợ giúp công khai của Shopee qua `scripts/fetch_public_pages.py`, có kiểm tra `robots.txt`.)
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | enum (`buyer`/`seller`/`both`) | `seller` | Bắt buộc theo K4 — cho phép `search_with_filter()` thu hẹp kết quả về đúng đối tượng hỏi (vd. câu hỏi của người bán không nên trả về chính sách chỉ dành cho người mua). |
| `category` | string | `returns`, `shipping`, `payment`, `seller-terms`, `privacy`, `general-terms` | Lọc theo chủ đề cụ thể khi câu hỏi rõ ràng thuộc 1 mảng chính sách, giảm nhiễu từ các tài liệu dài không liên quan. |
| `language` | enum (`vi`) | `vi` | Dự phòng cho corpus đa ngôn ngữ trong tương lai; hiện tại toàn bộ corpus tiếng Việt nên chưa dùng để lọc. |
| `source_url` + `retrieved_at` | string / date | `https://help.shopee.vn/...`, `2026-08-03` | Truy vết nguồn gốc câu trả lời (grounding) — bắt buộc theo `K4_VARIANT.md`, không dùng để lọc nhưng hiển thị kèm câu trả lời để kiểm chứng. |
| `doc_id` | string | `shopee-seller-listing-rules` | Gắn lên từng chunk khi ingest để `delete_document()` và truy vết "chunk này thuộc tài liệu nào" hoạt động đúng. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(body, chunk_size=500)` trên 3 tài liệu (dùng `_mock_embed`, chỉ để so sánh cấu trúc chunk — không dùng để kết luận chất lượng ngữ nghĩa):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| shopee-returns-refund (19.410 ký tự) | FixedSizeChunker (`fixed_size`) | 39 | 497,7 | Không — cắt cứng theo ký tự, thường vỡ giữa từ/câu (vd. chunk[1] bắt đầu bằng `"ùng để chỉ..."`, bị cắt ngay giữa từ "dùng"). |
| shopee-returns-refund | SentenceChunker (`by_sentences`) | 47 | 410,1 | Có — luôn bắt đầu/kết thúc ở ranh giới câu, dễ đọc độc lập. |
| shopee-returns-refund | RecursiveChunker (`recursive`) | 60 | 321,6 | Có — ưu tiên cắt tại `\n\n`/`. `, không vỡ từ; chunk nhỏ hơn 2 chiến lược kia do văn bản có nhiều đoạn ngắn. |
| shopee-payment-methods (5.817 ký tự) | FixedSizeChunker | 12 | 484,8 | Không — tương tự trên, cắt giữa cụm từ ("ShopeePay và tiến hành..." bị cắt mất phần đầu). |
| shopee-payment-methods | SentenceChunker | 8 | 725,8 | Trung bình — bắt đầu ở ranh giới câu nhưng đôi khi gộp cả tiêu đề mục ("Thẻ Tín dụng/Ghi nợ") lẫn đoạn nội dung theo sau vào cùng 1 chunk, làm avg_length dao động mạnh. |
| shopee-payment-methods | RecursiveChunker | 16 | 361,7 | Có — kích thước ổn định hơn `by_sentences` trên cùng tài liệu, vẫn giữ câu trọn vẹn. |
| shopee-seller-listing-rules (21.315 ký tự) | FixedSizeChunker | 43 | 495,7 | Không — cắt giữa từ (vd. "ng bán sản phẩm..." bị mất "đă" của từ "đăng"). |
| shopee-seller-listing-rules | SentenceChunker | 78 | 270,5 | Trung bình — số chunk tăng mạnh (78) vì văn bản có nhiều câu ngắn dạng liệt kê (a, b, c…); một số chunk trộn lẫn tiêu đề mục La Mã/chữ cái với câu nội dung. |
| shopee-seller-listing-rules | RecursiveChunker | 52 | 408,0 | Có — cân bằng tốt nhất giữa việc giữ câu trọn vẹn và kích thước ổn định gần với `chunk_size=500` mục tiêu. |

**Nhận xét baseline:** `FixedSizeChunker` cho kích thước đồng đều nhất nhưng **luôn vỡ từ/câu** ở ranh giới chunk — rủi ro cao với văn bản chính sách nhiều điều khoản như corpus này, vì một điều kiện quan trọng (vd. ngưỡng %, số ngày) có thể bị cắt làm đôi. `SentenceChunker` giữ ngữ nghĩa câu tốt nhưng kích thước dao động mạnh theo độ dài câu gốc (270–726 ký tự tùy tài liệu) và không phân biệt được tiêu đề mục với nội dung. `RecursiveChunker` cân bằng tốt nhất trong 3 chiến lược có sẵn: vừa không vỡ từ, vừa bám sát `chunk_size` mục tiêu hơn — là lựa chọn khởi điểm hợp lý cho corpus chính sách nhiều điều/khoản này, dù còn thua chiến lược tách theo điều/khoản (heading-based) mà `K4_VARIANT.md` khuyến nghị.

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
>
> **Kết quả của Lương Đức Thắng** — 2 lần chạy: (a) `_mock_embed` (kiểm thử pipeline), (b) `FPTEmbedder` (`Vietnamese_Embedding`, FPT AI Marketplace, embedder thật) + `Llama-3.3-70B-Instruct` làm `llm_fn`. Bảng dưới dùng kết quả (b) làm chính; bảng sẽ cập nhật thêm cột khi các thành viên khác chạy xong chiến lược riêng. Chi tiết từng câu: `REPORT_CANHAN_LuongDucThang.md` — Phần 5.

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn trả hàng/hoàn tiền | Thắng: FixedSizeChunker(500,50) + `Vietnamese_Embedding` — **2/2 điểm** | Có (top-1, score 0.616) | Agent trả lời đúng và đầy đủ, khớp gold answer. Với mock embedder trước đó: sai hoàn toàn (0 điểm). |
| 2 | % diện tích ảnh sản phẩm (seller) | Thắng: FixedSizeChunker(500,50) + `Vietnamese_Embedding` + filter `customer_role=seller` — **2/2 điểm** | Có (top-1, score 0.502) | Đúng cả tài liệu lẫn đúng đoạn nội dung (khác với lần chạy mock — khi đó đúng doc chỉ nhờ filter, sai đoạn). |
| 3 | Khoảng giá trị Apple Pay | Thắng: FixedSizeChunker(500,50) + `Vietnamese_Embedding` — **1/2 điểm** | Có (top-1, score 0.602), chunk chứa đúng câu trả lời | **Retrieval đúng nhưng agent trả lời sai** (nhầm sang khoảng của Google Pay) — ca lỗi Grounding Quality, xem phân tích chi tiết ở `REPORT_CANHAN_LuongDucThang.md`. |
| 4 | Giới hạn kích thước/cân nặng Hỏa Tốc | Thắng: FixedSizeChunker(500,50) + `Vietnamese_Embedding` — **2/2 điểm** | Có (top-1, score 0.445) | Agent trả lời đúng và đầy đủ, khớp gold answer. |
| 5 | Phạm vi áp dụng chính sách bảo mật | Thắng: FixedSizeChunker(500,50) + `Vietnamese_Embedding` — **1/2 điểm** | Có (top-1, score 0.566), nhưng lệch đoạn (không trúng đúng mục 1.5) | Agent trả lời đúng nội dung tài liệu (về trẻ em dưới 13 tuổi) nhưng không nêu đúng ý gold answer ("cả Người Bán và Người Mua") — ca lỗi Retrieval Precision (chunk 500 ký tự làm câu trả lời ngắn ở mục 1.5 bị chunk khác "lấn át"). |

**Điểm của Thắng: 8/10** (2+2+1+2+1).

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có — rõ nhất ở Q2: `search_with_filter(metadata_filter={"customer_role": "seller"})` đảm bảo kết quả chỉ đến từ `shopee-seller-listing-rules` (tài liệu duy nhất có `customer_role=seller`), loại trừ hoàn toàn nhiễu từ 5 tài liệu còn lại. Điểm thú vị: khi dùng mock embedder, filter là **lý do duy nhất** Q2 tìm đúng tài liệu (bản thân embedding không giúp gì); khi dùng embedder thật, Q2 vẫn là 1 trong 2 câu đạt điểm tuyệt đối, cho thấy filter + embedding tốt **cộng hưởng** thay vì thay thế nhau — filter thu hẹp không gian tìm kiếm, embedding tốt đảm bảo tìm đúng đoạn trong không gian đã thu hẹp đó. Cần đồng đội chạy thêm để so sánh mức độ cải thiện này có nhất quán giữa các chiến lược chunking khác nhau không.

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
