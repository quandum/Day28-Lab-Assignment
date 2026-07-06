# KẾ HOẠCH THỰC HIỆN — Lab #28: Full Platform Integration Sprint

**Học viên:** Trần Mạnh Chánh Quân  
**Mã học viên:** 2A202600786  
**Môn học:** AICB-P2T2 · Chương 6: Tổng Hợp  
**Thời gian dự kiến:** 2 giờ  

---

## TỔNG QUAN

Xây dựng AI platform hoàn chỉnh với kiến trúc hybrid (Local Docker Compose + Kaggle GPU), kết nối end-to-end qua 10 integration points, có đầy đủ observability (Prometheus + Grafana + LangSmith).

```
Local (Docker)                          Kaggle (GPU T4)
─────────────                          ────────────────
Kafka → Prefect → Delta Lake → Feast   vLLM serving
  ↓                ↓                   Embedding service
Qdrant         API Gateway ←───ngrok─── MLflow tracking
  ↓                ↓
Prometheus ←── Grafana
  ↓
LangSmith tracing
```

---

## PHẦN 0 — CHUẨN BỊ MÔI TRƯỜNG (10 phút)

| # | Công việc | Mô tả chi tiết | Kết quả mong đợi |
|---|-----------|----------------|-------------------|
| 0.1 | Kiểm tra Docker | `docker --version`, đảm bảo Docker Desktop đang chạy | Docker sẵn sàng |
| 0.2 | Kiểm tra Python | `python --version` → 3.10+ | Python 3.10+ |
| 0.3 | Cài đặt ngrok | `ngrok config add-authtoken <TOKEN>` (lấy từ ngrok.com) | ngrok sẵn sàng |
| 0.4 | Kiểm tra file `.env` | Tạo file `.env` với VLLM_NGROK_URL, EMBED_NGROK_URL, LANGCHAIN_API_KEY | `.env` đã sẵn sàng |
| 0.5 | Tạo thư mục còn thiếu | `mkdir -p delta-lake/raw` | Cấu trúc thư mục hoàn chỉnh |

---

## PHẦN 1 — DỰNG INFRASTRUCTURE LOCAL (Docker Compose) (20 phút)

| Bước | Công việc | Câu lệnh / Thao tác | Kết quả mong đợi |
|------|-----------|---------------------|-------------------|
| 1.1 | Khởi động toàn bộ stack | `docker compose up -d` | Tất cả containers chạy |
| 1.2 | Kiểm tra trạng thái | `docker compose ps` | Tất cả services `Up` |
| 1.3 | Kiểm tra Prefect UI | Mở http://localhost:4200 | Prefect dashboard hiển thị |
| 1.4 | Kiểm tra Grafana | Mở http://localhost:3000 (admin/admin) | Grafana dashboard hiển thị |
| 1.5 | Kiểm tra Qdrant | Mở http://localhost:6333/dashboard | Qdrant dashboard hiển thị |
| 1.6 | Kiểm tra Prometheus | Mở http://localhost:9090 | Prometheus UI hiển thị |
| 1.7 | Kiểm tra API Gateway | `curl http://localhost:8000/health` | `{"status": "ok"}` |

**Services cần chạy (8 services):**
- zookeeper (port 2181)
- kafka (port 9092)
- prefect-orion (port 4200)
- prefect-worker
- qdrant (port 6333)
- redis (port 6379)
- prometheus (port 9090)
- grafana (port 3000)
- api-gateway (port 8000)

---

## PHẦN 2 — KAGGLE GPU SETUP & EXPOSE QUA TUNNEL (25 phút)

### 2.1 Tạo Kaggle Notebook + Bật GPU T4 x2

| Bước | Công việc | Chi tiết |
|------|-----------|----------|
| 2.1.1 | Tạo Kaggle Notebook mới | Vào Kaggle → Create → New Notebook |
| 2.1.2 | Bật GPU | Settings → Accelerator → GPU T4 x2 |
| 2.1.3 | Chọn Option | **Khuyến nghị: Option A (Single GPU)** đơn giản hơn |

