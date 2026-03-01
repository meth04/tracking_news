# Báo cáo dự án đầy đủ: Hệ thống thu thập và phân tích tin tức tài chính Việt Nam

## 1. Tổng quan dự án

### 1.1 Bối cảnh

Thị trường tài chính Việt Nam có tốc độ biến động cao, tin tức xuất hiện liên tục từ nhiều nguồn (CafeF, VnExpress, Vietstock, RSS tổng hợp). Việc theo dõi thủ công có ba hạn chế chính:

1. **Độ trễ cao**: Nhà đầu tư/công cụ phân tích nhận thông tin chậm.
2. **Dữ liệu phân mảnh**: Tin tức nằm rải rác, khó tổng hợp nhanh theo chủ đề/ngày/mã cổ phiếu.
3. **Thiếu chuẩn hóa**: Cùng một sự kiện có thể xuất hiện dưới nhiều URL/tiêu đề khác nhau, gây nhiễu.

### 1.2 Mục tiêu dự án

Dự án hướng đến xây dựng một pipeline end-to-end:

- Thu thập tự động tin tức tài chính từ nhiều nguồn.
- Chuẩn hóa và khử trùng lặp dữ liệu.
- Bổ sung lớp NLP để trích xuất tín hiệu hữu ích:
  - mã chứng khoán liên quan,
  - cảm xúc tin tức,
  - mức độ tác động (impact).
- Lưu trữ song song:
  - dữ liệu quan hệ (DB) để truy vấn nghiệp vụ,
  - vector embeddings để truy vấn ngữ nghĩa.
- Cung cấp lớp phục vụ:
  - CLI cho vận hành,
  - MCP Server cho AI agents,
  - Dashboard trực quan cho giám sát.

### 1.3 Phạm vi hiện tại

Đã triển khai được các năng lực chính:

- Crawl nhiều nguồn (RSS + crawler theo site).
- Chạy định kỳ dạng daemon.
- NLP pipeline hoàn chỉnh (cleaning, NER ticker, sentiment, impact, embeddings).
- Dashboard giám sát đa trang + tổng hợp theo ngày + trang chi tiết bài báo.
- Đánh giá chất lượng pipeline bằng lệnh CLI `evaluate`.

---

## 2. Kiến trúc tổng thể

Hệ thống theo mô hình pipeline nhiều lớp, phân tách rõ thu thập, xử lý và phục vụ.

### 2.1 Các lớp chính

1. **Acquisition layer** (`src/news_ingestor/crawlers/`)
   - `BaseCrawler` làm khung chung cho retry/rate-limit/user-agent rotation.
   - Các crawler nguồn: `RSSCrawler`, `CafeFCrawler`, `VnExpressCrawler`, `VietStockCrawler`.
   - `BoLichThuThap` điều phối nhiều crawler theo chu kỳ.

2. **Processing layer** (`src/news_ingestor/processing/`)
   - `BoLamSach`: làm sạch văn bản.
   - `ContentFetcher`: lấy full content từ URL gốc.
   - `BoTrichXuatThucThe`: trích xuất mã CK + phân loại danh mục.
   - `BoPhanTichCamXuc`: sentiment (Gemini hoặc từ điển fallback).
   - `BoPhanLoaiTacDong`: chấm impact score/level/tags.
   - `BoTaoEmbeddings`: sinh vector embeddings.
   - `LuongXuLy`: orchestration toàn pipeline cho từng bài và theo batch.

3. **Persistence layer** (`src/news_ingestor/storage/`)
   - `database.py`: SQLAlchemy engine + schema + migration nhẹ cho SQLite.
   - `repository.py`: truy vấn nghiệp vụ.
   - `vector_store.py`: tích hợp Qdrant, có fallback in-memory nếu mất kết nối.

4. **Serving layer**
   - CLI: `src/news_ingestor/cli.py`
   - MCP: `src/news_ingestor/mcp_server/server.py`
   - Dashboard: `dashboard.py`

### 2.2 Luồng dữ liệu từ đầu đến cuối

1. Scheduler gọi các crawler.
2. Crawler trả về danh sách `BaiBaoTho`.
3. Scheduler dedup sơ cấp theo `url_chuan_hoa` và `tieu_de_hash`.
4. Callback đẩy vào `LuongXuLy`.
5. Pipeline thực hiện làm sạch, enrich NLP, tạo embedding.
6. Lưu `BaiBao` vào DB, lưu vector + metadata vào Vector DB.
7. Nếu impact cao và bật alert: gửi Telegram.
8. Dashboard/CLI/MCP đọc dữ liệu đã chuẩn hóa để phục vụ người dùng hoặc agent.

