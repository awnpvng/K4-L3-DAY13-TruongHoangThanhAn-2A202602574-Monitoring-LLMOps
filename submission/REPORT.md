# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Trương Hoàng Thanh An
- **MSSV:** 2A202602574
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/awnpvng/K4-L3-DAY13-TruongHoangThanhAn-2A202602574-Monitoring-LLMOps
- **Commit SHA cuối:** c7ed73439721c3be837ce1ea9f6bb801a24ede23
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602574`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence            | Đường dẫn                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| Pytest cuối        | `evidence/01-pytest.png`                                                                                 |
| Log validator       | `evidence/02-log-validator.png`                                                                          |
| Dashboard validator | `evidence/03-dashboard-validator.png`                                                                    |
| Structured log      | `evidence/04-structured-log.png`                                                                         |
| PII redaction       | `evidence/05-pii-redaction.png`                                                                          |
| Trace list          | `evidence/06-trace-list.png`                                                                             |
| Trace waterfall     | `evidence/07-trace-waterfall.png`                                                                        |
| Trace metadata      | `evidence/08-trace-metadata.png`                                                                         |
| Prompt versions     | `evidence/09-prompt-versions.png`                                                                        |
| Prompt rollback     | `evidence/10a-prompt-rollback.png` (production→v2), `evidence/10b-prompt-rollback.png` (rollback→v1) |
| Dashboard runtime   | `evidence/11-dashboard-overview.png`                                                                     |
| Incident metric     | `evidence/12-incident-metric.png`                                                                        |
| Incident log        | `evidence/13-incident-log.png`                                                                           |
| Incident trace      | `evidence/14-incident-trace.png`                                                                         |

## 3. Kết quả kỹ thuật

| Nội dung                 | Baseline                                                                                                                        | Kết quả cuối                                                                                                            | Nhận xét                                                                                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `validate_logs.py`      | 30/100 (Total 22, missing required fields 20, missing enrichment 20, unique correlation IDs 0)                                  | 100/100 (Total 68, missing required fields 0, missing enrichment 0, unique correlation IDs 31, PII leak 0)                 | Sau CP1: correlation ID + enrichment (`user_id_hash`, `session_id`, `feature`, `model`, `env`) đã bind đủ; PII scrubbing tiếp tục PASSED. |
| `validate_dashboard.py` | HỢP LỆ: 6/6 panel                                                                                                             | HỢP LỆ: 6/6 panel                                                                                                        | Contract dashboard đủ 6 panel từ baseline; đã bổ sung dashboard runtime (`scripts/render_dashboard.py`) để chứng minh dữ liệu thật.         |
| `pytest`                | 22 passed                                                                                                                       | 22 passed                                                                                                                  | Toàn bộ test vẫn pass sau khi hoàn thiện CP1 + CP2.                                                                                                  |
| Số traces hợp lệ       | 0 (chưa tạo child observation retrieval/generation)                                                                           | ≥30 root trace (`lab-agent-run`) có đủ child `retrieval`+`generation` trong project `day13-k4-l3b-2A202602574` | Đạt yêu cầu ≥10 trace tự tạo.                                                                                                                      |
| Số PII leak              | 0 (validator báo PASSED PII scrubbing)                                                                                         | 0                                                                                                                          | Không phát hiện PII nguyên văn sau redaction.                                                                                                        |
| Latency P95 / TTFT P95    | Chưa đo (load_test.py baseline chỉ log latency từng request, ví dụ 8753.5ms/442.9ms/...; chưa có panel latency runtime) | P95 = 1024.8 ms / TTFT P95 = 50.0 ms (dashboard runtime, cửa sổ 60 phút, 80 request)                                    | Đạt ngưỡng P95 ≤ 3000ms.                                                                                                                             |
| Retrieval success rate    | Chưa đo                                                                                                                       | 100.0% (dashboard runtime)                                                                                                 | Đạt ngưỡng ≥ 90%.                                                                                                                                    |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** `CorrelationIdMiddleware` (`app/middleware.py`) clear contextvars cũ đầu mỗi request, đọc header `x-request-id` nếu client gửi sẵn, nếu không thì sinh `req-<8-hex>` (`uuid4().hex[:8]`). ID được bind vào `structlog.contextvars` bằng `bind_contextvars(correlation_id=...)` nên mọi log trong cùng request tự động có field này, đồng thời trả lại cho client qua header `x-request-id` và `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Trong handler `/chat` (`app/main.py`), trước log `request_received` gọi `bind_contextvars(user_id_hash=..., session_id=..., feature=..., model=..., env=...)`. `user_id_hash` lấy từ `hash_user_id(user_id)` (SHA-256, cắt 12 ký tự) để không lưu user_id thô. Nhờ vậy tất cả log sau đó trong request (bao gồm `response_sent`/`request_failed`) đều có đủ field enrichment.
- **Cách bảo đảm PII được scrub trước khi ghi:** Trong `app/logging_config.py`, processor `scrub_event` được thêm vào pipeline `structlog.configure(processors=[...])` ngay sau `TimeStamper` và trước `JsonlFileProcessor`/`JSONRenderer`, nên `event` và các field text trong `payload` luôn được `scrub_text()` (regex email, SĐT VN, CCCD, thẻ, passport) trước khi ghi file hoặc render JSON.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` → 100/100 (68 record, 0 missing required/enrichment, 31 correlation ID duy nhất, 0 PII leak). Gửi thủ công 1 request chứa email + SĐT giả (`test@example.com`, `0912345678`) rồi kiểm tra `data/logs.jsonl` thấy `[REDACTED_EMAIL]`/`[REDACTED_PHONE_VN]` thay cho text gốc (evidence `05-pii-redaction.png`).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Tất cả trace được xem trong project Langfuse cá nhân `day13-k4-l3b-2A202602574` (thấy tên project ở góc trên trái mọi ảnh evidence 06–10). `LANGFUSE_PUBLIC_KEY`/`SECRET_KEY` trong `.env` chỉ trỏ tới project này; đã xác minh qua `auth_check()` và `client.api.prompts.list()` khi debug (không dùng key/project của người khác).
- **Cấu trúc root/retrieval/generation observations:** Trong `app/agent.py`, `LabAgent.run()` là root span (`as_type="agent"`, tên `lab-agent-run`). Bên trong, `self._retrieve(message)` là child observation `as_type="retriever"` (tên `retrieval`, ghi `doc_count`, `query_preview`); `self._generate(prompt)` là child observation `as_type="generation"` (tên `generation`, ghi `model`, `usage_details` input/output tokens, `cost_details`, `prompt` object qua `update_current_generation`). Cây quan sát được: `lab-agent-run → retrieval, generation` (evidence `07-trace-waterfall.png`).
- **Cách nối trace với log:** `correlation_id` (sinh ở `CorrelationIdMiddleware`) được truyền vào `LabAgent.run(correlation_id=...)` rồi đưa vào `metadata={"correlation_id": correlation_id}` của `propagate_attributes(...)` ở root span, nên toàn bộ trace (và các child observation) đều mang metadata này — khớp với `correlation_id` trong `data/logs.jsonl` của cùng request (evidence `08-trace-metadata.png`, trace `d6a4d50facb32dd1858ab18aacd5f218`, `correlation_id: "req-bec6eccc"`, `prompt_source: "langfuse"`, `prompt_version: 1`).
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** version `#1`, label `production` + `baseline`. Nội dung: `Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}`.
- **Version/label candidate:** version `#2`, label `latest` + `candidate` (sau đó tạm thời promote lên `production` để test). Nội dung thêm dòng `Answer concisely in at most 3 sentences.` so với v1.
- **Trace ID của mỗi version:**
  - v1 (production, trước promote): trace `21e2644d38f7337b97d9f0506bd90828`, correlation `req-de7bff5f`, metadata `prompt_version: 1`.
  - v1 (production, xác nhận lại trước rollback): trace `e5b93d7127da93f3ab29e3ddd50665bd`, correlation `req-3d98ec1e`.
  - v2 (production, sau promote): trace `eb06b433a67b5e8d4a6d32f432fde44a`, correlation `req-b51252f0`, metadata `prompt_version: 2`.
