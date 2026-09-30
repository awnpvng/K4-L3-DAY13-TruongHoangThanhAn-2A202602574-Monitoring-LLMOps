# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`, gắn với SLO `fast_successful_requests` (target 99.5%, ngưỡng latency 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút liên tục
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời, có thể timeout ở phía client
- Ba bước kiểm tra đầu tiên:
  1. Mở panel latency trên dashboard để xác nhận P95/P99 và khoảng thời gian bắt đầu tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh span `retrieval` và `generation` để xác định bước nào chậm.
- Mitigation tạm thời: nếu span `retrieval` chậm thì kiểm tra/khởi động lại retrieval backend; nếu prompt version mới gây tăng latency thì rollback `production` về version cũ; giảm tải bằng cách giảm concurrency của load test khi demo.
- Owner: `student-2A202602574`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: error rate của `request_failed` so với `request_received`, gắn guardrail `error_rate_pct_max: 2`
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` trong 5 phút liên tục
- Ảnh hưởng tới người dùng: một phần request trả lỗi 500, người dùng không nhận được câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở panel errors trên dashboard để xác nhận error rate tăng và khoảng thời gian.
  2. Lọc `data/logs.jsonl` theo `event == "request_failed"`, lấy `correlation_id` và `error_type` của một request lỗi.
  3. Mở trace cùng `correlation_id`, kiểm tra span nào raise exception (thường là `retrieval` khi vector store timeout).
- Mitigation tạm thời: nếu lỗi tập trung ở tool retrieval, tắt/khởi động lại incident scenario liên quan (`tool_fail`), kiểm tra dependency bên ngoài; nếu do prompt mới, rollback `production` về version ổn định.
- Owner: `student-2A202602574`

## Alert 3

- Tên: `LowRetrievalSuccessRate`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `tool_success_rate_pct` (retrieval success), gắn guardrail `retrieval_success_rate_pct_min: 90`
- Điều kiện và thời gian duy trì: `tool_success_rate_pct < 90` trong 10 phút liên tục
- Ảnh hưởng tới người dùng: câu trả lời thiếu context liên quan, quality proxy giảm dù request vẫn trả về 200
- Ba bước kiểm tra đầu tiên:
  1. Mở panel errors (phần retrieval success) và panel quality trên dashboard để xác nhận xu hướng giảm.
  2. Lọc `data/logs.jsonl` theo `tool_name == "retrieval"` và `tool_success == false`, lấy `correlation_id` đại diện.
  3. Mở trace cùng `correlation_id`, xem span `retrieval` trả về bao nhiêu tài liệu (`doc_count`) và nội dung fallback.
- Mitigation tạm thời: kiểm tra corpus/index retrieval có bị rỗng hoặc lỗi truy vấn không; nếu do incident giả lập thì tắt scenario `rag_slow`/`tool_fail`; cân nhắc mở rộng corpus nếu fallback xảy ra thường xuyên với truy vấn hợp lệ.
- Owner: `student-2A202602574`
