# Đóng góp benchmark của TriTue

## Cấu hình

- Chunker: `ContextualParagraphWindowChunker`
- Tham số: `chunk_size=900`, `overlap_paragraphs=1`, `word_overlap=20`
- Embedding: `mock`
- Tổng số chunk: 322
- Độ dài chunk trung bình: 727.7 ký tự

> **Cảnh báo:** Đây là mock embedding xác định dùng để smoke test; điểm và thứ hạng không có ý nghĩa ngữ nghĩa.

## Kết quả retrieval top-3

| # | Metadata filter | Có chunk liên quan | Hạng đầu tiên | Top-1 nguồn | Score |
|---:|---|---|---:|---|---:|
| 1 | Không | Không | - | shopee-marketplace-terms | 0.3806 |
| 2 | {'customer_role': 'seller'} | Có | 2 | shopee-seller-listing-rules | 0.1975 |
| 3 | Không | Không | - | shopee-marketplace-terms | 0.3648 |
| 4 | Không | Không | - | shopee-shipping-policy | 0.3410 |
| 5 | Không | Không | - | shopee-seller-listing-rules | 0.3861 |

## Chi tiết bằng chứng truy xuất

### Câu 1

Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng/hoàn tiền kể từ khi đơn hàng giao thành công? Trường hợp nào có thời hạn ngắn hơn?

Expected document: `shopee-returns-refund`

- Hạng 1 — `shopee-marketplace-terms` — score `0.3806` — **không đủ bằng chứng**: 3. Chính sách giao nhận vận chuyển a. Khi phát sinh đơn đặt hàng mua hàng hóa của Người Mua, hệ thống Shopee sẽ chuyển thông tin đơn hàng cho Người Bán để Người Bán xác nhận đơn hàng. Sau khi đơn hàng được xác nhận, đơn hàng sẽ được phân cho đơn vị cung ứng dịch vụ vận chuyển (dựa trên danh sách đơn vị cung ứng dịch vụ vận chuyển khả dụng cho mỗi phương thứ…

- Hạng 2 — `shopee-returns-refund` — score `0.3444` — **không đủ bằng chứng**: b. Trong trường hợp nhận được khiếu nại của Người Bán về kết quả giải quyết yêu cầu Trả hàng COM trên hệ thống của Shopee, Shopee có quyền (mà không phải là nghĩa vụ) cung cấp các thông tin về (i) hạng thành viên, (ii) hạn mức Trả hàng COM còn lại của Người Mua cho Người Bán mà không cần phải thông báo cho Người Mua về việc cung cấp thông tin này. Tùy vào t…

- Hạng 3 — `shopee-returns-refund` — score `0.2992` — **không đủ bằng chứng**: Người Mua hợp lệ chỉ được Trả hàng COM trong các hạn mức được tính theo tháng như sau: a. Đối với khách hàng thân thiết hạng Vàng và Kim Cương: không giới hạn hạn mức theo tháng, trừ trường hợp Người Mua thực hiện bất cứ hành vi nào vi phạm các Chính sách của Sàn TMĐT Shopee, bao gồm nhưng không giới hạn ở Điều khoản dịch vụ. Trong trường hợp đó, Người Mua…

### Câu 2

Theo quy định đăng bán sản phẩm, hình ảnh sản phẩm do người bán tự chụp phải chiếm tối thiểu bao nhiêu % diện tích ảnh?

Expected document: `shopee-seller-listing-rules`

- Hạng 1 — `shopee-seller-listing-rules` — score `0.1975` — **không đủ bằng chứng**: + Về nhãn hàng hóa theo quy định của Nghị định 43/2017/NĐ-CP về nhãn hàng hóa (mục 7 Phụ lục I); + Mô tả sản phẩm dưới dạng tài liệu về hàng hóa, dịch vụ để giới thiệu với khách hàng trong hoạt động trưng bày, giới thiệu hàng hóa, dịch vụ theo quy định tại Điều 117, Điều 120, Điều 121) Luật Thương mại 2005; + Phù hợp với quy định về cung cấp thông tin hàng…

