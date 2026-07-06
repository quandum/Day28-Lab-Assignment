# BÁO CÁO & HƯỚNG DẪN NỘP BÀI - Lab #28: Full Platform Integration Sprint

**Học viên:** Trần Mạnh Chánh Quân  
**Mã học viên:** 2A202600786  
**Môn học:** AICB-P2T2 · Chương 6: Tổng Hợp  
**Ngày thực hiện:** 06/07/2026  

---

## KẾT QUẢ THỰC HIỆN

### Services (9/9 Up)

| Service | Port | Trạng thái |
|---------|------|-----------|
| Zookeeper | 2181 | ✅ |
| Kafka | 9092 | ✅ |
| Prefect Orion | 4200 | ✅ |
| Prefect Worker | - | ✅ |
| Qdrant | 6333 | ✅ |
| Redis (Feast) | 6379 | ✅ |
| Prometheus | 9090 | ✅ |
| Grafana | 3000 | ✅ |
| API Gateway | 8000 | ✅ |

### 10 Integration Points

| # | Integration | Trạng thái |
|---|-------------|-----------|
| 1 | Data → Kafka | ✅ |
| 2 | Kafka → Prefect → Delta Lake | ✅ |
| 3 | Delta Lake → Feast (Redis) | ✅ |
| 4 | Feast Online Serving | ✅ |
| 5 | Embedding → Qdrant | ✅ |
| 6 | API Gateway → Qdrant (Vector Search) | ✅ |
| 7 | API Gateway → vLLM (LLM Inference) | ✅ |
| 8 | API Gateway → Response | ✅ |
| 9 | Prometheus Metrics | ✅ |
| 10 | LangSmith Tracing | ⚠️ (cấu hình sẵn, chưa có traces) |

### Smoke Tests: 8/8 PASSED ✅

```
smoke-tests/test_e2e.py::TestHappyPath::test_full_inference_returns_200 PASSED
smoke-tests/test_e2e.py::TestHappyPath::test_health_check_passes PASSED
smoke-tests/test_e2e.py::TestDataIngestion::test_kafka_ingest_and_qdrant_store PASSED
smoke-tests/test_e2e.py::TestObservability::test_prometheus_scrapes_api_gateway PASSED
smoke-tests/test_e2e.py::TestObservability::test_grafana_dashboard_accessible PASSED
smoke-tests/test_e2e.py::TestFailurePath::test_invalid_request_returns_422 PASSED
smoke-tests/test_e2e.py::TestFailurePath::test_timeout_handled_gracefully PASSED
smoke-tests/test_e2e.py::TestFeatureStore::test_feast_redis_has_features PASSED
```

### Production Readiness: 100% ✅

```
RELIABILITY:     Health check endpoint [PASS], API Gateway responds [PASS]
OBSERVABILITY:   Prometheus up [PASS], Grafana up [PASS], Metrics exposed [PASS]
SECURITY:        Unauthorized request rejected [PASS]
VECTOR STORE:    Qdrant healthy [PASS], Collection exists [PASS]
FEATURE STORE:   Redis reachable [PASS]
KAFKA:           Topics exist [PASS]
Score: 10/10 = 100%
```

### Screenshots Demo (7 ảnh)

| File | Nội dung |
|------|----------|
| `screenshots/prefect_ui.png` | Prefect Flow Runs với lab28-demo-run COMPLETED |
| `screenshots/api_gateway.png` | API Gateway health + chat response |
| `screenshots/grafana_dashboard.png` | Grafana dashboard Lab28 - AI Platform |
| `screenshots/prometheus_targets.png` | Prometheus targets: api-gateway, kafka, prefect-orion UP |
| `screenshots/qdrant_dashboard.png` | Qdrant collection `documents` |
| `screenshots/smoke_tests_results.png` | pytest 8/8 passed |
| `screenshots/production_readiness.png` | Production Readiness 100% |

---

## Yêu Cầu Nộp Bài

**Full AI infrastructure platform demo** - từ data ingestion đến model serving với full observability.

## Các Artifacts Cần Nộp

### 1. Source Code
- Folder `lab28/` hoàn chỉnh với tất cả files
- Tất cả integration scripts hoạt động
- Prefect flows đã deploy và schedule

### 2. Screenshots Demo
Chụp màn hình các bước:
- Prefect UI: http://localhost:4200 (flow đang chạy)
- API Gateway call: `curl http://localhost:8000/health`
- Grafana dashboard: http://localhost:3000

### 3. Kết Quả Smoke Tests
Chạy và chụp màn hình kết quả:
```bash
cd lab28
pytest smoke-tests/ -v
```
Kỳ vọng: 5/5 tests passing

### 4. Production Readiness Score
```bash
python scripts/production_readiness_check.py
```
Kỳ vọng: Score >80%

### 5. Documentation
- `README.md` giải thích cách:
  - Start platform: `docker compose up -d`
  - Deploy Prefect flows
  - Run smoke tests
  - Access dashboards (Grafana:3000, Prometheus:9090, Prefect:4200)

## Định Dạng Nộp Bài

Tạo Repo GitHub chứa:
```
lab28_submission_[student_id]
├── lab28/                    # Source code hoàn chỉnh
│   ├── docker-compose.yml
│   ├── prefect/flows/
│   ├── scripts/
│   ├── api-gateway/
│   └── monitoring/
├── screenshots/              # Screenshots demo
│   ├── prefect_ui.png
│   ├── api_gateway.png
│   └── grafana_dashboard.png
├── smoke_tests_results.png   # Screenshot kết quả pytest
├── production_readiness.png  # Screenshot readiness score
└── README.md                # Hướng dẫn setup
```

