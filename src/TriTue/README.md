# Phần cá nhân TriTue — Lab 7

Package này là lời giải cá nhân độc lập cho các TODO trong `src/chunking.py`, `src/store.py` và `src/agent.py`. Package gốc được giữ nguyên; bộ test chọn lời giải này qua `LAB_SOLUTION_PACKAGE=src.TriTue`.

## 1. Chuẩn bị môi trường Windows

Cài Python 3.11, sau đó mở PowerShell tại thư mục `K4-DAY7-Lab7-C3.2`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 2. Chạy test phần cá nhân

```powershell
$env:LAB_SOLUTION_PACKAGE = 'src.TriTue'
python -m pytest tests/ -v
```

Kết quả gần nhất trong môi trường hiện có: 42 test của đề và 26 test bổ sung đều pass trên Python 3.13.7. Cần chạy lại lệnh trên bằng Python 3.11 trước khi nộp vì đây là phiên bản chuẩn của lab.

## 3. Chạy demo cá nhân

```powershell
python -m src.TriTue
```

Demo thực hiện:

- so sánh ba chiến lược chunking;
- tính điểm cho năm cặp similarity;
- nạp corpus khởi động K4 bằng `RecursiveChunker(chunk_size=500)`;
- chạy đúng năm benchmark query, gồm một query lọc `customer_role=seller`;
- tạo câu trả lời trích xuất từ chính tập chunk đã truy xuất.

Mock embedding chỉ dùng để kiểm tra luồng xử lý. Để đánh giá tiếng Việt có ý nghĩa, cài `requirements-local.txt` và thay `_mock_embed` bằng `LocalEmbedder` trong benchmark của nhóm.

## 4. File thuộc phần cá nhân

- `src/TriTue/`: mã nguồn cá nhân.
- `tests/test_tritue_solution.py`: test edge case bổ sung.
- `report/REPORT_CANHAN_TriTue.md`: báo cáo cá nhân đã điền từ kết quả demo.

## 5. Việc cần thay bằng dữ liệu thật trước khi nộp

1. Xác nhận họ tên và tên nhóm trong báo cáo.
2. Dùng corpus 5–10 tài liệu công khai của nhóm thay cho hai file khởi động.
3. Dùng đúng năm query và gold answer chung của nhóm.
4. Chạy local multilingual embedder và cập nhật điểm similarity/retrieval.
5. Ghi bài học thực tế sau phần so sánh với thành viên khác.
6. Nếu hệ thống nộp bài chỉ nhận đúng tên `report/REPORT_CANHAN.md`, đổi tên bản `REPORT_CANHAN_TriTue.md` hoặc chép nội dung bản này vào file đó trước khi nộp.
