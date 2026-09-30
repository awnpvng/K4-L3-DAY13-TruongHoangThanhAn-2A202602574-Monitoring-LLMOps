# Kế hoạch làm bài — Day 13 Monitoring & LLMOps

> Quy tắc chung: mỗi việc = code TODO → chạy lệnh kiểm tra → chụp evidence (lưu vào `submission/evidence/`) → điền ngay vào `submission/REPORT.md`. Không dồn evidence tới cuối.

## CP0 — Setup & baseline ✅ (đã xong)

- [X] Tạo venv, cài `requirements.txt`, copy `.env`.
- [X] Tạo project Langfuse riêng `day13-k4-l3b-<MSSV>`, điền key vào `.env`.
- [X] Chạy API (`uvicorn app.main:app --reload --env-file .env`).
- [X] Chạy `python scripts/load_test.py`, `pytest -q` baseline.
- [X] Evidence: `evidence/01-pytest.png`.
- [X] Điền baseline (`validate_logs.py`, `validate_dashboard.py`, pytest) vào bảng mục 3 `REPORT.md`.

## CP1 — Logging & PII (mục tiêu: `validate_logs.py` ≥ 80/100)

- [x] Sửa `app/middleware.py`: clear context cũ, nhận `x-request-id` hoặc sinh `req-<8-hex>`, bind ID, trả ID + response time qua header.
- [x] Sửa `app/main.py`: bind `user_id_hash`, `session_id`, `feature`, `model`, `env` trước log `request_received`.
- [x] Sửa `app/logging_config.py`: gắn PII scrubber chạy trước khi render JSON/ghi file.
- [x] Sửa `app/pii.py`: hoàn thiện regex + tests cho email, SĐT VN, CCCD, thẻ thanh toán (thêm passport).
- [x] Xóa/đổi tên `data/logs.jsonl` cũ, restart API.
- [x] Chạy lại workload: `python scripts/load_test.py`.
- [x] Chạy `python scripts/validate_logs.py` → 100/100 (≥80 đạt).
- [x] **Chụp ngay:**
  - [x] `evidence/02-log-validator.png` (kết quả validator)
  - [x] `evidence/04-structured-log.png` (một dòng log JSON có correlation_id + metadata)
  - [x] `evidence/05-pii-redaction.png` (input có PII giả → log đã redact)
- [x] Điền mục 4 (Logging và PII) trong `REPORT.md` ngay sau khi có evidence.

## CP2 — Tracing, prompt versioning, dashboard (mục tiêu: dashboard 6/6)

### Tracing

- [x] Thêm child observation `retrieval` (loại `retriever`/`span`) trong code agent.
- [x] Thêm child observation `generation` (loại `generation`, có model, prompt, input/output tokens, cost).
- [x] Đảm bảo `correlation_id` nằm trong trace metadata (đã có sẵn qua `propagate_attributes`).
- [x] Chạy workload đủ để có ≥ 10 traces (`load_test.py` nhiều lần nếu cần) — hiện có ~30+ root traces.
- [x] **Chụp:**
  - [x] `evidence/06-trace-list.png` (danh sách ≥10 trace, thấy tên project)
  - [x] `evidence/07-trace-waterfall.png` (1 trace có root/retrieval/generation)
  - [x] `evidence/08-trace-metadata.png` (metadata: correlation_id, prompt_source=langfuse, prompt_version=1, prompt_label=production, token, cost)

### Prompt versioning

- [x] Theo `docs/PROMPT_VERSIONING.md`: tạo prompt `day13-chat` v1 trên Langfuse (label `production`+`baseline`) — đã xác nhận `prompt_source: "langfuse"` trong trace.
- [x] Chạy request dùng v1, xác nhận trace gắn đúng version (`prompt_version: 1`).
- [ ] Tạo v2, promote `production` → v2, chạy lại request.
- [x] Rollback `production` → v1, chạy lại để có bằng chứng rollback.
- [x] **Chụp:**
  - [x] `evidence/09-prompt-versions.png` (thấy v1 và v2)
  - [x] `evidence/10a-prompt-rollback.png` + `evidence/10b-prompt-rollback.png` (production: v1→v2 rồi v2→v1)
- [x] Điền mục 5 (Tracing và prompt versioning) trong `REPORT.md`.

### Dashboard, SLO, Alerts

