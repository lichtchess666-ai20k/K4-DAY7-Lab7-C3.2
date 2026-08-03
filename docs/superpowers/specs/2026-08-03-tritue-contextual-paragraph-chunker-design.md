# Thiết kế ContextualParagraphWindowChunker — đóng góp nhóm của TriTue

## Mục tiêu và phạm vi

Xây dựng một chiến lược chunking riêng cho sáu tài liệu Shopee trong `data/k4_ecommerce/`. Chiến lược không chia theo từng dòng, từng câu, heading/điều khoản hay từng loại chính sách. Mã nguồn nằm trong package cá nhân `src/TriTue/` và không thay đổi `report/REPORT_NHOM.md`.

Sản phẩm gồm implementation, test, runner benchmark đúng năm câu hỏi nhóm hiện có và một file bàn giao kết quả trong `src/TriTue/` để nhóm trưởng tự chọn số liệu đưa vào báo cáo chung.

## Cơ sở lựa chọn

Corpus có sáu tài liệu, từ khoảng 8 KB đến 103 KB. Mỗi file chỉ có một Markdown H1; cấu trúc chi tiết chủ yếu là văn bản đánh số và các khối ngăn bằng dòng trống. Tổng cộng có hơn 1.100 khối đoạn, trong đó nhiều khối dưới 80 ký tự là nhãn hoặc giá trị bảng, ví dụ `Hỏa Tốc`, `Instant`, `60 x 60 x 60`, `30`.

Vì vậy, tách từng đoạn riêng sẽ tạo quá nhiều chunk thiếu ngữ cảnh, còn fixed window có thể cắt rời các giá trị liên quan. Chiến lược cửa sổ đoạn văn sẽ ghép các khối lân cận đến gần ngân sách kích thước để giữ cấu trúc cục bộ mà không phụ thuộc vào domain chính sách.

## API và cấu hình

Lớp `ContextualParagraphWindowChunker` được đặt trong module mới `src/TriTue/custom_chunking.py` và xuất qua `src.TriTue`.

Constructor:

```python
ContextualParagraphWindowChunker(
    chunk_size: int = 900,
    overlap_paragraphs: int = 1,
    word_overlap: int = 20,
)
```

Public method:

```python
chunk(text: str) -> list[str]
```

Các tham số không hợp lệ bị từ chối bằng `ValueError`: `chunk_size <= 0`, `overlap_paragraphs < 0`, `word_overlap < 0`.

## Thuật toán

1. Chuỗi rỗng hoặc chỉ có whitespace trả `[]`.
2. Chuẩn hóa newline về `\n` và chia văn bản thành các khối bằng một hoặc nhiều dòng trống. Đây là ranh giới đoạn văn, không phải từng dòng hay từng câu.
3. Ghép tuần tự nhiều đoạn bằng `\n\n` cho đến khi thêm đoạn tiếp theo sẽ vượt `chunk_size`.
4. Khi phát chunk, giữ tối đa `overlap_paragraphs` đoạn cuối làm phần đầu của chunk tiếp theo, nhưng bỏ overlap nếu riêng phần overlap đã chiếm toàn bộ ngân sách hoặc không làm tiến trình tiến lên.
5. Nếu một đoạn đơn lẻ dài hơn `chunk_size`, chia đoạn đó tại ranh giới từ thành các cửa sổ không vượt giới hạn; cửa sổ kế tiếp lặp tối đa `word_overlap` từ cuối. Đây chỉ là fallback cho đoạn quá dài, không phải chiến lược word-window chính.
6. Các đoạn rất ngắn được ghép với hàng xóm. Nhờ đó các giá trị bảng/list đứng gần nhau vẫn xuất hiện trong cùng context khi tổng kích thước cho phép.

Mỗi chunk không vượt `chunk_size`, trừ trường hợp một token đơn lẻ dài hơn toàn bộ ngân sách; token đó được giữ nguyên để không làm mất dữ liệu.

## Pipeline benchmark

Module `src/TriTue/group_benchmark.py` sẽ:

1. Đọc sáu file bằng parser front matter được cung cấp trong `ingest.py`.
2. Chunk bằng `ContextualParagraphWindowChunker` và gắn nguyên metadata cùng `doc_id`, `chunk_index`, `chunking_strategy` lên từng chunk.
3. Nạp vào `src.TriTue.EmbeddingStore`.
4. Chạy đúng năm query/gold answer hiện có trong `report/REPORT_NHOM.md`; query thứ hai dùng `metadata_filter={"customer_role": "seller"}`.
5. Ghi top-3, score, expected document, evidence match và failure case ra console và file bàn giao `src/TriTue/GROUP_CONTRIBUTION.md`.

Runner ưu tiên `LocalEmbedder`. Nếu local model chưa được cài, runner dừng với hướng dẫn rõ ràng. Chế độ `--mock` chỉ dùng smoke test pipeline và phải gắn nhãn rằng score không có ý nghĩa ngữ nghĩa.

## Đánh giá relevance

Một kết quả chỉ được tính relevant khi cả hai điều kiện đúng:

- `metadata.doc_id` khớp tài liệu chứa gold answer;
- content chứa evidence kiểm chứng tương ứng, như cặp `15 ngày`/`24 giờ`, `40%`, cặp `10.000 VNĐ`/`25.000.000 VNĐ`, cặp `60 x 60 x 60`/`30`, hoặc `Người bán`/`Người mua`.

Cách kiểm tra này tránh tính một chunk bất kỳ trong đúng file là relevant khi nó không chứa câu trả lời.

## Kiểm thử

Test bổ sung sẽ chứng minh:

- đoạn ngắn được ghép thay vì mỗi đoạn thành một chunk;
- context bảng vận chuyển giữ `Instant`, `60 x 60 x 60` và `30` cùng nhau;
- mọi chunk thông thường không vượt `chunk_size`;
- overlap xuất hiện đúng nhưng thuật toán luôn tiến lên;
- đoạn quá dài dùng fallback theo từ;
- text rỗng và tham số lỗi được xử lý;
- runner có đúng năm query, filter seller và tiêu chí evidence;
- toàn bộ 42 test gốc cùng test cá nhân hiện tại không bị regression.

## Ranh giới trách nhiệm

Không sửa `report/REPORT_NHOM.md`, không tự điền kết quả của thành viên khác và không kết luận chiến lược tốt nhất cho nhóm. File `GROUP_CONTRIBUTION.md` chỉ là dữ liệu bàn giao cho nhóm trưởng, gồm mô tả chiến lược, lệnh chạy, thống kê và kết quả của riêng TriTue.