### 2.2 Chạy các Cell trong Kaggle Notebook (Option A - Single GPU)

| Cell | Nội dung | Thời gian chờ |
|------|----------|---------------|
| Cell 1 | `!pip install -q vllm fastapi uvicorn pyngrok mlflow sentence-transformers` | ~2 phút |
| Cell 2 | Setup ngrok auth token: `ngrok.set_auth_token("YOUR_NGROK_TOKEN")` | Vài giây |
| Cell 3 | Khởi động vLLM server (port 8001) với model `Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4` | ~60 giây |
| Cell 4 | Tạo ngrok tunnel → Lấy **VLLM_NGROK_URL** | Vài giây |
| Cell 5 | Khởi động Embedding API server (port 8002) với model `BAAI/bge-small-en-v1.5` | ~30 giây |
| Cell 6 | Tạo ngrok tunnel cho embedding → Lấy **EMBED_NGROK_URL** | Vài giây |

### 2.3 Cập nhật file `.env` trên Local

```bash
# Sao chép 2 URL từ output của Kaggle Notebook vào file .env:
VLLM_NGROK_URL=https://xxxx.ngrok-free.app
EMBED_NGROK_URL=https://yyyy.ngrok-free.app
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=lab28-platform
```

**Kiểm tra kết nối:**
```bash
curl $VLLM_NGROK_URL/v1/models        # Phải trả về model list
curl $EMBED_NGROK_URL/embed           # Phải trả về 200 OK
```

---

## PHẦN 3 — KẾT NỐI 10 INTEGRATION POINTS (35 phút)

### Integration 1: Data Ingestion → Kafka

| Bước | Thao tác | Lệnh | Kết quả |
|------|----------|------|---------|
| 3.1.1 | Chạy script ingest | `python scripts/01_ingest_to_kafka.py` | "Integration 1 OK: Data → Kafka" |
| 3.1.2 | Kiểm tra Kafka topic | `docker exec lab28-kafka-1 kafka-topics --list --bootstrap-server localhost:9092` | Thấy topic `data.raw` |

### Integration 2: Kafka → Prefect Pipeline

| Bước | Thao tác | Lệnh | Kết quả |
|------|----------|------|---------|
| 3.2.1 | Cài Prefect flow dependencies | `cd prefect/flows && pip install -r requirements.txt` | Packages installed |
| 3.2.2 | Deploy Prefect flow | `python kafka_to_delta.py` | Flow deployed to Prefect Orion |
| 3.2.3 | Kiểm tra Prefect UI | Mở http://localhost:4200 → Flows | Thấy flow `Kafka to Delta Pipeline` |
| 3.2.4 | Chạy flow lần đầu | Trigger flow từ Prefect UI hoặc CLI | Flow chạy thành công |

### Integration 3-4: Delta Lake → Feast (Redis)

| Bước | Thao tác | Lệnh | Kết quả |
|------|----------|------|---------|
| 3.3.1 | Chạy script delta_to_feast | `python scripts/03_delta_to_feast.py` | "Integration 3+4 OK: Delta Lake → Feast" |
| 3.3.2 | Kiểm tra Redis | `redis-cli KEYS "feature:*"` | Thấy feature keys |

### Integration 5: Embed → Qdrant

| Bước | Thao tác | Lệnh | Kết quả |
|------|----------|------|---------|
| 3.4.1 | Chạy script embed_to_qdrant | `python scripts/05_embed_to_qdrant.py` | "Integration 5 OK: vectors stored in Qdrant" |
| 3.4.2 | Kiểm tra Qdrant collection | Mở http://localhost:6333/dashboard → Collections | Thấy collection `documents` |

### Integration 6-7-8: API Gateway (FastAPI) → Qdrant → vLLM