---

## 3. Thiết kế dữ liệu

### 3.1 Mô hình dữ liệu nghiệp vụ

- `BaiBaoTho` (raw): dữ liệu ngay sau crawler.
- `BaiBao` (processed): bản ghi chuẩn hóa đầy đủ để phục vụ truy vấn và phân tích.

Các trường quan trọng:

- Định danh và dedup: `id`, `url`, `url_chuan_hoa`, `tieu_de_hash`
- Nội dung: `tieu_de`, `noi_dung_tom_tat`, `noi_dung_goc`
- Metadata nguồn: `nguon_tin`, `thoi_gian_xuat_ban`, `danh_muc`
- NLP outputs: `ma_chung_khoan_lien_quan`, `diem_cam_xuc`, `nhan_cam_xuc`
- Impact outputs: `impact_score`, `impact_level`, `impact_tags`, `is_high_impact`
- Vector linkage: `vector_id`
- Trạng thái xử lý: `trang_thai`

### 3.2 Schema database

Bảng chính: `tin_tuc_tai_chinh` (ORM `BangTinTuc`)

Điểm nổi bật:

- `url_chuan_hoa` unique giúp giảm duplicate do query params/alias URL.
- Index cho `impact_level`, `is_high_impact`, `tieu_de_hash`.
- Lưu danh sách mã CK dưới dạng JSON string để tương thích SQLite.

Bảng phụ trợ: `nhat_ky_thu_thap` cho theo dõi phiên crawl.

### 3.3 Chiến lược dedup

Dedup dùng hai trục:

1. **Canonical URL** (`url_chuan_hoa`) – tránh duplicate cùng bài khác tracking params.
2. **Hash tiêu đề chuẩn hóa** (`tieu_de_hash`) – giảm duplicate khi URL khác nhưng headline trùng sự kiện.

---

## 4. Thành phần crawl và scheduler

### 4.1 BaseCrawler

`BaseCrawler` cung cấp các cơ chế chuẩn:

- HTTP GET với retry nhiều lần.
- Backoff theo số lần lỗi.
- Luân phiên User-Agent.
- Delay ngẫu nhiên giữa request để giảm nguy cơ bị chặn.
- Bắt lỗi status/timeout có log đầy đủ.

### 4.2 Crawler theo nguồn

- `RSSCrawler`: đọc danh sách feed từ `config/feeds.json`.
- `CafeFCrawler`: parse các mục chứng khoán/vĩ mô/doanh nghiệp.
- `VnExpressCrawler`: parse mục kinh doanh/chứng khoán/BĐS.
- `VietStockCrawler`: parse mục chứng khoán/doanh nghiệp/tài chính.

Mỗi crawler có:

- selector chính theo cấu trúc HTML phổ biến,
- fallback strategy khi selector chính thất bại,
- parse timestamp với chuẩn UTC.

### 4.3 Scheduler daemon

`BoLichThuThap` hỗ trợ:

- `chay_mot_lan`: chạy một chu kỳ crawl.
- `chay_daemon`: chạy liên tục theo `interval`.
- Exponential backoff khi lỗi liên tiếp (giới hạn tối đa), giúp hệ thống ổn định hơn khi nguồn lỗi tạm thời.

---

## 5. NLP pipeline chi tiết

`LuongXuLy` là trung tâm xử lý nghiệp vụ.

### 5.1 Bước 0 – Fetch full content

`ContentFetcher` truy cập URL gốc để lấy nội dung đầy đủ (không chỉ summary RSS). Đây là bước quan trọng giúp cải thiện chất lượng sentiment và impact.

### 5.2 Bước 1 – Cleaning

`BoLamSach` thực hiện:

- loại HTML,
- sửa ký tự lỗi Unicode,
- loại mẫu quảng cáo/boilerplate,
- chuẩn hóa khoảng trắng,
- cắt tóm tắt theo ranh giới câu.

### 5.3 Bước 2 – Entity extraction + category

`BoTrichXuatThucThe` dùng từ điển `tickers.json` để:

- phát hiện mã CK từ từ khóa và regex,
- phân loại danh mục bài (vi mô/ngành/vĩ mô) theo scoring từ khóa.

### 5.4 Bước 3 – Sentiment

