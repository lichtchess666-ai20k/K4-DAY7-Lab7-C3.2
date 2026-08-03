# Thiết kế lời giải cá nhân TriTue — Lab 7

## Mục tiêu

Tạo một package lời giải cá nhân độc lập tại `src/TriTue/` mà không sửa các TODO trong package khung `src`. Package phải cung cấp cùng API công khai với `src`, vượt qua bộ kiểm thử hiện có khi đặt `LAB_SOLUTION_PACKAGE=src.TriTue`, và có thể dùng cho demo RAG của bài lab.

Tạo báo cáo cá nhân riêng tại `report/REPORT_CANHAN_TriTue.md` để giữ nguyên file mẫu. Báo cáo hoàn thiện các phần có thể xác định độc lập; phần kết quả truy xuất dùng bộ dữ liệu K4 mẫu và nêu rõ kết quả này cần được đồng bộ lại nếu nhóm chọn bộ năm câu hỏi khác.

## Cấu trúc package

`src/TriTue/` gồm các module sau:

- `__init__.py`: xuất toàn bộ API mà bộ test và demo sử dụng.
- `models.py`: định nghĩa `Document` dataclass.
- `embeddings.py`: cung cấp mock, local và OpenAI embedder tương thích package gốc.
- `chunking.py`: chứa ba chunker, cosine similarity và bộ so sánh chiến lược.
- `store.py`: chứa vector store với hai backend ChromaDB và in-memory.
- `agent.py`: chứa RAG agent nhận store và hàm LLM qua dependency injection.

Package sao chép các thành phần đã được cung cấp sẵn (`Document`, `FixedSizeChunker`, các embedder) để lời giải cá nhân không phụ thuộc vào TODO của package cha.

## Hành vi chia nhỏ và tính độ tương tự

`SentenceChunker` phát hiện ranh giới câu sau dấu `.`, `!`, `?` khi theo sau là khoảng trắng hoặc xuống dòng. Các câu được chuẩn hóa khoảng trắng, giữ dấu kết thúc câu và gom tối đa theo `max_sentences_per_chunk`. Chuỗi rỗng trả về danh sách rỗng.

`RecursiveChunker` lần lượt thử các separator theo độ ưu tiên. Đoạn không vượt `chunk_size` là base case. Đoạn quá dài được tách bằng separator hiện tại; phần vẫn quá dài tiếp tục xử lý bằng separator kế tiếp. Separator rỗng hoặc hết separator sẽ cắt cứng theo kích thước để luôn kết thúc và bảo đảm dữ liệu không bị mất.

`compute_similarity` dùng cosine similarity, trả `0.0` nếu một vector có norm bằng không, và từ chối hai vector khác số chiều để tránh kết quả âm thầm sai do `zip` cắt ngắn.

`ChunkingStrategyComparator` chạy `FixedSizeChunker`, `SentenceChunker` và `RecursiveChunker`, sau đó trả về `count`, `avg_length`, và `chunks` cho từng chiến lược.

## Vector store

Mỗi record chuẩn hóa gồm ID nội bộ duy nhất, `doc_id`, `content`, bản sao `metadata`, và `embedding`. `doc_id` luôn được đưa vào metadata để hỗ trợ xóa toàn bộ chunk của cùng tài liệu. ID nội bộ kết hợp ID tài liệu và bộ đếm tăng dần để cho phép nhiều chunk có cùng `doc_id`.

Với in-memory backend, truy vấn được nhúng một lần, chấm điểm bằng tích vô hướng, sắp xếp giảm dần và cắt `top_k`. Metadata filter được áp dụng trước khi chấm điểm. Xóa tài liệu loại bỏ mọi record có `metadata.doc_id` tương ứng.

Nếu ChromaDB có sẵn, store tạo client in-memory và collection riêng, rồi ánh xạ kết quả Chroma về cùng schema kết quả của backend in-memory. Metadata được chuẩn hóa để Chroma nhận các kiểu scalar. Các phương thức `add_documents`, `search`, `get_collection_size`, `search_with_filter`, và `delete_document` phải có hành vi tương đương giữa hai backend.

Các giá trị `top_k <= 0`, truy vấn khi store rỗng, danh sách tài liệu rỗng và xóa ID không tồn tại được xử lý an toàn.

## RAG agent

`KnowledgeBaseAgent.answer` truy xuất tối đa `top_k` record, ghép nội dung thành các khối context có số thứ tự, rồi tạo prompt gồm chỉ dẫn chỉ trả lời dựa trên context, context và câu hỏi. Prompt được chuyển nguyên vẹn cho `llm_fn` và kết quả của hàm này được trả về.

Nếu không truy xuất được context, prompt nói rõ knowledge base không có thông tin phù hợp để LLM không giả định dữ kiện không tồn tại.

## Kiểm thử và xác minh

Quy trình xác minh:

1. Chạy bộ test hiện có với `LAB_SOLUTION_PACKAGE=src.TriTue`.
2. Bổ sung test cá nhân cho edge case quan trọng chưa có trong bộ test lớp: chuỗi rỗng, vector lệch chiều, separator không xuất hiện, filter nhiều trường, nhiều chunk cùng `doc_id`, và nội dung prompt của agent.
3. Chạy demo nạp dữ liệu K4 bằng package cá nhân và ghi kết quả cần thiết vào báo cáo.
4. Kiểm tra không còn TODO hoặc `NotImplementedError` trong `src/TriTue/`.

Máy hiện chưa nhận lệnh `python` hoặc `py`. Nếu môi trường này vẫn không có Python ở giai đoạn xác minh, mã nguồn và lệnh test sẽ được chuẩn bị đầy đủ, đồng thời hướng dẫn cài Python 3.11 và chạy lại sẽ được ghi rõ; không tuyên bố test đã pass nếu chưa có output thực tế.

## Báo cáo cá nhân

`REPORT_CANHAN_TriTue.md` sẽ bao gồm:

- lời giải warm-up và phép tính số chunk;
- mô tả đúng với implementation thực tế;
- output test chỉ được ghi sau khi chạy thành công;
- năm dự đoán similarity kèm kết quả từ embedder khả dụng;
- năm câu benchmark trên corpus K4 mẫu, top-1, score, đánh giá liên quan và câu trả lời demo;
- nhãn cảnh báo ngắn ở phần benchmark nếu đây chưa phải bộ câu hỏi chung cuối cùng của nhóm.

Không tự điền họ tên, tên nhóm hoặc tuyên bố học được từ thành viên khác khi chưa có dữ liệu từ người dùng.