- **Cách promote và rollback `production`:** Trên Langfuse UI, mở prompt `day13-chat` → chọn version `#2` → gắn label `production` cho version đó (label tự động rời khỏi v1) = promote. Chạy `python scripts/load_test.py`, trace mới xác nhận `prompt_version: 2, prompt_label: production` (evidence `10a-prompt-rollback.png`, thời điểm production đang ở v2). Để rollback, mở lại version `#1` → gắn lại label `production` cho v1 (label rời khỏi v2). Chạy lại `load_test.py`, trace mới xác nhận `prompt_version: 1` (evidence `10b-prompt-rollback.png`, v2 chỉ còn `latest`+`candidate`). App không cần sửa code khi đổi version vì `resolve_prompt()` luôn hỏi Langfuse theo `LANGFUSE_PROMPT_NAME`/`LANGFUSE_PROMPT_LABEL=production`, label trỏ version nào thì dùng version đó.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Contract 6 panel nằm ở `config/dashboard.yaml`: Latency (P50/P95/P99 + TTFT P95), Traffic, Errors (error rate + retrieval success), Cost, Tokens, Quality. Vì repo không kèm sẵn công cụ dashboard runtime, tôi viết `scripts/render_dashboard.py` đọc trực tiếp `data/logs.jsonl` theo đúng mapping/threshold trong `config/dashboard.yaml` và xuất `data/dashboard.html`. Chạy `python scripts/render_dashboard.py` rồi mở file trong trình duyệt cho ra dashboard runtime thật (evidence `11-dashboard-overview.png`): 80 request trong 60 phút gần nhất, Latency P95 1024.8ms (ngưỡng ≤3000ms, OK), Traffic 1.33 req/min (ngưỡng ≥1, OK), Error rate 0.0% / retrieval success 100% (ngưỡng ≤2%, OK), Cost $0.165402 (ngưỡng ≤$2.5, OK), Tokens 13386 (ngưỡng ≤50000, OK), Quality mean 0.88 (ngưỡng ≥0.75, OK). `python scripts/validate_dashboard.py` xác nhận contract 6/6 (evidence `03-dashboard-validator.png`).
- **SLO và lý do chọn:** `config/slo.yaml` giữ SLO gốc `fast_successful_requests`: 99.5% request trong cửa sổ 28 ngày phải vừa thành công (`response_sent`) vừa có `latency_ms <= 3000`. Chọn ngưỡng 3000ms vì trùng với threshold panel latency (P95 ≤ 3000ms) nên một SLI duy nhất vừa dùng để tính error budget vừa dùng để cảnh báo, tránh hai bộ số khác nhau gây nhầm lẫn khi điều tra.
- **Cách tính error budget:** target 99.5% → error budget 0.5%. Với baseline hiện tại 80 request/giờ trong log mẫu, nếu ngoại suy 28 ngày (28×24×80 ≈ 53,760 request) thì error budget cho phép tối đa khoảng 269 request lỗi hoặc chậm hơn 3000ms (0.5% × 53,760). Guardrail bổ sung trong `slo.yaml`: error_rate_pct_max 2, daily_cost_usd_max 2.5, quality_score_avg_min 0.75, retrieval_success_rate_pct_min 90 — dùng làm ngưỡng cảnh báo sớm trước khi chạm SLO chính.
- **Ba alert và runbook tương ứng:** Định nghĩa đầy đủ tại `config/alert_rules.yaml`, chi tiết điều kiện/ảnh hưởng/mitigation tại `docs/alerts.md`:
  1. `HighLatencyP95` (warning, `p95(latency_ms) > 3000ms` trong 5m) — runbook `docs/alerts.md#alert-1`.
  2. `HighErrorRate` (critical, `error_rate_pct > 2` trong 5m) — runbook `docs/alerts.md#alert-2`.
  3. `LowRetrievalSuccessRate` (warning, `tool_success_rate_pct < 90` trong 10m) — runbook `docs/alerts.md#alert-3`.
     Cả ba đều symptom-based (dựa trên metric người dùng cảm nhận được, không dựa tên hàm nội bộ), có duration, severity, owner (`student-2A202602574`) và kênh Slack `#k4-l3b-alerts`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Khoảng thời gian điều tra:** 2026-09-30, cửa sổ 60 phút gần nhất tính từ lúc render dashboard (04:09–05:09 UTC), triệu chứng rõ nhất quanh 05:09:37 UTC — ngay sau khi chạy `python scripts/inject_incident.py` và `python scripts/load_test.py --challenge --concurrency 5`.
