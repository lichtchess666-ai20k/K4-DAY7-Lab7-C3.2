# Phần cá nhân TriTue — Lab 7

Thư mục này chứa lời giải cá nhân của TriTue cho pipeline chunking, embedding,
vector store, RAG agent và phần đóng góp vào benchmark chung của nhóm.

## 1. Chuẩn bị môi trường

Mở PowerShell tại thư mục `K4-DAY7-Lab7-C3.2`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Để chạy benchmark với multilingual embedding thật:

```powershell
python -m pip install -r requirements-local.txt
```

## 2. Chạy test

```powershell
$env:LAB_SOLUTION_PACKAGE = 'src.TriTue'
python -m pytest tests/ -v
```

## 3. Chạy demo cá nhân ban đầu

```powershell
python -m src.TriTue
```

Demo này so sánh ba chiến lược chunking có sẵn, kiểm tra similarity, nạp vector
store và chạy năm câu hỏi mẫu của phần cá nhân.

## 4. Phương pháp chunk riêng cho phần làm việc nhóm

`ContextualParagraphWindowChunker` là phương pháp riêng của TriTue:

- tách văn bản thành các khối đoạn bằng dòng trống;
- ghép các đoạn liền kề đến giới hạn ký tự;
- giữ lại một đoạn cuối làm ngữ cảnh chồng lấp cho chunk tiếp theo;
- dùng cửa sổ theo ranh giới từ nếu một đoạn đơn lẻ quá dài.

Đây không phải phương pháp chia theo từng dòng, từng câu, heading/điều khoản hay
loại chính sách. Cấu hình mặc định là `chunk_size=900`,
`overlap_paragraphs=1`, `word_overlap=20`.

Chạy benchmark trên đúng sáu tài liệu trong `data/k4_ecommerce` bằng local
multilingual embedding:

```powershell
python -m src.TriTue.group_benchmark --output src/TriTue/GROUP_CONTRIBUTION.md
```

Chỉ smoke test pipeline khi chưa cài model local:

```powershell
python -m src.TriTue.group_benchmark --mock --output src/TriTue/GROUP_CONTRIBUTION.md
```

Mock embedding không có ý nghĩa ngữ nghĩa; điểm và thứ hạng từ chế độ này không
được dùng để kết luận chiến lược retrieval tốt hay kém.

## 5. File bàn giao

- `custom_chunking.py`: implementation phương pháp chunk riêng.
- `group_benchmark.py`: loader corpus, năm query chung, retrieval top-3 và CLI.
- `GROUP_CONTRIBUTION.md`: kết quả cá nhân để gửi nhóm trưởng tổng hợp.
- `tests/test_tritue_solution.py`: test edge case và test hồi quy.
- `report/REPORT_CANHAN_TriTue.md`: báo cáo cá nhân.

Runner cá nhân không đọc-ghi hay chỉnh sửa `report/REPORT_NHOM.md`; báo cáo nhóm
do nhóm trưởng quản lý.
