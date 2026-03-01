"""
🗞️ Dashboard Tin tức Tài chính Việt Nam — Professional Edition.

Multi-page dashboard for debugging and monitoring the news ingestion pipeline.
Chạy: streamlit run dashboard.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
import textwrap
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from config.settings import lay_cau_hinh_nlp

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="📊 News Pipeline Monitor",
    page_icon="🗞️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# THEME CSS
# ============================================

BADGE_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .detail-card a { color: #a78bfa; text-decoration: none; }
    .detail-card a:hover { text-decoration: underline; }
    .badge { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; }
    .badge-positive { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .badge-negative { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .badge-neutral { background: rgba(148,163,184,0.12); color: #94a3b8; border: 1px solid rgba(148,163,184,0.25); }
    .badge-source { background: rgba(99,102,241,0.15); color: #a78bfa; border: 1px solid rgba(99,102,241,0.3); }
    .badge-category { background: rgba(236,72,153,0.12); color: #f472b6; border: 1px solid rgba(236,72,153,0.25); }
    .badge-stock { background: rgba(251,191,36,0.12); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
    .badge-ok { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .badge-warn { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
    .badge-error { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
"""

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d1b2a 100%);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #a78bfa, #6366f1);
        background-size: 200% 100%;
        animation: shimmer 3s linear infinite;
    }
    @keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
    .main-header h1 { color:#e2e8f0; font-size:24px; font-weight:700; margin:0; }
    .main-header p { color:#94a3b8; font-size:13px; margin:4px 0 0; }

    .kpi-card {
        background: linear-gradient(135deg, #1e1e3f 0%, #16162e 100%);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 14px;
        padding: 18px 16px;
        text-align: center;
        transition: all 0.3s;
    }
    .kpi-card:hover {
        border-color: rgba(99,102,241,0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99,102,241,0.15);
    }
    .kpi-icon { font-size:24px; margin-bottom:6px; }
    .kpi-value { font-size:28px; font-weight:700; color:#e2e8f0; line-height:1.1; }
    .kpi-label { font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:1px; margin-top:4px; font-weight:500; }

    .kpi-positive .kpi-value { color: #4ade80; }
    .kpi-negative .kpi-value { color: #f87171; }
    .kpi-neutral .kpi-value { color: #94a3b8; }
    .kpi-accent .kpi-value { color: #a78bfa; }
    .kpi-warn .kpi-value { color: #fbbf24; }

    .section-header {
        color: #e2e8f0;
        font-size: 17px;
        font-weight: 600;
        margin: 24px 0 12px;
        padding-bottom: 6px;
        border-bottom: 2px solid rgba(99,102,241,0.2);
    }

    .diag-card {
        background: linear-gradient(135deg, #1e1e3f 0%, #16162e 100%);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .diag-card h5 { color:#e2e8f0; font-size:14px; font-weight:600; margin:0 0 8px; }
    .diag-row { display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid rgba(99,102,241,0.06); font-size:13px; }
    .diag-row:last-child { border-bottom:none; }
    .diag-key { color:#94a3b8; }
    .diag-val { color:#e2e8f0; font-weight:500; }
    .diag-val.ok { color:#4ade80; }
    .diag-val.warn { color:#fbbf24; }
    .diag-val.error { color:#f87171; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23 0%, #12122a 100%);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATA LOADING
# ============================================

DB_PATH = PROJECT_ROOT / "data" / "tin_tuc.db"


@st.cache_data(ttl=30)
def load_articles():
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query(
        "SELECT * FROM tin_tuc_tai_chinh ORDER BY thoi_gian_xuat_ban DESC",
        conn,
    )
    conn.close()
    if not df.empty:
        df["thoi_gian_xuat_ban"] = pd.to_datetime(df["thoi_gian_xuat_ban"], errors="coerce")
        df["thoi_gian_tao"] = pd.to_datetime(df["thoi_gian_tao"], errors="coerce")
        df["ma_ck_list"] = df["ma_chung_khoan_lien_quan"].apply(
            lambda v: json.loads(v) if v and v != "[]" else []
        )
        df["len_goc"] = df["noi_dung_goc"].apply(lambda x: len(x) if x else 0)
        df["len_tom_tat"] = df["noi_dung_tom_tat"].apply(lambda x: len(x) if x else 0)
        df["has_content"] = df["len_goc"] > 0
        df["has_summary"] = df["len_tom_tat"] > 0
        df["has_sentiment"] = df["diem_cam_xuc"].notna() & (df["diem_cam_xuc"] != 0)
        df["has_tickers"] = df["ma_ck_list"].apply(lambda x: len(x) > 0)
        df["has_vector"] = df["vector_id"].notna() & (df["vector_id"] != "")
    return df


@st.cache_data(ttl=30)
def load_crawl_logs():
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        df = pd.read_sql_query("SELECT * FROM nhat_ky_thu_thap ORDER BY thoi_gian_bat_dau DESC LIMIT 50", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


# Badge helpers
def sentiment_badge(label, score):
    if label == "POSITIVE":
        return f'<span class="badge badge-positive">Tích cực ({score:+.2f})</span>'
    elif label == "NEGATIVE":
        return f'<span class="badge badge-negative">Tiêu cực ({score:+.2f})</span>'
    return f'<span class="badge badge-neutral">Trung tính ({score:+.2f})</span>'


def source_badge(s):
    return f'<span class="badge badge-source">{escape(str(s))}</span>'


def category_badge(c):
    m = {
        "MACRO": "Vĩ mô",
        "STOCK": "CK",
        "COMPANY": "DN",
        "REAL_ESTATE": "BĐS",
        "INDUSTRY": "Ngành",
        "MICRO": "Vi mô",
    }
    return f'<span class="badge badge-category">{escape(str(m.get(c, c)))}</span>'


def stock_badges(lst):
    if not lst:
        return ""
    return " ".join(f'<span class="badge badge-stock">{escape(str(t))}</span>' for t in lst[:6])


def quality_badge(val, thresh_ok=1, thresh_warn=0):
    if val > thresh_ok:
        return f'<span class="badge badge-ok">✓ {val}</span>'
    elif val > thresh_warn:
        return f'<span class="badge badge-warn">⚠ {val}</span>'
    return f'<span class="badge badge-error">✗ {val}</span>'


# ============================================
# SIDEBAR — Navigation + Filters
# ============================================

with st.sidebar:
    st.markdown("## 🗞️ News Pipeline")
    page = st.radio(
        "Trang",
        [
            "📅 Tổng hợp ngày",
            "📊 Tổng quan",
            "📋 Danh sách tin",
            "🔍 Chi tiết bài báo",
            "🩺 Chẩn đoán Pipeline",
            "📡 Nguồn & Crawl",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    df = load_articles()

    if df.empty:
        st.error("Chưa có dữ liệu. Chạy:\n```\nnews-ingestor crawl --once\n```")
        st.stop()

    # Common filters
    st.markdown("### 🔧 Bộ lọc chung")
    all_sources = sorted(df["nguon_tin"].dropna().unique().tolist())
    selected_sources = st.multiselect("📡 Nguồn tin", all_sources, all_sources)

    all_cats = sorted(df["danh_muc"].dropna().unique().tolist())
    selected_cats = st.multiselect("📂 Danh mục", all_cats, all_cats)

    search_q = st.text_input("🔎 Tìm kiếm", placeholder="tiêu đề, mã CK...")

    st.markdown("---")
    if st.button("🔄 Làm mới", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"📦 DB: {DB_PATH.name} ({DB_PATH.stat().st_size / 1024:.0f} KB)")
    st.caption(f"🕐 Cập nhật: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")

# Apply filters
filtered = df.copy()
if selected_sources:
    filtered = filtered[filtered["nguon_tin"].isin(selected_sources)]
if selected_cats:
    filtered = filtered[filtered["danh_muc"].isin(selected_cats)]
if search_q:
    q = search_q.lower()
    filtered = filtered[
        filtered["tieu_de"].str.lower().str.contains(q, na=False) |
        filtered["noi_dung_tom_tat"].str.lower().str.contains(q, na=False) |
        filtered["ma_chung_khoan_lien_quan"].str.lower().str.contains(q, na=False)
    ]


# ============================================
# PAGE: TỔNG HỢP NGÀY
# ============================================

if page == "📅 Tổng hợp ngày":
    st.markdown("""
    <div class="main-header">
        <h1>📅 Tổng hợp theo ngày</h1>
        <p>Xem nhanh số lượng tin, cảm xúc, nguồn tin và mã cổ phiếu theo từng ngày</p>
    </div>
    """, unsafe_allow_html=True)

    ddf = filtered.dropna(subset=["thoi_gian_xuat_ban"]).copy()
    if ddf.empty:
        st.warning("Không có dữ liệu thời gian để tổng hợp theo ngày.")
    else:
        ddf["ngay"] = ddf["thoi_gian_xuat_ban"].dt.date

        by_day = (
            ddf.groupby("ngay")
            .agg(
                tong_bai=("id", "count"),
                tin_tich_cuc=("nhan_cam_xuc", lambda s: (s == "POSITIVE").sum()),
                tin_tieu_cuc=("nhan_cam_xuc", lambda s: (s == "NEGATIVE").sum()),
                tin_trung_tinh=("nhan_cam_xuc", lambda s: (s == "NEUTRAL").sum()),
                diem_tb=("diem_cam_xuc", "mean"),
                so_nguon=("nguon_tin", "nunique"),
                so_ma_ck=("ma_ck_list", lambda col: len({t for lst in col for t in (lst if isinstance(lst, list) else [])})),
            )
            .reset_index()
            .sort_values("ngay", ascending=False)
        )
        by_day["diem_tb"] = by_day["diem_tb"].fillna(0.0).round(4)

        st.markdown('<div class="section-header">📌 Bảng tổng hợp ngày</div>', unsafe_allow_html=True)
        st.dataframe(
            by_day.rename(
                columns={
                    "ngay": "Ngày",
                    "tong_bai": "Tổng bài",
                    "tin_tich_cuc": "Tích cực",
                    "tin_tieu_cuc": "Tiêu cực",
                    "tin_trung_tinh": "Trung tính",
                    "diem_tb": "Điểm TB",
                    "so_nguon": "Số nguồn",
                    "so_ma_ck": "Số mã CK",
                }
            ),
            use_container_width=True,
            height=320,
        )

        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown('<div class="section-header">📈 Số lượng tin theo ngày</div>', unsafe_allow_html=True)
            fig_day = px.bar(
                by_day.sort_values("ngay"),
                x="ngay",
                y="tong_bai",
                labels={"ngay": "", "tong_bai": "Số bài"},
                color_discrete_sequence=["#6366f1"],
            )
            fig_day.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Inter", size=11),
                xaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                yaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                margin=dict(l=0, r=0, t=10, b=0),
                height=280,
            )
            st.plotly_chart(fig_day, use_container_width=True)

        with c2:
            st.markdown('<div class="section-header">💭 Điểm cảm xúc TB</div>', unsafe_allow_html=True)
            fig_score = px.line(
                by_day.sort_values("ngay"),
                x="ngay",
                y="diem_tb",
                markers=True,
                labels={"ngay": "", "diem_tb": "Điểm TB"},
            )
            fig_score.update_traces(line_color="#a78bfa")
            fig_score.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Inter", size=11),
                xaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                yaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                margin=dict(l=0, r=0, t=10, b=0),
                height=280,
            )
            st.plotly_chart(fig_score, use_container_width=True)

        ngay_list = [str(d) for d in by_day["ngay"].tolist()]
        ngay_chon = st.selectbox("📆 Chọn ngày để xem chi tiết", ngay_list)
        dsel = ddf[ddf["ngay".strip()] == pd.to_datetime(ngay_chon).date()].copy()

        st.markdown('<div class="section-header">📰 Chi tiết theo ngày đã chọn</div>', unsafe_allow_html=True)
        left, right = st.columns(2)

        with left:
            src_count = (
                dsel["nguon_tin"].value_counts().reset_index().rename(columns={"index": "Nguồn", "nguon_tin": "Số bài"})
            )
            st.caption("Top nguồn tin")
            st.dataframe(src_count.head(10), use_container_width=True, height=260)

        with right:
            tickers = [t for lst in dsel["ma_ck_list"] for t in (lst if isinstance(lst, list) else [])]
            if tickers:
                tk_df = pd.Series(tickers).value_counts().reset_index()
                tk_df.columns = ["Mã CK", "Số bài"]
            else:
                tk_df = pd.DataFrame(columns=["Mã CK", "Số bài"])
            st.caption("Top mã CK")
            st.dataframe(tk_df.head(15), use_container_width=True, height=260)

        cols = [
            "thoi_gian_xuat_ban",
            "nguon_tin",
            "danh_muc",
            "tieu_de",
            "nhan_cam_xuc",
            "diem_cam_xuc",
            "ma_chung_khoan_lien_quan",
            "url",
        ]
        view = dsel[cols].sort_values("thoi_gian_xuat_ban", ascending=False)
        view = view.rename(
            columns={
                "thoi_gian_xuat_ban": "Thời gian",
                "nguon_tin": "Nguồn",
                "danh_muc": "Danh mục",
                "tieu_de": "Tiêu đề",
                "nhan_cam_xuc": "Nhãn cảm xúc",
                "diem_cam_xuc": "Điểm cảm xúc",
                "ma_chung_khoan_lien_quan": "Mã CK",
                "url": "URL",
            }
        )
        st.dataframe(view, use_container_width=True, height=420)


# ============================================
# PAGE: TỔNG QUAN
# ============================================

elif page == "📊 Tổng quan":
    st.markdown("""
    <div class="main-header">
        <h1>🗞️ News Pipeline Monitor — Tổng quan</h1>
        <p>Theo dõi trạng thái pipeline thu thập, xử lý NLP, và chất lượng dữ liệu</p>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    total = len(filtered)
    pos = len(filtered[filtered["nhan_cam_xuc"] == "POSITIVE"])
    neg = len(filtered[filtered["nhan_cam_xuc"] == "NEGATIVE"])
    has_content = filtered["has_content"].sum()
    has_sent = filtered["has_sentiment"].sum()
    has_vec = filtered["has_vector"].sum()
    has_tick = filtered["has_tickers"].sum()
    avg_score = filtered["diem_cam_xuc"].mean() if total > 0 else 0

    cols = st.columns(8)
    kpis = [
        ("📰", total, "Tổng bài", "kpi-accent"),
        ("📈", pos, "Tích cực", "kpi-positive"),
        ("📉", neg, "Tiêu cực", "kpi-negative"),
        ("📝", has_content, "Có nội dung", "kpi-accent" if has_content == total else "kpi-warn"),
        ("💭", has_sent, "Có sentiment", "kpi-accent" if has_sent > total * 0.5 else "kpi-warn"),
        ("🏷️", has_tick, "Có mã CK", "kpi-accent"),
        ("🧬", has_vec, "Có vector", "kpi-accent" if has_vec == total else "kpi-warn"),
        ("🎯", f"{avg_score:+.3f}", "Điểm TB", ""),
    ]
    for c, (icon, val, label, cls) in zip(cols, kpis, strict=False):
        with c:
            score_color = ""
            if label == "Điểm TB":
                sc = avg_score
                score_color = f'style="color:{"#4ade80" if sc > 0.1 else ("#f87171" if sc < -0.1 else "#94a3b8")}"'
            st.markdown(f"""
            <div class="kpi-card {cls}">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-value" {score_color}>{val}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        st.markdown('<div class="section-header">📊 Timeline cảm xúc</div>', unsafe_allow_html=True)
        if not filtered.empty:
            tdf = filtered.dropna(subset=["thoi_gian_xuat_ban"]).copy()
            tdf["ngay"] = tdf["thoi_gian_xuat_ban"].dt.date
            daily = tdf.groupby(["ngay", "nhan_cam_xuc"]).size().reset_index(name="n")
            fig = px.bar(daily, x="ngay", y="n", color="nhan_cam_xuc",
                         color_discrete_map={"POSITIVE": "#4ade80", "NEGATIVE": "#f87171", "NEUTRAL": "#475569"},
                         barmode="stack", labels={"ngay": "", "n": "Bài", "nhan_cam_xuc": ""})
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Inter", size=11),
                legend=dict(orientation="h", y=1.08), margin=dict(l=0,r=0,t=20,b=0),
                xaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                yaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-header">📡 Nguồn tin</div>', unsafe_allow_html=True)
        if not filtered.empty:
            sc = filtered["nguon_tin"].value_counts().reset_index()
            sc.columns = ["nguon", "n"]
            fig2 = px.pie(sc, values="n", names="nguon", hole=0.55,
                          color_discrete_sequence=["#6366f1","#8b5cf6","#a78bfa","#c4b5fd","#818cf8","#7c3aed","#4f46e5"])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8", family="Inter", size=10),
                               margin=dict(l=0,r=0,t=10,b=0), height=280, showlegend=True, legend=dict(font=dict(size=10)))
            fig2.update_traces(textposition="inside", textinfo="percent", textfont_size=9)
            st.plotly_chart(fig2, use_container_width=True)

    with c3:
        st.markdown('<div class="section-header">🔬 Chất lượng dữ liệu</div>', unsafe_allow_html=True)
        if not filtered.empty:
            quality = pd.DataFrame({
                "Metric": ["Có nội dung", "Có tóm tắt", "Có sentiment", "Có mã CK", "Có vector"],
                "Count": [has_content, filtered["has_summary"].sum(), has_sent, has_tick, has_vec],
                "Total": [total] * 5,
            })
            quality["Pct"] = (quality["Count"] / quality["Total"] * 100).round(1)
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(y=quality["Metric"], x=quality["Pct"], orientation="h",
                                  marker=dict(color=quality["Pct"].apply(
                                      lambda x: "#4ade80" if x > 80 else ("#fbbf24" if x > 50 else "#f87171"))),
                                  text=quality.apply(lambda r: f"{r['Count']}/{r['Total']} ({r['Pct']}%)", axis=1),
                                  textposition="inside", textfont=dict(size=11)))
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font=dict(color="#94a3b8", family="Inter", size=11),
                               xaxis=dict(range=[0, 105], gridcolor="rgba(99,102,241,0.08)", title=""),
                               yaxis=dict(autorange="reversed"), margin=dict(l=0,r=0,t=10,b=0), height=280)
            st.plotly_chart(fig3, use_container_width=True)

    # Data quality alert
    st.markdown('<div class="section-header">⚠️ Phát hiện vấn đề</div>', unsafe_allow_html=True)

    issues = []
    pct_content = has_content / total * 100 if total > 0 else 0
    pct_sent = has_sent / total * 100 if total > 0 else 0
    avg_len = filtered["len_goc"].mean() if total > 0 else 0
    content_eq_summary = (filtered["noi_dung_goc"] == filtered["noi_dung_tom_tat"]).sum()

    if content_eq_summary > total * 0.5:
        issues.append(f"🔴 **{content_eq_summary}/{total} bài** có `noi_dung_goc == noi_dung_tom_tat` — Crawlers chưa lấy nội dung đầy đủ, chỉ lấy preview/description từ RSS feed")
    if avg_len < 300:
        issues.append(f"🟡 Độ dài trung bình nội dung chỉ **{avg_len:.0f} ký tự** — Quá ngắn, thường bài báo cần 500-2000+ ký tự")
    if pct_sent < 30:
        issues.append(f"🟡 Chỉ **{pct_sent:.1f}%** bài có sentiment score != 0 — NLP pipeline có thể chưa phân tích đủ")
    no_content = total - has_content
    if no_content > 0:
        issues.append(f"🔴 **{no_content} bài** hoàn toàn không có nội dung")

    # Check VietStock
    vs_count = len(filtered[filtered["nguon_tin"].str.contains("VietStock", na=False)])
    if vs_count <= 1:
        issues.append(f"🟡 VietStock chỉ có **{vs_count} bài** — Crawler VietStock có thể bị lỗi hoặc bị block")

    if issues:
        for iss in issues:
            st.markdown(iss)
    else:
        st.success("✅ Không phát hiện vấn đề nào!")


# ============================================
# PAGE: DANH SÁCH TIN
# ============================================

elif page == "📋 Danh sách tin":
    st.markdown("""
    <div class="main-header">
        <h1>📋 Danh sách tin tức</h1>
        <p>Duyệt qua tất cả bài báo đã thu thập — click vào tiêu đề để xem chi tiết</p>
    </div>
    """, unsafe_allow_html=True)

    per_page = st.selectbox("Số bài/trang", [25, 50, 100], index=1, label_visibility="collapsed")
    total = len(filtered)
    total_pages = max(1, (total + per_page - 1) // per_page)
    pg = st.number_input("Trang", 1, total_pages, 1, label_visibility="collapsed")

    start = (pg - 1) * per_page
    page_data = filtered.iloc[start:start + per_page]

    # Build HTML table
    rows_html = []
    for i, (_, r) in enumerate(page_data.iterrows()):
        tieu_de = r["tieu_de"] or "N/A"
        url = r["url"] or "#"
        nguon = r["nguon_tin"] or "N/A"
        cat = r["danh_muc"] or "N/A"
        nhan = r["nhan_cam_xuc"] or "NEUTRAL"
        diem = r["diem_cam_xuc"] if pd.notna(r["diem_cam_xuc"]) else 0.0
        tom_tat = r["noi_dung_tom_tat"] or ""
        tickers = r["ma_ck_list"] if isinstance(r["ma_ck_list"], list) else []
        tg = r["thoi_gian_xuat_ban"].strftime("%d/%m %H:%M") if pd.notna(r["thoi_gian_xuat_ban"]) else "N/A"
        len_goc = r["len_goc"]
        has_vec = "✓" if r["has_vector"] else "✗"

        # Quality indicators
        content_indicator = f'<span style="color:#4ade80;font-size:11px">📝 {len_goc}ch</span>' if len_goc > 0 else '<span style="color:#f87171;font-size:11px">📝 trống</span>'
        vec_indicator = '<span style="color:#4ade80;font-size:11px">🧬✓</span>' if r["has_vector"] else '<span style="color:#f87171;font-size:11px">🧬✗</span>'

        summary_html = f'<div style="color:#64748b;font-size:12px;margin-top:4px;line-height:1.4">{tom_tat[:250]}{"..." if len(tom_tat) > 250 else ""}</div>' if tom_tat else ""

        rows_html.append(f"""
        <div style="padding:14px 20px;border-bottom:1px solid rgba(99,102,241,0.07);">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div style="color:#e2e8f0;font-size:14px;font-weight:500;line-height:1.5;flex:1">
                    <a href="{url}" target="_blank" style="color:#e2e8f0;text-decoration:none">{start + i + 1}. {tieu_de}</a>
                </div>
                <div style="display:flex;gap:6px;align-items:center;margin-left:12px;flex-shrink:0">
                    {content_indicator} {vec_indicator}
                </div>
            </div>
            <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:6px">
                <span style="color:#64748b;font-size:12px">📅 {tg}</span>
                {source_badge(nguon)} {category_badge(cat)} {sentiment_badge(nhan, diem)} {stock_badges(tickers)}
            </div>
            {summary_html}
        </div>
        """)

    table_html = f"""
    <style>{BADGE_CSS}
    .table-container {{
        background: linear-gradient(135deg, #12122a 0%, #0f0f23 100%);
        border: 1px solid rgba(99,102,241,0.12);
        border-radius: 14px;
        overflow: hidden;
    }}
    .table-header {{
        background: rgba(99,102,241,0.08);
        padding: 14px 20px;
        border-bottom: 1px solid rgba(99,102,241,0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .table-header h3 {{ color:#e2e8f0; margin:0; font-size:15px; font-weight:600; }}
    .table-header span {{ color:#94a3b8; font-size:12px; }}
    </style>
    <div class="table-container">
        <div class="table-header">
            <h3>📰 {total} bài báo</h3>
            <span>Trang {pg}/{total_pages} · Hiển thị {start + 1}–{min(start + per_page, total)}</span>
        </div>
        {"".join(rows_html)}
    </div>
    """

    components.html(table_html, height=min(len(page_data) * 100 + 80, 5000), scrolling=True)


# ============================================
# PAGE: CHI TIẾT BÀI BÁO
# ============================================

elif page == "🔍 Chi tiết bài báo":
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Chi tiết bài báo</h1>
        <p>Xem toàn bộ nội dung, kết quả NLP, metadata và raw data của từng bài</p>
    </div>
    """, unsafe_allow_html=True)

    if filtered.empty:
        st.warning("Không có bài báo phù hợp với bộ lọc hiện tại.")
    else:
        # Article selector
        articles_display = filtered[["id", "tieu_de", "nguon_tin", "thoi_gian_xuat_ban"]].copy()
        articles_display["label"] = articles_display.apply(
            lambda r: f"[{r['nguon_tin']}] {r['tieu_de'][:70]}", axis=1
        )

        selected_idx = st.selectbox(
            "Chọn bài báo",
            range(len(articles_display)),
            format_func=lambda i: articles_display.iloc[i]["label"],
        )
        article = filtered.iloc[selected_idx]

        # Header with badges
        nhan = article["nhan_cam_xuc"] or "NEUTRAL"
        diem = article["diem_cam_xuc"] if pd.notna(article["diem_cam_xuc"]) else 0.0
        tickers = article["ma_ck_list"] if isinstance(article["ma_ck_list"], list) else []

        title_safe = escape(str(article["tieu_de"]))
        source_safe = escape(str(article["nguon_tin"]))
        category_safe = escape(str(article["danh_muc"]))
        published_safe = escape(str(article["thoi_gian_xuat_ban"]))
        status_safe = escape(str(article["trang_thai"]))
        article_id_safe = escape(str(article["id"]))
        url_safe = escape(str(article["url"]))
        ticker_text = (
            escape(", ".join(tickers))
            if tickers
            else '<span style="color:#64748b">Không phát hiện</span>'
        )
        vector_text = (
            escape(str(article["vector_id"]))
            if article["vector_id"]
            else '<span style="color:#f87171">Không có</span>'
        )
        summary_text = (
            '<span class="empty">⚠️ Chưa có nội dung tóm tắt</span>'
            if not article["noi_dung_tom_tat"]
            else escape(str(article["noi_dung_tom_tat"]))
        )
        full_text = (
            '<span class="empty">⚠️ Chưa có nội dung gốc — Crawler chưa lấy được body bài báo</span>'
            if not article["noi_dung_goc"]
            else escape(str(article["noi_dung_goc"]))
        )

        detail_html = f"""
        <style>{BADGE_CSS}
        .detail-card {{
            background: linear-gradient(135deg, #1e1e3f 0%, #16162e 100%);
            border: 1px solid rgba(99,102,241,0.2);
            border-radius: 14px;
            padding: 24px;
            font-family: 'Inter', sans-serif;
            color: #e2e8f0;
        }}
        .detail-card * {{ box-sizing: border-box; }}
        .detail-card h3 {{ color:#e2e8f0; font-size:20px; font-weight:600; margin:0 0 16px; line-height:1.4; }}
        .meta-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:12px; margin-bottom:16px; }}
        .meta-item {{ display:flex; gap:8px; padding:8px 0; border-bottom:1px solid rgba(99,102,241,0.08); }}
        .meta-label {{ color:#94a3b8; font-size:13px; min-width:120px; }}
        .meta-value {{ color:#e2e8f0; font-size:13px; }}
        .content-box {{
            background: rgba(0,0,0,0.2);
            border: 1px solid rgba(99,102,241,0.1);
            border-radius: 10px;
            padding: 18px;
            margin-top: 16px;
        }}
        .content-box h4 {{ color:#a78bfa; font-size:15px; font-weight:600; margin:0 0 12px; }}
        .content-box p {{ color:#e2e8f0; font-size:16px; line-height:1.8; white-space:pre-wrap; }}
        .content-box .empty {{ color:#94a3b8; font-style:italic; }}
        </style>

        <div class="detail-card">
            <h3>{title_safe}</h3>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">
                {source_badge(article["nguon_tin"])}
                {category_badge(article["danh_muc"])}
                {sentiment_badge(nhan, diem)}
                {stock_badges(tickers)}
            </div>

            <div class="meta-grid">
                <div>
                    <div class="meta-item"><span class="meta-label">🆔 ID</span><span class="meta-value" style="font-family:monospace;font-size:11px">{article_id_safe}</span></div>
                    <div class="meta-item"><span class="meta-label">📡 Nguồn</span><span class="meta-value">{source_safe}</span></div>
                    <div class="meta-item"><span class="meta-label">📂 Danh mục</span><span class="meta-value">{category_safe}</span></div>
                    <div class="meta-item"><span class="meta-label">📅 Xuất bản</span><span class="meta-value">{published_safe}</span></div>
                </div>
                <div>
                    <div class="meta-item"><span class="meta-label">💭 Điểm CX</span><span class="meta-value" style="color:{"#4ade80" if diem > 0.1 else ("#f87171" if diem < -0.1 else "#94a3b8")}">{diem:+.4f}</span></div>
                    <div class="meta-item"><span class="meta-label">🏷️ Mã CK</span><span class="meta-value">{ticker_text}</span></div>
                    <div class="meta-item"><span class="meta-label">🧬 Vector ID</span><span class="meta-value" style="font-family:monospace;font-size:11px">{vector_text}</span></div>
                    <div class="meta-item"><span class="meta-label">📋 Trạng thái</span><span class="meta-value">{status_safe}</span></div>
                </div>
            </div>

            <div class="meta-item"><span class="meta-label">🔗 URL</span><span class="meta-value"><a href="{url_safe}" target="_blank">{url_safe}</a></span></div>

            <div class="content-box">
                <h4>📝 Nội dung tóm tắt ({article["len_tom_tat"]} ký tự)</h4>
                <p>{summary_text}</p>
            </div>

            <div class="content-box">
                <h4>📄 Nội dung gốc ({article["len_goc"]} ký tự)</h4>
                <p>{full_text}</p>
            </div>
        </div>
        """

        st.html(textwrap.dedent(detail_html))

        # Re-run sentiment analysis button
        if st.button("🔄 Phân tích lại Cảm xúc (Dùng quy tắc & AI mới)", key=f"re-sent-{article['id']}"):
            with st.spinner("Đang phân tích lại..."):
                from news_ingestor.processing.sentiment import BoPhanTichCamXuc
                cau_hinh_nlp = lay_cau_hinh_nlp()
                gemini_key = cau_hinh_nlp.gemini_api_key if cau_hinh_nlp.gemini_api_key else None
                phan_tich = BoPhanTichCamXuc(gemini_api_key=gemini_key)
                # Dùng full content nếu có
                text_to_analyze = f"{article['tieu_de']} {article['noi_dung_tom_tat']} {article['noi_dung_goc']}"
                res = phan_tich.phan_tich(text_to_analyze)
                
                # Update DB
                conn = sqlite3.connect(str(DB_PATH))
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tin_tuc_tai_chinh SET nhan_cam_xuc = ?, diem_cam_xuc = ? WHERE id = ?",
                    (res["nhan"].value if hasattr(res["nhan"], 'value') else str(res["nhan"]), res["diem"], article["id"]),
                )
                conn.commit()
                conn.close()
                st.success(f"Đã cập nhật: {res['nhan']} ({res['diem']:+.2f})")
                st.cache_data.clear()
                st.rerun()

        # Quality analysis
        st.markdown('<div class="section-header">🔬 Phân tích chất lượng bài báo</div>', unsafe_allow_html=True)

        q_cols = st.columns(5)
        checks = [
            ("📝 Nội dung", article["has_content"], f"{article['len_goc']} ch"),
            ("📋 Tóm tắt", article["has_summary"], f"{article['len_tom_tat']} ch"),
            ("💭 Sentiment", article["has_sentiment"], f"{diem:+.2f}"),
            ("🏷️ Mã CK", article["has_tickers"], f"{len(tickers)} mã"),
            ("🧬 Vector", article["has_vector"], article["vector_id"][:8] + "..." if article["vector_id"] else "N/A"),
        ]
        for c, (label, ok, detail) in zip(q_cols, checks, strict=False):
            with c:
                if ok:
                    st.success(f"✅ {label}\n\n{detail}")
                else:
                    st.error(f"❌ {label}\n\n{detail}")

        # Content comparison
        if article["noi_dung_goc"] and article["noi_dung_tom_tat"]:
            if article["noi_dung_goc"] == article["noi_dung_tom_tat"]:
                st.warning("⚠️ `noi_dung_goc` và `noi_dung_tom_tat` **giống hệt nhau** — Crawler chưa lấy nội dung đầy đủ, chỉ lấy RSS description")
            else:
                st.info(f"ℹ️ Nội dung gốc ({article['len_goc']} ch) khác tóm tắt ({article['len_tom_tat']} ch)")

        # Raw JSON
        with st.expander("📊 Raw JSON Data"):
            raw = article.to_dict()
            for k, v in raw.items():
                if isinstance(v, pd.Timestamp):
                    raw[k] = v.isoformat() if pd.notna(v) else None
                elif isinstance(v, (bool,)):
                    raw[k] = bool(v)
            st.json(raw)


# ============================================
# PAGE: CHẨN ĐOÁN PIPELINE
# ============================================

elif page == "🩺 Chẩn đoán Pipeline":
    st.markdown("""
    <div class="main-header">
        <h1>🩺 Chẩn đoán Pipeline</h1>
        <p>Phân tích chi tiết chất lượng dữ liệu, tìm lỗi và vấn đề trong pipeline</p>
    </div>
    """, unsafe_allow_html=True)

    total = len(filtered)

    # Diagnostics cards
    diag_html = f"""
    <style>{BADGE_CSS}
    .diag-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:16px; }}
    .diag-card {{
        background: linear-gradient(135deg, #1e1e3f 0%, #16162e 100%);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 12px;
        padding: 20px;
    }}
    .diag-card h5 {{ color:#e2e8f0; font-size:15px; font-weight:600; margin:0 0 12px; }}
    .diag-row {{ display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(99,102,241,0.06); font-size:13px; }}
    .diag-row:last-child {{ border-bottom:none; }}
    .diag-key {{ color:#94a3b8; }}
    .diag-val {{ font-weight:500; }}
    .ok {{ color:#4ade80; }}
    .warn {{ color:#fbbf24; }}
    .err {{ color:#f87171; }}
    </style>
    <div class="diag-grid">
        <div class="diag-card">
            <h5>📝 Nội dung (Content)</h5>
            <div class="diag-row"><span class="diag-key">Có nội dung gốc</span><span class="diag-val {'ok' if filtered['has_content'].sum() == total else 'warn'}">{filtered['has_content'].sum()}/{total}</span></div>
            <div class="diag-row"><span class="diag-key">Có tóm tắt</span><span class="diag-val {'ok' if filtered['has_summary'].sum() == total else 'warn'}">{filtered['has_summary'].sum()}/{total}</span></div>
            <div class="diag-row"><span class="diag-key">Nội dung = Tóm tắt</span><span class="diag-val {'err' if (filtered['noi_dung_goc'] == filtered['noi_dung_tom_tat']).sum() > total * 0.5 else 'ok'}">{(filtered['noi_dung_goc'] == filtered['noi_dung_tom_tat']).sum()}/{total}</span></div>
            <div class="diag-row"><span class="diag-key">Avg length (gốc)</span><span class="diag-val {'warn' if filtered['len_goc'].mean() < 300 else 'ok'}">{filtered['len_goc'].mean():.0f} ch</span></div>
            <div class="diag-row"><span class="diag-key">Max length</span><span class="diag-val">{filtered['len_goc'].max()} ch</span></div>
            <div class="diag-row"><span class="diag-key">Min length</span><span class="diag-val {'err' if filtered['len_goc'].min() == 0 else 'ok'}">{filtered['len_goc'].min()} ch</span></div>
        </div>

        <div class="diag-card">
            <h5>💭 NLP / Sentiment</h5>
            <div class="diag-row"><span class="diag-key">Có sentiment != 0</span><span class="diag-val {'warn' if filtered['has_sentiment'].sum() < total * 0.3 else 'ok'}">{filtered['has_sentiment'].sum()}/{total}</span></div>
            <div class="diag-row"><span class="diag-key">POSITIVE</span><span class="diag-val ok">{len(filtered[filtered['nhan_cam_xuc'] == 'POSITIVE'])}</span></div>
            <div class="diag-row"><span class="diag-key">NEGATIVE</span><span class="diag-val err">{len(filtered[filtered['nhan_cam_xuc'] == 'NEGATIVE'])}</span></div>
            <div class="diag-row"><span class="diag-key">NEUTRAL</span><span class="diag-val">{len(filtered[filtered['nhan_cam_xuc'] == 'NEUTRAL'])}</span></div>
            <div class="diag-row"><span class="diag-key">score NULL</span><span class="diag-val {'err' if filtered['diem_cam_xuc'].isna().sum() > 0 else 'ok'}">{filtered['diem_cam_xuc'].isna().sum()}</span></div>
            <div class="diag-row"><span class="diag-key">Avg score</span><span class="diag-val">{filtered['diem_cam_xuc'].mean():+.4f}</span></div>
        </div>

        <div class="diag-card">
            <h5>🏷️ NER / Mã CK</h5>
            <div class="diag-row"><span class="diag-key">Bài có mã CK</span><span class="diag-val">{filtered['has_tickers'].sum()}/{total}</span></div>
            <div class="diag-row"><span class="diag-key">Tổng mã phát hiện</span><span class="diag-val">{sum(len(x) for x in filtered['ma_ck_list'])}</span></div>
            <div class="diag-row"><span class="diag-key">Unique mã CK</span><span class="diag-val">{len(set(t for tl in filtered['ma_ck_list'] for t in tl))}</span></div>
        </div>

        <div class="diag-card">
            <h5>🧬 Embeddings / Vector</h5>
            <div class="diag-row"><span class="diag-key">Có vector_id</span><span class="diag-val {'ok' if filtered['has_vector'].sum() == total else 'warn'}">{filtered['has_vector'].sum()}/{total}</span></div>
            <div class="diag-row"><span class="diag-key">Thiếu vector</span><span class="diag-val {'err' if total - filtered['has_vector'].sum() > 0 else 'ok'}">{total - filtered['has_vector'].sum()}</span></div>
            <div class="diag-row"><span class="diag-key">Trạng thái COMPLETED</span><span class="diag-val">{len(filtered[filtered['trang_thai'] == 'COMPLETED'])}</span></div>
            <div class="diag-row"><span class="diag-key">Trạng thái khác</span><span class="diag-val {'warn' if len(filtered[filtered['trang_thai'] != 'COMPLETED']) > 0 else 'ok'}">{len(filtered[filtered['trang_thai'] != 'COMPLETED'])}</span></div>
        </div>
    </div>
    """
    components.html(diag_html, height=520, scrolling=False)

    # Content length distribution
    st.markdown('<div class="section-header">📏 Phân bố độ dài nội dung</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(filtered, x="len_goc", nbins=30,
                           labels={"len_goc": "Độ dài nội dung gốc (ký tự)", "count": "Số bài"},
                           color_discrete_sequence=["#6366f1"])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#94a3b8", family="Inter"),
                          xaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                          yaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                          margin=dict(l=0,r=0,t=20,b=0), height=250, title="Nội dung gốc")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig2 = px.histogram(filtered[filtered["diem_cam_xuc"].notna()], x="diem_cam_xuc", nbins=30,
                            labels={"diem_cam_xuc": "Điểm cảm xúc", "count": "Số bài"},
                            color_discrete_sequence=["#8b5cf6"])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font=dict(color="#94a3b8", family="Inter"),
                           xaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                           yaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                           margin=dict(l=0,r=0,t=20,b=0), height=250, title="Phân bố cảm xúc")
        st.plotly_chart(fig2, use_container_width=True)

    # Problem articles
    st.markdown('<div class="section-header">🚨 Bài có vấn đề</div>', unsafe_allow_html=True)

    problem_filter = st.selectbox("Loại vấn đề", [
        "Tất cả bài có vấn đề",
        "Không có nội dung",
        "Nội dung = Tóm tắt (chưa crawl đầy đủ)",
        "Sentiment score NULL",
        "Nội dung quá ngắn (< 100 ch)",
    ])

    if problem_filter == "Không có nội dung":
        problems = filtered[~filtered["has_content"]]
    elif problem_filter == "Nội dung = Tóm tắt (chưa crawl đầy đủ)":
        problems = filtered[filtered["noi_dung_goc"] == filtered["noi_dung_tom_tat"]]
    elif problem_filter == "Sentiment score NULL":
        problems = filtered[filtered["diem_cam_xuc"].isna()]
    elif problem_filter == "Nội dung quá ngắn (< 100 ch)":
        problems = filtered[filtered["len_goc"] < 100]
    else:
        problems = filtered[
            (~filtered["has_content"]) |
            (filtered["diem_cam_xuc"].isna()) |
            (filtered["len_goc"] < 100)
        ]

    st.caption(f"Tìm thấy **{len(problems)}** bài")
    if not problems.empty:
        display_df = problems[["tieu_de", "nguon_tin", "danh_muc", "len_goc", "diem_cam_xuc", "nhan_cam_xuc", "has_vector"]].copy()
        display_df.columns = ["Tiêu đề", "Nguồn", "Danh mục", "Độ dài", "Điểm CX", "Nhãn CX", "Vector"]
        display_df["Tiêu đề"] = display_df["Tiêu đề"].str[:60]
        st.dataframe(display_df, use_container_width=True, height=400)


# ============================================
# PAGE: NGUỒN & CRAWL
# ============================================

elif page == "📡 Nguồn & Crawl":
    st.markdown("""
    <div class="main-header">
        <h1>📡 Phân tích nguồn tin & Crawl</h1>
        <p>Thống kê chi tiết theo từng nguồn, hiệu suất crawler, và đo chất lượng</p>
    </div>
    """, unsafe_allow_html=True)

    # Source breakdown
    st.markdown('<div class="section-header">📊 Thống kê theo nguồn</div>', unsafe_allow_html=True)

    source_stats = []
    for src in sorted(filtered["nguon_tin"].unique()):
        src_df = filtered[filtered["nguon_tin"] == src]
        source_stats.append({
            "Nguồn": src,
            "Tổng bài": len(src_df),
            "Có nội dung": src_df["has_content"].sum(),
            "Avg len": f"{src_df['len_goc'].mean():.0f}",
            "Có sentiment": src_df["has_sentiment"].sum(),
            "Tích cực": len(src_df[src_df["nhan_cam_xuc"] == "POSITIVE"]),
            "Tiêu cực": len(src_df[src_df["nhan_cam_xuc"] == "NEGATIVE"]),
            "Trung tính": len(src_df[src_df["nhan_cam_xuc"] == "NEUTRAL"]),
            "Có mã CK": src_df["has_tickers"].sum(),
            "Content=Summary": (src_df["noi_dung_goc"] == src_df["noi_dung_tom_tat"]).sum(),
        })

    stats_df = pd.DataFrame(source_stats)
    st.dataframe(stats_df, use_container_width=True, height=300)

    # Top tickers
    st.markdown('<div class="section-header">🏷️ Top mã CK theo nguồn</div>', unsafe_allow_html=True)

    all_tickers = []
    for _, r in filtered.iterrows():
        for t in r["ma_ck_list"]:
            all_tickers.append({"Mã": t, "Nguồn": r["nguon_tin"]})

    if all_tickers:
        ticker_df = pd.DataFrame(all_tickers)
        fig = px.bar(
            ticker_df.groupby(["Mã", "Nguồn"]).size().reset_index(name="n").sort_values("n", ascending=False).head(30),
            x="n", y="Mã", color="Nguồn", orientation="h",
            color_discrete_sequence=["#6366f1","#8b5cf6","#a78bfa","#c4b5fd","#ec4899","#f472b6","#818cf8"],
            labels={"n": "Số bài", "Mã": ""},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            xaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
            yaxis=dict(autorange="reversed"),
            margin=dict(l=0,r=0,t=10,b=0), height=max(200, len(ticker_df["Mã"].unique()) * 25),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Chưa phát hiện mã CK nào.")

    # Crawl logs
    st.markdown('<div class="section-header">📋 Nhật ký thu thập</div>', unsafe_allow_html=True)
    logs = load_crawl_logs()
    if not logs.empty:
        st.dataframe(logs, use_container_width=True)
    else:
        st.info("Chưa có nhật ký thu thập. Hệ thống chưa ghi nhật ký hoặc chưa có lần crawl nào được log.")


# ============================================
# FOOTER
# ============================================

st.markdown("""
<div style="text-align:center;padding:30px 0 10px;color:#475569;font-size:11px">
    <p>🇻🇳 <strong>News Pipeline Monitor</strong> — Streamlit + Plotly · Data: CafeF · VnExpress · VietStock · RSS</p>
</div>
""", unsafe_allow_html=True)
