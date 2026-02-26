"""CLI - Giao diện dòng lệnh cho hệ thống thu thập tin tức tài chính."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

# Thêm thư mục gốc vào path để import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))


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

        pipeline = LuongXuLy(
            kho_tin_tuc=KhoTinTuc(),
            kho_vector=kho_vector,
            tao_embedding=not no_embedding and kho_vector is not None,
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
    click.echo("   Tools: tim_tin_vi_mo, lay_tin_doanh_nghiep, tim_kiem_ngu_nghia, lay_cam_xuc_thi_truong")

    from news_ingestor.mcp_server.server import chay_server
    asyncio.run(chay_server())


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


def main() -> None:
    """Entry point chính."""
    cli()


if __name__ == "__main__":
    main()