| Bước | Thao tác | Lệnh | Kết quả |
|------|----------|------|---------|
| 3.5.1 | Kiểm tra health | `curl http://localhost:8000/health` | `{"status":"ok"}` |
| 3.5.2 | Test chat endpoint | `curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"query":"What is AI?","embedding":[0.1]*384}'` | Nhận được answer từ LLM + latency_ms |

### Integration 9: Prometheus Metrics

| Bước | Thao tác | Lệnh | Kết quả |
|------|----------|------|---------|
| 3.6.1 | Kiểm tra metrics endpoint | `curl http://localhost:8000/metrics` | Thấy `http_requests_total` |
| 3.6.2 | Kiểm tra Prometheus scrape | Vào http://localhost:9090 → Status → Targets | Tất cả targets UP |
| 3.6.3 | Chạy verify script | `python scripts/09_verify_observability.py` | "Integration 9 OK" |

### Integration 10: LangSmith Tracing

| Bước | Thao tác | Lệnh | Kết quả |
|------|----------|------|---------|
| 3.7.1 | Kiểm tra LangSmith API key | Đảm bảo `LANGCHAIN_API_KEY` trong `.env` | Key hợp lệ |
| 3.7.2 | Verify LangSmith traces | Script `09_verify_observability.py` sẽ kiểm tra | "Integration 10 OK" |

---

## PHẦN 4 — KIỂM TRA & VALIDATE (20 phút)

### 4.1 Smoke Tests (End-to-End)

| Bước | Thao tác | Lệnh | Kết quả mong đợi |
|------|----------|------|-------------------|
| 4.1.1 | Cài pytest | `pip install pytest kafka-python redis requests` | Packages installed |
| 4.1.2 | Chạy smoke tests | `pytest smoke-tests/ -v` | **5/5 tests PASSED** |
| 4.1.3 | Chụp màn hình kết quả | Screenshot terminal output | Lưu vào thư mục `screenshots/` |

**5 tests cần pass:**
1. `test_full_inference_returns_200` — API Gateway trả về answer từ LLM
2. `test_health_check_passes` — Health check OK
3. `test_kafka_ingest_and_qdrant_store` — Data flow từ Kafka → Qdrant
4. `test_prometheus_scrapes_api_gateway` — Prometheus scrape metrics
5. `test_grafana_dashboard_accessible` — Grafana dashboard load được
6. `test_invalid_request_returns_422` — Error handling hoạt động
7. `test_timeout_handled_gracefully` — Timeout không crash
8. `test_feast_redis_has_features` — Feature store có dữ liệu

### 4.2 Production Readiness Check

| Bước | Thao tác | Lệnh | Kết quả mong đợi |
|------|----------|------|-------------------|
| 4.2.1 | Chạy readiness check | `python scripts/production_readiness_check.py` | **Score >80%** |
| 4.2.2 | Chụp màn hình kết quả | Screenshot terminal output | Lưu vào `screenshots/` |

**Các mục kiểm tra:**
- RELIABILITY: Health check, API Gateway responds
- OBSERVABILITY: Prometheus up, Grafana up, Metrics exposed
- SECURITY: Unauthorized request rejected
- VECTOR STORE: Qdrant healthy, Collection exists
- FEATURE STORE: Redis reachable
- KAFKA: Topics exist

---

## PHẦN 5 — CHỤP ẢNH DEMO (10 phút)

| # | Ảnh cần chụp | URL / Lệnh | Lưu thành |
|---|-------------|------------|-----------|
| 5.1 | Prefect UI (flow đang chạy) | http://localhost:4200 | `screenshots/prefect_ui.png` |
| 5.2 | API Gateway health check | `curl http://localhost:8000/health` | `screenshots/api_gateway.png` |
| 5.3 | Grafana dashboard | http://localhost:3000 | `screenshots/grafana_dashboard.png` |
| 5.4 | Prometheus targets | http://localhost:9090/targets | `screenshots/prometheus_targets.png` |
| 5.5 | Qdrant dashboard | http://localhost:6333/dashboard | `screenshots/qdrant_dashboard.png` |
| 5.6 | Smoke test results | Terminal output | `screenshots/smoke_tests_results.png` |
| 5.7 | Production readiness score | Terminal output | `screenshots/production_readiness.png` |

