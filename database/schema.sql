-- ============================================
-- SCHEMA CƠ SỞ DỮ LIỆU TIN TỨC TÀI CHÍNH
-- Phân hệ: News Ingestion & Processing Module
-- Database: PostgreSQL 15+
-- ============================================

-- Bật extension UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- BẢNG CHÍNH: tin_tuc_tai_chinh
-- Lưu trữ siêu dữ liệu bài báo đã xử lý
-- ============================================
CREATE TABLE IF NOT EXISTS tin_tuc_tai_chinh (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tieu_de         VARCHAR(500) NOT NULL,
    noi_dung_tom_tat TEXT DEFAULT '',
    noi_dung_goc    TEXT DEFAULT '',
    url             VARCHAR(2000) NOT NULL UNIQUE,
    nguon_tin       VARCHAR(100) NOT NULL,
    thoi_gian_xuat_ban TIMESTAMP WITH TIME ZONE NOT NULL,
    danh_muc        VARCHAR(20) NOT NULL DEFAULT 'MACRO'
                    CHECK (danh_muc IN ('MACRO', 'MICRO', 'INDUSTRY')),
    ma_chung_khoan_lien_quan TEXT[] DEFAULT '{}',
    diem_cam_xuc    REAL DEFAULT 0.0
                    CHECK (diem_cam_xuc >= -1.0 AND diem_cam_xuc <= 1.0),
    nhan_cam_xuc    VARCHAR(20) DEFAULT 'NEUTRAL'
                    CHECK (nhan_cam_xuc IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')),
    vector_id       UUID,
    trang_thai      VARCHAR(20) DEFAULT 'PENDING'
                    CHECK (trang_thai IN ('PENDING', 'PROCESSING', 'COMPLETED', 'ERROR')),
    thoi_gian_tao   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Đảm bảo không trùng lặp bài báo
    CONSTRAINT uq_bai_bao UNIQUE (url)
);

-- ============================================
-- INDEX để tối ưu truy vấn
-- ============================================

-- Index cho tìm kiếm theo mã chứng khoán (GIN cho array)
CREATE INDEX IF NOT EXISTS idx_ma_ck
    ON tin_tuc_tai_chinh USING GIN (ma_chung_khoan_lien_quan);

-- Index cho lọc theo danh mục
CREATE INDEX IF NOT EXISTS idx_danh_muc
    ON tin_tuc_tai_chinh (danh_muc);

-- Index cho truy vấn theo thời gian
CREATE INDEX IF NOT EXISTS idx_thoi_gian
    ON tin_tuc_tai_chinh (thoi_gian_xuat_ban DESC);

-- Index cho lọc theo nguồn tin
CREATE INDEX IF NOT EXISTS idx_nguon_tin
    ON tin_tuc_tai_chinh (nguon_tin);

-- Index cho trạng thái xử lý
CREATE INDEX IF NOT EXISTS idx_trang_thai
    ON tin_tuc_tai_chinh (trang_thai);

-- Index kết hợp cho truy vấn phổ biến
CREATE INDEX IF NOT EXISTS idx_danh_muc_thoi_gian
    ON tin_tuc_tai_chinh (danh_muc, thoi_gian_xuat_ban DESC);

-- ============================================
-- BẢNG PHỤ: nhat_ky_thu_thap
-- Theo dõi lịch sử chạy crawler
-- ============================================
CREATE TABLE IF NOT EXISTS nhat_ky_thu_thap (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nguon_tin       VARCHAR(100) NOT NULL,
    thoi_gian_bat_dau TIMESTAMP WITH TIME ZONE NOT NULL,
    thoi_gian_ket_thuc TIMESTAMP WITH TIME ZONE,
    so_bai_thu_thap INTEGER DEFAULT 0,
    so_bai_moi      INTEGER DEFAULT 0,
    trang_thai      VARCHAR(20) DEFAULT 'RUNNING'
                    CHECK (trang_thai IN ('RUNNING', 'SUCCESS', 'FAILED')),
    thong_bao_loi   TEXT
);

-- Index cho theo dõi lịch sử
CREATE INDEX IF NOT EXISTS idx_nhat_ky_thoi_gian
    ON nhat_ky_thu_thap (thoi_gian_bat_dau DESC);