- Hạng 2 — `shopee-seller-listing-rules` — score `0.1575` — **liên quan**: Tiêu đề, hình ảnh, giá cả, mô tả sản phẩm và các thông tin liên quan phải thống nhất, đúng chính tả, đúng quy định về đăng tin của Shopee. Cụ thể như sau: 1. Hình ảnh sản phẩm a. Hình ảnh sản phẩm phải là ảnh chụp rõ, chi tiết tình trạng sản phẩm. Không được để những hình ảnh hoặc thông tin không liên quan đến sản phẩm này như thông tin giới thiệu shop, thô…

- Hạng 3 — `shopee-seller-listing-rules` — score `0.1345` — **không đủ bằng chứng**: 3.4. Thời trang/Giày dép/Phụ kiện - Nêu rõ chất liệu và kích thước của sản phẩm. Riêng đối với sản phẩm thuộc ngành hàng Thời trang phải có bảng quy đổi kích thước. - Đối với các sản phẩm thời trang hoặc phụ kiện làm bằng lụa tơ tằm, Người Bán phải đăng kèm chứng nhận nhãn hiệu ở phần hình ảnh sản phẩm. - Nên có ít nhất một hình ảnh thật của sản phẩm để khá…

### Câu 3

Đơn hàng thanh toán bằng Apple Pay trên Shopee cần có giá trị thanh toán cuối cùng trong khoảng nào?

Expected document: `shopee-payment-methods`

- Hạng 1 — `shopee-marketplace-terms` — score `0.3648` — **không đủ bằng chứng**: Điều kiện bảo hành đối với hàng hóa Các điều kiện bảo hành được liệt kê dưới đây là các điều kiện cơ bản mà Shopee khuyến cáo Người Mua cần hiểu rõ mỗi khi mua sản phẩm/dịch vụ trên Sàn TMĐT Shopee. Trong mọi trường hợp Người Mua cần tham khảo Chính sách bảo hành đối với hàng hóa, dịch vụ tương ứng trong phần mô tả sản phẩm, dịch vụ được đăng bán của Người…

- Hạng 2 — `shopee-privacy-policy` — score `0.2871` — **không đủ bằng chứng**: khi bạn sử dụng các dịch vụ điện tử của chúng tôi, hoặc tương tác với chúng tôi qua Nền tảng hoặc Trang Web hoặc Các Dịch Vụ của chúng tôi. Trường hợp này bao gồm thông qua tập tin cookie mà chúng tôi có thể triển khai khi bạn tương tác với các Nền tảng hoặc Trang Web của chúng tôi; khi bạn cấp quyền trên thiết bị của bạn để chia sẻ thông tin với ứng dụng h…

- Hạng 3 — `shopee-marketplace-terms` — score `0.2670` — **không đủ bằng chứng**: Bước 6: Người Mua nhận hàng; Bước 7: Sau khi hết thời gian khiếu nại của đơn hàng hoặc Người Mua xác nhận không có khiếu nại, Shopee thanh toán tiền hàng cho Người Bán thông qua Số dư Tài khoản Shopee. Bước 8: Người Mua thực hiện thanh toán số tiền mua hàng theo kỳ hạn đã lựa chọn với Ngân hàng. VI. Đảm bảo an toàn giao dịch Ban quản lý đã sử dụng các dị…

### Câu 4

Kiện hàng vận chuyển theo hình thức Hỏa Tốc (Instant) bị giới hạn kích thước và cân nặng tối đa bao nhiêu?

Expected document: `shopee-shipping-policy`