---

## PHẦN 6 — HOÀN THIỆN BÁO CÁO & NỘP BÀI (10 phút)

| Bước | Công việc | Chi tiết |
|------|-----------|----------|
| 6.1 | Cập nhật `report.md` | Điền thông tin cá nhân, kết quả, trả lời 5 câu hỏi |
| 6.2 | Kiểm tra cấu trúc thư mục | Đảm bảo đúng format trong `SUBMISSION.md` |
| 6.3 | Tạo GitHub repo | `lab28_submission_2A202600786` |
| 6.4 | Push code lên GitHub | Tất cả source code + screenshots + README.md + report.md |
| 6.5 | Nộp link GitHub qua LMS | Copy link repo → Nộp lên LMS |

---

## CẤU TRÚC THƯ MỤC NỘP BÀI

```
lab28_submission_2A202600786/
├── lab28/                          # Source code hoàn chỉnh
│   ├── docker-compose.yml
│   ├── .env
│   ├── api-gateway/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── prefect/
│   │   └── flows/
│   │       ├── kafka_to_delta.py
│   │       └── requirements.txt
│   ├── scripts/
│   │   ├── 01_ingest_to_kafka.py
│   │   ├── 03_delta_to_feast.py
│   │   ├── 05_embed_to_qdrant.py
│   │   ├── 09_verify_observability.py
│   │   └── production_readiness_check.py
│   ├── monitoring/
│   │   └── prometheus.yml
│   ├── smoke-tests/
│   │   └── test_e2e.py
│   ├── delta-lake/
│   │   └── raw/
│   └── feast/
├── screenshots/                    # Screenshots demo
│   ├── prefect_ui.png
│   ├── api_gateway.png
│   ├── grafana_dashboard.png
│   ├── prometheus_targets.png
│   ├── qdrant_dashboard.png
│   ├── smoke_tests_results.png
│   └── production_readiness.png
├── work_plan.md                    # File kế hoạch này
├── report.md                       # Báo cáo tổng kết
└── README.md                       # Hướng dẫn setup
```

---

## BẢNG TIẾN ĐỘ THEO DÕI

| Phần | Nội dung | Thời gian | Trạng thái |
|------|----------|-----------|------------|
| 0 | Chuẩn bị môi trường | 10 phút | ⬜ Chưa làm |
| 1 | Dựng Infrastructure Local | 20 phút | ⬜ Chưa làm |
| 2 | Kaggle GPU Setup | 25 phút | ⬜ Chưa làm |
| 3 | Kết nối 10 Integration Points | 35 phút | ⬜ Chưa làm |
| 4 | Kiểm tra & Validate | 20 phút | ⬜ Chưa làm |
| 5 | Chụp ảnh Demo | 10 phút | ⬜ Chưa làm |
| 6 | Hoàn thiện & Nộp bài | 10 phút | ⬜ Chưa làm |
| **Tổng** | | **~130 phút** | |

---

## LƯU Ý QUAN TRỌNG

1. **Thứ tự thực hiện:** Phải làm tuần tự từ Phần 0 → Phần 6, không được đảo lộn vì mỗi phần phụ thuộc vào phần trước.
2. **Kaggle GPU session:** Có giới hạn thời gian (~9h/tuần với GPU T4). Hãy đảm bảo tắt session sau khi lấy URL.
3. **ngrok URL thay đổi:** Mỗi lần chạy lại Kaggle Notebook, ngrok URL sẽ khác → Cần cập nhật lại file `.env`.
4. **Docker resources:** Đảm bảo Docker có ít nhất 8GB RAM để chạy được toàn bộ stack.
5. **Port conflicts:** Kiểm tra không có service nào khác đang chiếm các port: 2181, 9092, 4200, 6333, 6379, 9090, 3000, 8000.
