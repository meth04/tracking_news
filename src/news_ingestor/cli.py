"""CLI - Giao diện dòng lệnh cho hệ thống thu thập tin tức tài chính."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import socket
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import click

# Thêm thư mục gốc vào path để import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@click.group()
@click.option("--log-level", default="INFO", help="Cấp độ log: DEBUG, INFO, WARNING, ERROR")
@click.option("--json-log", is_flag=True, default=False, help="Xuất log dạng JSON (production)")
@click.pass_context
def cli(ctx: click.Context, log_level: str, json_log: bool) -> None:
    """🗞️ Hệ thống Thu thập và Xử lý Tin tức Tài chính.

    Tự động thu thập, phân tích cảm xúc, và phục vụ tin tức qua MCP Server.
    """
    from news_ingestor.utils.logging_config import cau_hinh_logging

    cau_hinh_logging(cap_do=log_level, json_mode=json_log)
    ctx.ensure_object(dict)


def _tim_cong_trong() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@cli.command("demo")
def chay_demo() -> None:
    """🚀 Chạy dashboard demo trên cổng trống tự động."""
    dashboard_path = Path(__file__).resolve().parent.parent.parent / "dashboard.py"

    if not dashboard_path.exists():
        raise click.ClickException("Không tìm thấy dashboard.py ở thư mục gốc dự án.")

    if importlib.util.find_spec("streamlit") is None:
        raise click.ClickException(
            "Thiếu dependency 'streamlit'. Cài bằng: pip install streamlit"
        )

    cong = _tim_cong_trong()
    url = f"http://127.0.0.1:{cong}"

    click.echo(f"🚀 Demo dashboard đang chạy tại: {url}")
    click.echo("   Nhấn Ctrl+C để dừng")

    ket_qua = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(dashboard_path),
            "--server.address",
            "127.0.0.1",
            "--server.port",
            str(cong),
            "--server.headless",
            "true",
        ],
        check=False,
    )

    if ket_qua.returncode not in {0, 130}:
        raise click.ClickException(
            f"Dashboard thoát với mã lỗi {ket_qua.returncode}."
        )


@cli.command("init-db")
def khoi_tao_db() -> None:
    """🗄️ Khởi tạo cơ sở dữ liệu (tạo bảng)."""
    from news_ingestor.storage.database import lay_quan_ly_db

    click.echo("📦 Đang khởi tạo cơ sở dữ liệu...")
    db = lay_quan_ly_db()
    db.khoi_tao_bang()
    click.echo("✅ Đã khởi tạo database thành công!")

    # Hiển thị thông tin
    from news_ingestor.storage.repository import KhoTinTuc
    kho = KhoTinTuc()
    so_bai = kho.dem_bai_bao()
    click.echo(f"📊 Số bài báo hiện có: {so_bai}")


@cli.command("crawl")
@click.option("--once", is_flag=True, default=False, help="Chạy một lần rồi thoát")
@click.option("--daemon", is_flag=True, default=False, help="Chạy liên tục (daemon mode)")
@click.option(
    "--interval",
    type=int,
    default=900,
    help="Khoảng cách giữa các lần (giây, mặc định 900 = 15 phút)",
)
@click.option("--skip-nlp", is_flag=True, default=False, help="Bỏ qua bước xử lý NLP")
@click.option("--no-embedding", is_flag=True, default=False, help="Không tạo embeddings")
def thu_thap(once: bool, daemon: bool, interval: int, skip_nlp: bool, no_embedding: bool) -> None:
    """🕷️ Thu thập tin tức từ các nguồn.

    Mặc định chạy một lần. Dùng --daemon để chạy liên tục.
    """
    import logging

    from config.settings import lay_cau_hinh_he_thong
    from news_ingestor.crawlers.scheduler import BoLichThuThap
    from news_ingestor.storage.database import lay_quan_ly_db

    logger = logging.getLogger(__name__)

    # Khởi tạo DB
    db = lay_quan_ly_db()
    db.khoi_tao_bang()

    # Khởi tạo scheduler
    scheduler = BoLichThuThap()
    scheduler.dang_ky_tat_ca()

    if not skip_nlp:
        # Tạo pipeline callback
        from news_ingestor.processing.pipeline import LuongXuLy
        from news_ingestor.storage.repository import KhoTinTuc

        kho_vector = None
        if not no_embedding:
            try:
                from news_ingestor.storage.vector_store import KhoVector
                kho_vector = KhoVector()
                kho_vector.ket_noi()
            except Exception as e:
                logger.warning(f"Không thể kết nối Vector DB: {e}")

        cau_hinh_he_thong = lay_cau_hinh_he_thong()

        bo_canh_bao = None
        if cau_hinh_he_thong.telegram_alert_enabled:
            from news_ingestor.utils.alerting import tao_bo_canh_bao_tu_env

            bo_canh_bao = tao_bo_canh_bao_tu_env(
                telegram_enabled=cau_hinh_he_thong.telegram_alert_enabled,
                telegram_bot_token=cau_hinh_he_thong.telegram_bot_token,
                telegram_chat_id=cau_hinh_he_thong.telegram_chat_id,
            )
            if bo_canh_bao is None:
                logger.warning(
                    "TELEGRAM_ALERT_ENABLED=true nhưng thiếu "
                    "TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID"
                )

        pipeline = LuongXuLy(
            kho_tin_tuc=KhoTinTuc(),
            kho_vector=kho_vector,
            tao_embedding=not no_embedding and kho_vector is not None,
            bo_canh_bao=bo_canh_bao,
        )

        def callback(danh_sach_bai):
            pipeline.xu_ly_hang_loat(danh_sach_bai)

        scheduler.dat_callback(callback)
    else:
        click.echo("⚠️ Bỏ qua xử lý NLP (--skip-nlp)")

    if daemon:
        click.echo(f"🔄 Chế độ daemon - Chu kỳ: {interval}s ({interval // 60} phút)")
        click.echo("   Nhấn Ctrl+C để dừng")
        scheduler.chay_daemon(khoang_cach_giay=interval)
    else:
        click.echo("▶️ Thu thập một lần...")
        ket_qua = scheduler.chay_mot_lan()
        click.echo(f"✅ Hoàn thành! Thu được {len(ket_qua)} bài báo")


@cli.command("serve-mcp")
def phuc_vu_mcp() -> None:
    """🌐 Khởi động MCP Server cho AI Agent.

    Server chạy qua stdio protocol.
    """
    click.echo("🌐 Đang khởi động MCP Server: tin-tuc-tai-chinh...")
    click.echo(
        "   Tools: tim_tin_vi_mo, lay_tin_doanh_nghiep, tim_kiem_ngu_nghia, "
        "lay_cam_xuc_thi_truong, lay_metrics"
    )

    from news_ingestor.mcp_server.server import chay_server
    asyncio.run(chay_server())


@cli.command("high-impact")
@click.option("--days", type=int, default=3, help="Số ngày gần nhất")
@click.option("--limit", type=int, default=20, help="Số lượng kết quả tối đa")
def tin_tac_dong_cao(days: int, limit: int) -> None:
    """📣 Hiển thị các tin có tác động cao đến tài chính Việt Nam."""
    from news_ingestor.storage.database import lay_quan_ly_db
    from news_ingestor.storage.repository import KhoTinTuc

    db = lay_quan_ly_db()
    db.khoi_tao_bang()

    kho = KhoTinTuc()
    ket_qua = kho.lay_tin_tac_dong_cao(so_ngay=days, gioi_han=limit)

    if not ket_qua:
        click.echo(f"Không có tin tác động cao trong {days} ngày gần nhất.")
        return

    click.echo(f"📣 TIN TÁC ĐỘNG CAO ({len(ket_qua)} kết quả, {days} ngày gần nhất)")
    for i, bai in enumerate(ket_qua, 1):
        tags = ", ".join(bai.impact_tags[:4]) if bai.impact_tags else "-"
        click.echo(
            f"{i}. [{bai.impact_level}] score={bai.impact_score} | {bai.tieu_de}\n"
            f"   {bai.nguon_tin} | {bai.thoi_gian_xuat_ban.strftime('%Y-%m-%d %H:%M')}\n"
            f"   Tags: {tags}\n"
            f"   URL: {bai.url}\n"
        )


@cli.command("stats")
def thong_ke() -> None:
    """📊 Hiển thị thống kê hệ thống."""
    from news_ingestor.storage.database import lay_quan_ly_db
    from news_ingestor.storage.repository import KhoTinTuc

    db = lay_quan_ly_db()
    db.khoi_tao_bang()

    kho = KhoTinTuc()
    so_bai = kho.dem_bai_bao()

    click.echo("╔══════════════════════════════════════════╗")
    click.echo("║  📊 THỐNG KÊ HỆ THỐNG TIN TỨC TÀI CHÍNH  ║")
    click.echo("╠══════════════════════════════════════════╣")
    click.echo(f"║  📰 Tổng số bài báo:  {so_bai:>10}          ║")

    # Thống kê cảm xúc
    thong_ke = kho.lay_cam_xuc_thi_truong(so_ngay=7)
    click.echo(f"║  📈 Tin tích cực (7d): {thong_ke.so_tin_tich_cuc:>10}          ║")
    click.echo(f"║  📉 Tin tiêu cực (7d): {thong_ke.so_tin_tieu_cuc:>10}          ║")
    click.echo(f"║  ➡️  Tin trung tính:   {thong_ke.so_tin_trung_tinh:>10}          ║")
    click.echo(f"║  🎯 Điểm TB (7d):    {thong_ke.diem_trung_binh:>+10.4f}          ║")
    click.echo(f"║  📊 Xu hướng:         {thong_ke.xu_huong:>10}          ║")
    click.echo("╚══════════════════════════════════════════╝")


@cli.command("evaluate")
@click.option("--days", type=int, default=7, help="Khung thời gian đánh giá (ngày)")
@click.option("--limit", type=int, default=500, help="Số bản ghi tối đa để đánh giá")
@click.option("--json-output", is_flag=True, default=False, help="In kết quả dạng JSON")
def danh_gia(days: int, limit: int, json_output: bool) -> None:
    """🧪 Đánh giá chất lượng pipeline trên dữ liệu đã ingest."""
    from news_ingestor.storage.database import lay_quan_ly_db
    from news_ingestor.storage.repository import KhoTinTuc
    from news_ingestor.utils.evaluation import tao_bao_cao_pipeline

    db = lay_quan_ly_db()
    db.khoi_tao_bang()

    kho = KhoTinTuc()
    ds = kho.lay_tat_ca(gioi_han=limit)
    bao_cao = tao_bao_cao_pipeline(ds_bai=ds, so_ngay=days)

    if json_output:
        click.echo(json.dumps(asdict(bao_cao), ensure_ascii=False, indent=2))
        return

    click.echo("Evaluation summary")
    click.echo(f"- Window (days): {bao_cao.window_days}")
    click.echo(f"- Total articles: {bao_cao.total_articles}")
    click.echo(f"- Unique sources: {bao_cao.unique_sources}")
    click.echo(f"- Content coverage: {bao_cao.coverage['has_content_ratio'] * 100:.2f}%")
    click.echo(f"- Summary coverage: {bao_cao.coverage['has_summary_ratio'] * 100:.2f}%")
    click.echo(f"- Sentiment coverage: {bao_cao.coverage['has_sentiment_ratio'] * 100:.2f}%")
    click.echo(f"- Ticker coverage: {bao_cao.coverage['has_tickers_ratio'] * 100:.2f}%")
    click.echo(f"- Vector coverage: {bao_cao.coverage['has_vector_ratio'] * 100:.2f}%")
    click.echo(
        "- Impact dist (LOW/MEDIUM/HIGH): "
        f"{bao_cao.impact_distribution['LOW']}/"
        f"{bao_cao.impact_distribution['MEDIUM']}/"
        f"{bao_cao.impact_distribution['HIGH']}"
    )
    click.echo(f"- High impact ratio: {bao_cao.high_impact_ratio * 100:.2f}%")
    click.echo(f"- Avg sentiment: {bao_cao.sentiment_average:+.4f}")
    click.echo(
        f"- Avg length (orig/sum): {bao_cao.avg_original_length:.2f}/"
        f"{bao_cao.avg_summary_length:.2f}"
    )


def main() -> None:
    """Entry point chính."""
    cli()


if __name__ == "__main__":
    main()