- Hạng 1 — `shopee-shipping-policy` — score `0.3410` — **không đủ bằng chứng**: 8. Việc không gửi hàng thật, đưa tiền cho nhân viên vận chuyển để cập nhật sai trạng thái đơn hàng, tự đặt hàng của chính mình, thông đồng giữa Người Bán, Người Mua vv… nhằm lợi dụng Chính Sách Vận Chuyển và/hoặc các chương trình khuyến mại theo từng thời kỳ của Shopee sẽ dẫn đến hình thức xử phạt nghiêm khắc của Shopee theo Chính sách xử lý gian lận của Sà…

- Hạng 2 — `shopee-marketplace-terms` — score `0.3220` — **không đủ bằng chứng**: Cách 2: Thanh toán online qua Ví điện tử ShopeePay, ApplePay, Google Pay hoặc thẻ tín dụng/ghi nợ: Shopee chấp nhận thanh toán thẻ của tất cả các ngân hàng tại Việt Nam với điều kiện phải là thẻ của thương hiệu thẻ Visa, Master Card JCB hoặc AMEX. Bước 1: Người Mua tìm hiểu thông tin về sản phẩm, dịch vụ được đăng tin; Bước 2: Người Mua đặt đơn hàng trên S…

- Hạng 3 — `shopee-returns-refund` — score `0.3174` — **không đủ bằng chứng**: Người Mua hợp lệ chỉ được Trả hàng COM trong các hạn mức được tính theo tháng như sau: a. Đối với khách hàng thân thiết hạng Vàng và Kim Cương: không giới hạn hạn mức theo tháng, trừ trường hợp Người Mua thực hiện bất cứ hành vi nào vi phạm các Chính sách của Sàn TMĐT Shopee, bao gồm nhưng không giới hạn ở Điều khoản dịch vụ. Trong trường hợp đó, Người Mua…

### Câu 5

Chính sách bảo mật của Shopee áp dụng cho những đối tượng người dùng nào?

Expected document: `shopee-privacy-policy`

- Hạng 1 — `shopee-seller-listing-rules` — score `0.3861` — **không đủ bằng chứng**: - Không đăng bán các sản phẩm không rõ nguồn gốc xuất xứ (ví dụ như sản phẩm handmade, kem trộn, v.v…); - Đối với các sản phẩm thương hiệu trong nước: phải đăng kèm hình scan (bản gốc hoặc sao y công chứng) các loại Giấy Chứng Nhận sau: + Phiếu công bố mỹ phẩm do Bộ/ Sở Y tế cấp, trong đó thể hiện thông tin chủ thể chịu trách nhiệm đưa sản phẩm ra thị trườn…

- Hạng 2 — `shopee-marketplace-terms` — score `0.3827` — **không đủ bằng chứng**: # Quy chế hoạt động sàn thương mại điện tử Shopee.vn I. Nguyên tắc chung 1. Mô hình Loại hình cung cấp dịch vụ trên Website: Đặt hàng trực tuyến và giao tận nơi; Voucher/Mã giảm giá; Sàn giao dịch Thương mại điện tử (TMĐT) Shopee do Công ty TNHH Shopee (“Công ty”, “Shopee”) thực hiện hoạt động và vận hành. Thành viên trên sàn là các thương nhân, tổ chức, cá…

- Hạng 3 — `shopee-marketplace-terms` — score `0.3557` — **không đủ bằng chứng**: d. Thành viên sẽ tự chịu trách nhiệm về tính chính xác, trung thực của thông tin, tài liệu cung cấp cho Shopee cũng như tự chịu trách nhiệm về bảo mật và lưu giữ mọi hoạt động sử dụng dịch vụ dưới tên đăng ký, mật khẩu của mình. Thành viên có trách nhiệm thông báo kịp thời cho Sàn giao dịch TMĐT Shopee về những hành vi sử dụng trái phép, lạm dụng, vi phạm b…

## Trường hợp retrieval thất bại

Các câu không có chunk đủ `doc_id + evidence` trong top-3: 1, 3, 4, 5.

> File này là phần bàn giao cá nhân cho nhóm trưởng; runner không sửa `report/REPORT_NHOM.md`.