- [x] Dựng đúng 6 panel theo `config/dashboard.yaml` (đã có sẵn từ repo, không cần sửa).
- [x] Chạy `python scripts/validate_dashboard.py` → "HỢP LỆ: 6/6 panel" (đã xác nhận).
- [x] `config/slo.yaml` đã có SLO + giải thích error budget sẵn (không cần sửa).
- [x] Hoàn thiện `config/alert_rules.yaml` (3 alert: HighLatencyP95, HighErrorRate, LowRetrievalSuccessRate).
- [x] Viết `docs/alerts.md` (cách kiểm tra + mitigation mỗi alert).
- [x] Viết `scripts/render_dashboard.py` (đọc `data/logs.jsonl` + `config/dashboard.yaml`, xuất `data/dashboard.html` đủ 6 panel, time range, đơn vị, threshold) vì repo không có sẵn công cụ dashboard runtime.
- [x] `evidence/03-dashboard-validator.png` đã có sẵn (output validator 6/6).
- [x] **Chụp:** `evidence/11-dashboard-overview.png` — chạy `python scripts/render_dashboard.py` rồi mở `data/dashboard.html` trong trình duyệt, chụp toàn trang.
- [x] Điền mục 6 (Dashboard, SLO, alerts) trong `REPORT.md`, dẫn link `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md`.

## CP3 — Challenge chính thức (chỉ khi Lab Coach mở challenge)

- [x] Nhận file riêng từ Lab Coach, lưu vào `config/challenge.json` (đã gitignore — KHÔNG force-add/commit/push). Challenge ID: `day13-k4-l3b-monitoring-llmops-v1`.
- [x] Chạy `python scripts/inject_incident.py`.
- [x] Chạy `python scripts/load_test.py --challenge --concurrency 5`.
- [x] Điều tra theo thứ tự bắt buộc:
  - [x] 1. Xem dashboard → latency P95 tăng lên 2636.8ms (ngưỡng 3000ms).
  - [x] 2. Lọc `data/logs.jsonl` trong khoảng đó → `correlation_id: "req-52415b45"` (4248ms).
  - [x] 3. Tìm trace cùng `correlation_id` (`dab4b7e049deaa5741f037a393e7e39c`) → span `retrieval` chiếm 2.50s/4.25s.
  - [x] 4. Root cause: retrieval chậm (khớp kịch bản `rag_slow`).
- [x] **Chụp:**
  - [x] `evidence/12-incident-metric.png`
  - [x] `evidence/13-incident-log.png`
  - [x] `evidence/14-incident-trace.png`
- [x] Điền mục 7 (Điều tra challenge) trong `REPORT.md`: challenge ID, khoảng thời gian, triệu chứng, log line, trace/span, root cause, fix action, preventive measure.

## CP4 — Report, evidence, kiểm tra cuối

- [x] Chạy lại toàn bộ trước khi commit: `pytest` (22 passed), `validate_logs.py` (100/100), `validate_dashboard.py` (6/6).
- [x] Cập nhật cột "Kết quả cuối" trong bảng mục 3 `REPORT.md`.
- [x] Hoàn thiện mục 1 (thông tin học viên, Repository URL đã điền), mục 2 (evidence index — đã sửa path 08/10a/10b đúng), mục 8 (tự đánh giá).
- [x] Rà soát an toàn trước khi push:
  - [x] Xác nhận `.env`, `config/challenge.json`, `data/logs.jsonl` đều trong `.gitignore`; thêm `data/dashboard.html` vào `.gitignore` (file build tạm).
  - [x] Không có PII thô hoặc evidence của người khác/lớp khác; `sk-lf-` chỉ xuất hiện dạng placeholder trong docs gốc, không phải key thật.
  - [x] Mọi ảnh trong `REPORT.md` dùng path tương đối và mở được (đã sửa file bị đặt tên sai `.png.png`/ký tự ẩn: 08, 08a/08b cũ).
- [x] Tick checklist mục 9 trong `REPORT.md` (còn 2 mục chờ bạn tự làm: commit SHA cuối + nộp LMS).
- [ ] **Việc của bạn:** Commit các thay đổi (`git add`, `git commit`), lấy commit SHA (`git log -1 --oneline`), điền vào mục 1 `REPORT.md`, rồi push và nộp URL repo + SHA lên LMS/Codelabs.

## Mẹo tránh rườm rà

- Sau mỗi lần sửa xong 1 TODO nhỏ, chạy ngay lệnh validator liên quan thay vì đợi sửa hết mới chạy — tránh phải debug dồn.
- Đặt tên evidence đúng số thứ tự trong `submission/evidence/README.md` ngay từ đầu để khỏi đổi tên lại.
- Điền `REPORT.md` theo từng mục ngay sau khi xong phần đó (không để cuối buổi mới viết), vì mỗi mục cần khớp với evidence vừa chụp.