## Địa Điểm Nộp
Nộp link repo GitHub qua LMS

## Tiêu Chí Chấm Điểm

| Tiêu Chí | Trọng Số | Mô Tả |
|----------|----------|-------|
| Integration Completeness | 40% | Tất cả 10 integration points hoạt động, data flow end-to-end |
| Observability | 25% | Logs, metrics, traces hiển thị; alerts configured |
| Performance | 20% | Latency trong SLO; load tested; không có memory leaks |
| Architecture Quality | 15% | Clean separation, GitOps config, documented decisions |

## Các Vấn Đề Cần Tránh

- Config drift giữa các environments
- Thiếu error handling tại integration points
- Monitoring coverage không hoàn chỉnh
- Không có rollback strategy
- Demo không test trước khi nộp

## 5 Câu Hỏi Cần Trả Lời Khi Nộp

1. **Phân tích các trade-offs trong thiết kế kiến trúc AI platform của bạn. Bạn đã cân bằng giữa performance, reliability, và maintainability như thế nào?**

> **Trade-offs chính:**
> - **Performance vs Cost:** Chạy LLM inference trên Kaggle GPU (free T4) thay vì local GPU → latency cao hơn do qua ngrok tunnel (~80-200ms network overhead) nhưng tiết kiệm chi phí.
> - **Reliability vs Simplicity:** Dùng Kafka làm message broker đảm bảo dữ liệu không bị mất khi consumer gặp sự cố (at-least-once delivery), nhưng tăng độ phức tạp hệ thống.
> - **Maintainability:** Tách biệt local infrastructure (Docker Compose) và GPU compute (Kaggle) → dễ bảo trì từng phần, nhưng thêm điểm failure ở ngrok tunnel.
> 
> **Cân bằng:** Ưu tiên reliability (Kafka, retry logic) và maintainability (Docker hóa toàn bộ local stack), chấp nhận latency network cho GPU inference vì không có GPU local.

2. **Trong kiến trúc hybrid (Local + Kaggle), bạn xử lý ngắt kết nối giữa local và Kaggle như thế nào? Có cơ chế fallback không?**

> - **Phát hiện:** API Gateway có timeout 30s khi gọi vLLM; nếu không phản hồi → trả về lỗi 500.
> - **Fallback:** Mock LLM server local (`scripts/mock_llm_server.py`) chạy trên port 8001 để test integration khi Kaggle không sẵn sàng. Trong production, có thể dùng circuit breaker pattern (dừng gọi sau N lần fail liên tiếp).
> - **Retry:** Kafka consumer tự động retry khi mất kết nối; Prefect flow có thể schedule retry.
> - **Graceful degradation:** API Gateway vẫn serve health check và metrics ngay cả khi Kaggle offline.

3. **Giải thích cách event-driven architecture với Kafka giúp decouple các components trong AI platform của bạn.**

> Kafka hoạt động như central message bus:
> - **Producer (Data Ingestion)** gửi dữ liệu vào topic `data.raw` mà không cần biết ai sẽ consume.
> - **Consumer (Prefect Flow)** đọc từ Kafka và ghi vào Delta Lake độc lập, không blocking producer.
> - **Downstream services** (Feast, Qdrant) đọc từ Delta Lake mà không phụ thuộc vào Kafka consumer.
> - **Lợi ích:** Có thể thêm consumer mới (ví dụ: real-time alerting) mà không cần sửa producer; mỗi component scale độc lập; dữ liệu được buffer trong Kafka nếu consumer tạm dừng.

4. **Bạn đã implement observability như thế nào? Logs, metrics, và traces được thu thập và visualized ra sao?**

> - **Metrics:** Prometheus scrape `/metrics` từ API Gateway (qua `prometheus-fastapi-instrumentator`), Kafka, Prefect. Metrics chính: `http_requests_total`, `up`, latency.
> - **Visualization:** Grafana dashboard "Lab28 - AI Platform" hiển thị API Gateway requests và uptime từ Prometheus datasource.
> - **Traces:** LangSmith API key đã cấu hình qua `LANGCHAIN_API_KEY` và `LANGCHAIN_PROJECT=lab28-platform` để trace toàn bộ pipeline execution.
> - **Logs:** Docker Compose logs (`docker compose logs <service>`) cho debugging; API Gateway log mỗi request với status code.

5. **Nếu một service trong stack (ví dụ: Qdrant hoặc Kafka) bị crash, hệ thống của bạn sẽ xử lý như thế nào? Có graceful degradation không?**

> - **Kafka crash:** Producer không gửi được → lỗi được log, retry khi Kafka up lại. Consumer không mất dữ liệu vì offset được lưu. Cần Kafka để ingest data mới, nhưng các service khác (Qdrant, API Gateway) vẫn hoạt động.
> - **Qdrant crash:** API Gateway không lấy được context từ vector search → fallback: gửi prompt không có context đến LLM (vẫn trả lời được, chỉ thiếu RAG). Health check vẫn OK.
> - **Redis crash:** Feature store không truy xuất được → API Gateway vẫn hoạt động bình thường (không phụ thuộc trực tiếp).
> - **Prefect crash:** Không ảnh hưởng real-time serving; flow có thể chạy thủ công khi Prefect up lại.
> - **Docker Compose restart policy:** Cấu hình `restart: always` trong production để tự động khôi phục.

## Câu Hỏi Thêm?
Liên hệ giảng viên qua LMS hoặc office hours.