`BoPhanTichCamXuc` hoạt động 2 chế độ:

- **Gemini** (nếu có key): ưu tiên độ chính xác ngữ cảnh.
- **Keyword fallback**: chạy offline, ổn định.

Đầu ra:

- nhãn cảm xúc,
- điểm trong [-1, 1],
- cờ tin đồn.

### 5.5 Bước 4 – Impact classification

`BoPhanLoaiTacDong` chấm tác động tài chính và gán:

- `impact_score` (điểm),
- `impact_level` (LOW/MEDIUM/HIGH),
- `impact_tags`,
- `is_high_impact`.

### 5.6 Bước 5 – Embeddings + vector store

Nếu bật embedding:

- `BoTaoEmbeddings` sinh vector từ văn bản đã làm sạch.
- `KhoVector` lưu vector + metadata vào Qdrant.
- Nếu Qdrant không sẵn sàng, fallback in-memory giúp pipeline không bị dừng cứng.

### 5.7 Bước 6 – Persistence + alert

- Lưu bản ghi đã xử lý vào DB.
- Nếu bài `is_high_impact` và alert bật: gửi Telegram qua `BoCanhBaoTelegram`.

---

## 6. Lớp phục vụ (CLI, MCP, Dashboard)

### 6.1 CLI

Các lệnh vận hành chính:

- `init-db`: khởi tạo DB.
- `crawl --once | --daemon --interval`: chạy crawl + pipeline.
- `high-impact`: lấy danh sách tin tác động cao.
- `stats`: thống kê cảm xúc thị trường.
- `serve-mcp`: chạy server MCP qua stdio.
- `demo`: chạy dashboard Streamlit trên port tự chọn.
- `evaluate`: đánh giá chất lượng pipeline theo cửa sổ thời gian.

### 6.2 MCP Server

MCP server cung cấp tools:

1. `tim_tin_vi_mo`
2. `lay_tin_doanh_nghiep`
3. `tim_kiem_ngu_nghia`
4. `lay_cam_xuc_thi_truong`
5. `lay_metrics`

Mục tiêu: cho phép AI agents truy cập dữ liệu tài chính đã chuẩn hóa theo giao thức MCP.

### 6.3 Dashboard Streamlit

Dashboard gồm nhiều trang phục vụ:

- tổng quan,
- danh sách tin,
- chi tiết bài báo,
- chẩn đoán pipeline,
- nguồn crawl,
- tổng hợp theo ngày.

Cải tiến gần nhất:

- trang chi tiết bài báo dùng khung fit nội dung, không cuộn nội bộ,
- escape text trước render HTML để an toàn hiển thị.

---

## 7. Cấu hình và vận hành

### 7.1 Cấu hình tập trung

`config/settings.py` quản lý các nhóm cấu hình:

- Database (`DATABASE_URL`)
- Qdrant (`QDRANT_URL`, `QDRANT_COLLECTION`)
- NLP (`GEMINI_API_KEY`, `EMBEDDING_MODEL`)
- Crawler (`CRAWL_INTERVAL_MINUTES`, `REQUEST_TIMEOUT`, `MAX_RETRIES`, `USER_AGENT`)
- Hệ thống (`LOG_LEVEL`, `METRICS_ENABLED`, Telegram flags)

Có validator kiểm tra hợp lệ và singleton accessor để dùng xuyên suốt ứng dụng.

### 7.2 Logging

`logging_config.py` hỗ trợ 2 chế độ:

- Console formatter (developer friendly).
- JSON formatter (production/observability friendly).

### 7.3 Alerting

`alerting.py` triển khai Telegram optional alert:

- chỉ hoạt động khi đủ flags + token/chat_id,
- gửi thông báo cho bài có `is_high_impact=True`.

---

## 8. Đánh giá chất lượng hệ thống

### 8.1 Mục tiêu đánh giá

Đánh giá theo 2 hướng:

1. **Độ đúng phân lớp impact** trên tập đã gán nhãn.
2. **Chất lượng vận hành pipeline** trên dữ liệu ingest thực tế.

### 8.2 Module đánh giá đã triển khai

File: `src/news_ingestor/utils/evaluation.py`

Chức năng chính:

- `danh_gia_impact_classifier(...)`
  - Trả về: `so_mau`, `dung`, `accuracy`, `confusion matrix`.
- `tao_bao_cao_pipeline(...)`
  - Tổng hợp KPI theo cửa sổ N ngày.

KPI gồm:

- tổng số bài,
- số nguồn duy nhất,
- coverage ratios:
  - có nội dung gốc,
  - có tóm tắt,
  - có sentiment,
  - có ticker,
  - có vector,
- phân bố sentiment,
- sentiment trung bình,
- phân bố impact,
- tỷ lệ high impact,
- độ dài nội dung/tóm tắt trung bình.

### 8.3 Lệnh CLI đánh giá

```bash
news-ingestor evaluate --days 7 --limit 500
news-ingestor evaluate --days 7 --limit 500 --json-output
```

### 8.4 Kiểm thử đánh giá

Đã có test cho:

- accuracy/confusion (`tests/unit/test_evaluation.py`),
- KPI pipeline dataset có dữ liệu và rỗng,
- CLI evaluate text/json mode (`tests/unit/test_cli_demo.py`).

---

## 9. Bảo mật, an toàn và độ tin cậy

### 9.1 Điểm đã làm tốt

- Không hardcode secrets vào code nghiệp vụ.
- Cấu hình qua env + validation.
- Không phụ thuộc cứng vào Qdrant (có fallback in-memory).
- Crawler có retry/backoff/rate-limit cơ bản.
- Dashboard chi tiết đã thêm escape text khi render HTML.

### 9.2 Rủi ro còn tồn tại

1. Crawler phụ thuộc cấu trúc HTML bên ngoài, có thể gãy khi nguồn đổi layout.
2. Fallback in-memory cho vector chỉ phù hợp tình huống tạm thời, không bền cho production dài hạn.
3. Chất lượng sentiment/impact phụ thuộc nguồn text và heuristic/rule set.
4. Còn warning deprecation Pydantic (`class Config`, `json_encoders`) cần chuẩn hóa lên ConfigDict.

---

## 10. Hiệu năng và khả năng mở rộng

### 10.1 Trạng thái hiện tại

- Phù hợp môi trường dev/small-to-medium workload.
- Batch pipeline chạy tuần tự, dễ hiểu và dễ debug.
- Truy vấn semantic đã hỗ trợ qua vector DB.

### 10.2 Hướng mở rộng kỹ thuật

1. Song song hóa crawl + processing theo worker pool.
2. Bổ sung queue/event bus để tách acquisition và processing.
3. Dùng migration framework đầy đủ (Alembic) thay migration nhẹ.
4. Caching và incremental indexing cho dashboard.
5. Snapshot định kỳ KPI đánh giá để theo dõi trend chất lượng.

---

## 11. Kiểm thử và chất lượng mã

### 11.1 Bộ kiểm thử hiện có

- Unit tests cho models, repository, impact classifier, scheduler, CLI.
- Integration test cho pipeline.
- Lint bằng Ruff.

### 11.2 Quy trình verify chuẩn

```bash
python -m ruff check .
python -m pytest -q
python -m news_ingestor.cli evaluate --days 7 --limit 500
```

---

## 12. Hướng dẫn chạy nhanh

### 12.1 Khởi tạo

```bash
python -m news_ingestor.cli init-db
```

### 12.2 Crawl một lần

```bash
python -m news_ingestor.cli crawl --once
```

### 12.3 Crawl daemon (10 phút)

```bash
python -m news_ingestor.cli crawl --daemon --interval 600
```

### 12.4 Dashboard

```bash
python -m news_ingestor.cli demo
```

### 12.5 Đánh giá

```bash
python -m news_ingestor.cli evaluate --days 7 --limit 500
```

---

## 13. Kết luận

Dự án đã đạt được mục tiêu cốt lõi: xây dựng một hệ thống thu thập và phân tích tin tức tài chính Việt Nam có tính vận hành thực tế, có lớp NLP enrich dữ liệu, hỗ trợ truy vấn ngữ nghĩa và giám sát trực quan.

Các cải tiến gần nhất đã nâng chất lượng sản phẩm theo hai hướng rõ rệt:

1. **Kỹ thuật**: có khung đánh giá KPI và CLI evaluate để đo chất lượng pipeline định lượng.
2. **Trải nghiệm**: trang chi tiết bài báo hiển thị đầy đủ, khung fit nội dung, dễ đọc hơn cho vận hành.

Trong giai đoạn tiếp theo, hệ thống có thể mở rộng theo hướng production-grade bằng cách tăng tính song song, chuẩn hóa migration, tăng độ bền crawler và hoàn thiện pipeline đánh giá liên tục theo thời gian.
