# 🗞️ Phân hệ Tự động Thu thập và Xử lý Tin tức Tài chính

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Server-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Hệ thống tự động thu thập, xử lý NLP, và phục vụ tin tức tài chính Việt Nam qua giao thức **Model Context Protocol (MCP)** — giúp AI Agent ra quyết định đầu tư thông minh hơn.

---

## 📋 Mục lục

- [Tổng quan](#-tổng-quan)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Cài đặt nhanh](#-cài-đặt-nhanh)
- [Sử dụng](#-sử-dụng)
- [Dashboard](#-dashboard)
- [MCP Tools](#-mcp-tools)
- [Cấu hình](#️-cấu-hình)
- [Docker](#-docker)
- [Kiểm thử](#-kiểm-thử)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)

---

## 🎯 Tổng quan

Phân hệ này là **"giác quan"** của hệ thống đầu tư tự động, giải quyết bài toán **dữ liệu định tính** (tin tức, sự kiện) thông qua 5 lớp xử lý:

| Lớp | Chức năng | Công nghệ |
|-----|-----------|-----------|
| 🕷️ **Thu thập** | Cào dữ liệu từ 7+ nguồn uy tín | httpx, BeautifulSoup, feedparser |
| 📄 **Lấy nội dung** | Fetch full body bài báo từ URL gốc | ContentFetcher, CSS selectors theo domain |
| 🧠 **Xử lý NLP** | Làm sạch, NER, Phân tích cảm xúc | Gemini AI, Keyword-based |
| 💾 **Lưu trữ** | Database kép (Relational + Vector) | SQLite (dev) / PostgreSQL (prod), Qdrant |
| 🔌 **MCP Server** | 4 tools cho AI Agent | MCP Protocol |

### Nguồn tin hỗ trợ

- **CafeF** — Chứng khoán, Vĩ mô, Doanh nghiệp
- **VnExpress** — Kinh doanh, Chứng khoán, Bất động sản
- **VietStock** — Chứng khoán, Doanh nghiệp, Tài chính
- **RSS Tổng hợp** — Thanh Niên, và các nguồn tùy chỉnh qua `config/feeds.json`

### Content Fetching

Hệ thống không chỉ lấy tiêu đề/mô tả từ RSS, mà **fetch toàn bộ nội dung bài báo** từ URL gốc:

| Nguồn | CSS Selector | Avg Content |
|-------|-------------|-------------|
| VnExpress | `article.fck_detail` / `p.Normal` | 2,500–6,500 ký tự |
| CafeF | `div.detail-content` | 1,800–10,600 ký tự |
| VietStock | `div.article-content` | 2,000–8,000 ký tự |
| Thanh Niên | `div.detail__content` | 1,500–5,000 ký tự |

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────┐
│                    AI AGENT (Claude, GPT...)             │
│                         ▲                                │
│                         │ MCP Protocol                   │
│                         ▼                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │              🔌 MCP SERVER                         │  │
│  │  tim_tin_vi_mo │ lay_tin_doanh_nghiep              │  │
│  │  tim_kiem_ngu_nghia │ lay_cam_xuc_thi_truong       │  │
│  └──────────┬───────────────────┬─────────────────────┘  │
│             │                   │                        │
│   ┌─────────▼────────┐ ┌───────▼──────────┐             │
│   │  💾 SQLite/PG    │ │  🔍 Qdrant       │             │
│   │  (Metadata)      │ │  (Vector Search) │             │
│   └─────────▲────────┘ └───────▲──────────┘             │
│             │                   │                        │
│  ┌──────────┴───────────────────┴─────────────────────┐  │
│  │              🧠 NLP PIPELINE                       │  │
│  │  Fetch Content → Làm sạch → NER → Sentiment       │  │
│  │                                    → Embeddings    │  │
│  └──────────────────────▲─────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────┴─────────────────────────────┐  │
│  │              🕷️ CRAWLERS                           │  │
│  │  CafeF │ VnExpress │ VietStock │ RSS Tổng hợp     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────────┐│
│  │  📊 STREAMLIT DASHBOARD                             ││
│  │  Tổng quan │ Danh sách │ Chi tiết │ Chẩn đoán      ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Cài đặt nhanh

### Yêu cầu

- Python 3.11+ (khuyên dùng 3.12)
- (Tùy chọn) Conda (`conda create -n news python=3.12`)
- (Tùy chọn) Google Gemini API Key ([lấy miễn phí](https://aistudio.google.com/apikey))

### Cài đặt

```bash
# Clone dự án
git clone https://github.com/meth04/tracking_news.git
cd tracking_news

# Cách 1: Dùng conda (khuyên dùng)
conda create -n news python=3.12 -y
conda activate news

# Cách 2: Dùng venv
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

# Cài đặt dependencies
pip install -e ".[dev]"

# Cấu hình
cp .env.example .env
# Chỉnh sửa .env — DATABASE_URL mặc định dùng SQLite, sẵn sàng chạy ngay

# Khởi tạo database
news-ingestor init-db
```

> **Lưu ý:** Mặc định dùng SQLite (`sqlite+aiosqlite:///./data/tin_tuc.db`), không cần cài PostgreSQL. Muốn dùng PostgreSQL cho production, đổi `DATABASE_URL` trong `.env`.

---

## 💻 Sử dụng

### Thu thập tin tức (một lần)

```bash
news-ingestor crawl --once
```

Pipeline tự động thực hiện:
1. Thu thập tiêu đề + URL từ RSS feeds và trang listing
2. **Fetch nội dung đầy đủ** từ URL gốc (VnExpress, CafeF, VietStock)
3. Làm sạch, trích xuất mã CK, phân tích cảm xúc
4. Tạo vector embeddings
5. Lưu vào database

### Chạy daemon (tự động thu thập mỗi 15 phút)

```bash
news-ingestor crawl --daemon --interval 900
```

### Khởi động MCP Server

```bash
news-ingestor serve-mcp
```

### Xem thống kê

```bash
news-ingestor stats
```

### Tùy chọn nâng cao

```bash
# Thu thập không chạy NLP (chỉ lưu raw)
news-ingestor crawl --once --skip-nlp

# Thu thập không tạo embeddings (nhanh hơn)
news-ingestor crawl --once --no-embedding

# Log dạng JSON (production)
news-ingestor --json-log crawl --once

# Debug mode
news-ingestor --log-level DEBUG crawl --once
```

---

## 📊 Dashboard

Hệ thống có dashboard Streamlit chuyên nghiệp với 5 trang:

```bash
# Chạy dashboard
streamlit run dashboard.py
# Mở http://localhost:8501
```

### Các trang

| Trang | Chức năng |
|-------|-----------|
| 📊 **Tổng quan** | 8 KPI cards, biểu đồ timeline cảm xúc, nguồn tin, chất lượng dữ liệu, auto-detect vấn đề |
| 📋 **Danh sách tin** | Duyệt bài báo với badges màu (nguồn, danh mục, cảm xúc, mã CK), indicator chất lượng |
| 🔍 **Chi tiết bài báo** | Xem toàn bộ nội dung gốc, metadata, kết quả NLP, quality checks, Raw JSON |
| 🩺 **Chẩn đoán Pipeline** | 4 diagnostic cards, histograms phân bố, bảng bài có vấn đề |
| 📡 **Nguồn & Crawl** | Thống kê theo nguồn, top mã CK, nhật ký thu thập |

### Tính năng

- 🌙 Dark theme premium
- 🏷️ Color badges (nguồn, danh mục, cảm xúc, mã CK)
- 📈 Interactive Plotly charts
- 🔎 Bộ lọc (nguồn tin, danh mục, tìm kiếm)
- 🚨 Tự động phát hiện vấn đề dữ liệu

---

## 🔌 MCP Tools

Hệ thống cung cấp 4 công cụ qua giao thức MCP:

### 1. `tim_tin_vi_mo` — Tìm tin vĩ mô
```json
{
  "khung_thoi_gian": "7d",
  "chu_de": "lãi suất",
  "gioi_han": 20
}
```

### 2. `lay_tin_doanh_nghiep` — Tin doanh nghiệp
```json
{
  "ma_ck": "FPT",
  "ngay_bat_dau": "2026-01-01",
  "gioi_han": 30
}
```

### 3. `tim_kiem_ngu_nghia` — Semantic Search
```json
{
  "cau_hoi": "Ảnh hưởng của lãi suất FED đến thị trường Việt Nam",
  "gioi_han": 10
}
```

### 4. `lay_cam_xuc_thi_truong` — Thống kê cảm xúc
```json
{
  "ma_ck": "VCB",
  "so_ngay": 7
}
```

### Tích hợp MCP vào Claude Desktop

Thêm vào `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tin-tuc-tai-chinh": {
      "command": "news-ingestor",
      "args": ["serve-mcp"]
    }
  }
}
```

---

## ⚙️ Cấu hình

### Biến môi trường (.env)

| Biến | Mô tả | Mặc định |
|------|--------|----------|
| `DATABASE_URL` | Chuỗi kết nối DB | `sqlite+aiosqlite:///./data/tin_tuc.db` |
| `QDRANT_URL` | URL Qdrant server | `http://localhost:6333` |
| `GEMINI_API_KEY` | Google Gemini API key | (trống - dùng keyword-based) |
| `CRAWL_INTERVAL_MINUTES` | Chu kỳ thu thập (phút) | `15` |
| `LOG_LEVEL` | Cấp độ log | `INFO` |

### Thêm mã chứng khoán

Chỉnh sửa `config/tickers.json` để thêm mã CK và từ khóa nhận diện.

### Thêm nguồn RSS

Chỉnh sửa `config/feeds.json` để thêm nguồn RSS mới.

---

## 🐳 Docker

### Chạy toàn bộ hệ thống với Docker Compose

```bash
# Đặt Gemini API key (tùy chọn)
export GEMINI_API_KEY=your_key_here

# Khởi động tất cả services
docker compose up -d

# Xem logs
docker compose logs -f crawler
```

### Services

| Service | Mô tả | Port |
|---------|--------|------|
| `postgres` | PostgreSQL 16 | 5432 |
| `qdrant` | Vector Database | 6333, 6334 |
| `crawler` | Thu thập tự động (daemon) | — |
| `mcp-server` | MCP Server cho AI Agent | stdio |

---

## 🧪 Kiểm thử

```bash
# Chạy tất cả tests
python -m pytest tests/ -v

# Chỉ unit tests
python -m pytest tests/unit/ -v

# Chỉ integration tests
python -m pytest tests/integration/ -v

# Với coverage
python -m pytest tests/ --cov=news_ingestor --cov-report=term-missing
```

---

## 📁 Cấu trúc dự án

```
tracking_news/
├── config/                     # Cấu hình
│   ├── settings.py             #   Pydantic Settings
│   ├── feeds.json              #   Nguồn RSS
│   └── tickers.json            #   Mã CK & từ khóa
├── src/news_ingestor/          # Mã nguồn chính
│   ├── crawlers/               #   Bộ thu thập dữ liệu
│   │   ├── base.py             #     ABC + retry/rate-limit
│   │   ├── rss_crawler.py      #     RSS/Atom tổng quát
│   │   ├── cafef.py            #     CafeF scraper
│   │   ├── vnexpress.py        #     VnExpress scraper
│   │   ├── vietstock.py        #     VietStock scraper
│   │   └── scheduler.py        #     Orchestrator
│   ├── processing/             #   Pipeline NLP
│   │   ├── content_fetcher.py  #     ★ Fetch full article body
│   │   ├── cleaner.py          #     Làm sạch dữ liệu
│   │   ├── entity_extractor.py #     NER mã CK
│   │   ├── sentiment.py        #     Phân tích cảm xúc
│   │   ├── embeddings.py       #     Vector embeddings
│   │   └── pipeline.py         #     Orchestrator NLP
│   ├── storage/                #   Lưu trữ
│   │   ├── database.py         #     SQLite/PostgreSQL
│   │   ├── repository.py       #     CRUD operations
│   │   └── vector_store.py     #     Qdrant client
│   ├── mcp_server/             #   MCP Server
│   │   └── server.py           #     4 tools cho AI Agent
│   └── utils/                  #   Tiện ích
│       ├── logging_config.py
│       └── text_utils.py
├── dashboard.py                # ★ Streamlit Dashboard (5 trang)
├── .streamlit/config.toml      #   Dashboard dark theme config
├── tests/                      # Kiểm thử
├── data/                       # SQLite database (auto-created)
├── docker-compose.yml          # Docker Compose
└── pyproject.toml              # Dependencies
```

---

## 📝 Giấy phép

Dự án được phân phối theo giấy phép [MIT](LICENSE).

---

<p align="center">
  <strong>🇻🇳 Được xây dựng cho thị trường tài chính Việt Nam</strong>
</p>