- **Triệu chứng từ metrics:** Panel Latency trên dashboard runtime (`evidence/12-incident-metric.png`) cho thấy P95 tăng từ baseline ~1024.8ms lên **2636.8ms**, P99 lên **2908.2ms** (sát ngưỡng SLO 3000ms). Các panel khác (error rate 0%, retrieval success 100%, cost, tokens, quality) vẫn nằm trong ngưỡng bình thường — cho thấy đây là vấn đề latency cục bộ, không phải lỗi hệ thống diện rộng hay tăng chi phí.
- **Log line và correlation ID liên quan:** Lọc `data/logs.jsonl` trong đúng cửa sổ 60 phút, request chậm nhất là `correlation_id="req-52415b45"` với `latency_ms=4248`, `feature="monitoring"`, `ts=2026-09-30T05:09:37.502889Z` (evidence `evidence/13-incident-log.png`, gồm cả dòng `request_received` và `response_sent`).
- **Trace ID và span gây ảnh hưởng:** Trace `dab4b7e049deaa5741f037a393e7e39c` (metadata `correlation_id: "req-52415b45"`, khớp đúng log). Tổng thời gian trace 4.25s, trong đó span `retrieval` chiếm **2.50s** — gần như toàn bộ độ trễ — trong khi span `generation` chỉ mất 0.15s (evidence `evidence/14-incident-trace.png`).
- **Root cause:** Bước retrieval (truy vấn corpus/tài liệu) bị chậm bất thường, khớp với kịch bản incident giả lập `rag_slow` trong `app/incidents.py` (khi bật, `retrieve()` sleep 2.5s trước khi trả kết quả). LLM generation vẫn hoạt động bình thường, nên nguyên nhân không nằm ở model/prompt mà nằm ở tầng retrieval/tool.
- **Fix action:** Chạy `python scripts/inject_incident.py --disable` (hoặc tắt incident tương ứng qua endpoint `/incidents/{name}/disable`) để khôi phục retrieval về tốc độ bình thường; kiểm tra lại panel latency và trace mới để xác nhận P95 quay về dưới ngưỡng.
- **Preventive measure:** Alert `HighLatencyP95` (`config/alert_rules.yaml`, `docs/alerts.md#alert-1`) đã được cấu hình để cảnh báo khi `p95(latency_ms) > 3000ms` trong 5 phút, với runbook chỉ rõ 3 bước kiểm tra dashboard → log → trace giống quy trình vừa thực hiện ở trên, giúp phát hiện và xử lý sớm nếu retrieval chậm tái diễn trong production.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Vì repo không kèm sẵn công cụ dashboard runtime, tôi tự viết `scripts/render_dashboard.py` để đọc trực tiếp `data/logs.jsonl` theo đúng mapping/threshold trong `config/dashboard.yaml` và xuất ra `data/dashboard.html` tĩnh, thay vì cài thêm dependency (Streamlit/Grafana). Lý do: giữ repo nhẹ, không cần server/service ngoài, vẫn đủ chứng minh dữ liệu thật cho 6 panel theo đúng contract.
- **Một lỗi/blocker đã gặp:** Prompt `day13-chat` tạo trên Langfuse UI nhìn giống hệt tên trong `.env` nhưng app vẫn báo `prompt_fetch_error: "LangfuseFallback"` / `prompt_source: "local-fallback"` dù key và label đều đúng.
- **Cách tìm nguyên nhân và xử lý:** Gọi trực tiếp `client.get_prompt(...)` và `client.api.prompts.list()` qua Python REPL để xem lỗi thật từ API thay vì chỉ nhìn UI. Phát hiện tên prompt trên server thực chất là `day13-chat` (có ký tự zero-width space ẩn ở đầu, có thể do copy-paste), khiến so khớp tên bị lệch dù hiển thị giống hệt. Xử lý bằng cách tạo lại prompt, gõ tay tên (không copy-paste) để tránh ký tự ẩn.
- **Cách hiểu luồng Metrics → Logs → Traces:** Khi bơm incident (`inject_incident.py` + `load_test.py --challenge`), dashboard runtime cho thấy panel Latency P95 tăng bất thường (triệu chứng + khoảng thời gian) → lọc `data/logs.jsonl` trong đúng khoảng đó để tìm `correlation_id` của request chậm nhất (chọn được request cụ thể) → mở trace Langfuse cùng `correlation_id` đó, so sánh span `retrieval` (2.50s) với `generation` (0.15s) để xác định chính xác bước gây chậm (root cause ở tầng nào). Ba nguồn bổ trợ nhau: metric khoanh vùng, log chọn request, trace định vị bước lỗi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version cho phép thay đổi hành vi hệ thống mà không sửa code, nhưng cũng là một biến số có thể gây regression (latency/quality/cost) nên cần trace ghi lại version dùng cho từng request để truy vết. SLO/error budget định lượng "chấp nhận được đến đâu" thay vì chỉ theo dõi số liệu suông; rollback là công cụ khôi phục nhanh khi version mới gây xấu đi, và evidence promote/rollback chứng minh thao tác này có thể thực hiện an toàn, có kiểm chứng.
- **Điều quan trọng nhất đã học:** Một hệ thống LLM "chạy được" không đồng nghĩa "quan sát được" — phải chủ động thiết kế correlation ID, structured log, trace và dashboard ngay từ đầu thì mới điều tra được sự cố dựa trên bằng chứng thay vì đoán mò.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Dashboard runtime là script tự viết (HTML tĩnh, phải chạy lại lệnh mỗi khi muốn xem dữ liệu mới) thay vì dashboard tự động refresh; ước tính error budget ở mục 6 dựa trên ngoại suy từ traffic thấp trong môi trường lab, chưa phải số liệu production thật.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối. _(chờ commit cuối, xem mục 1)_
- [X] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [X] Incident evidence nối đúng metric → log → trace.
- [X] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret (chỉ hiện public key `pk-lf-...`, không hiện secret key hay trang API Keys).
- [X] Repository chạy lại được theo README (đã chạy lại `pytest`, `validate_logs.py`, `validate_dashboard.py` thành công trên máy).
- [X] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác (`.env`, `config/challenge.json`, `data/logs.jsonl` đều nằm trong `.gitignore`).
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs. _(việc cuối cùng sau khi push)_
