"""MCP Server - Bộ công cụ AI Agent cho tin tức tài chính.

Cung cấp 4 tools qua giao thức MCP:
1. tim_tin_vi_mo - Tìm tin tức vĩ mô theo thời gian và chủ đề
2. lay_tin_doanh_nghiep - Tin tức + sentiment theo mã chứng khoán
3. tim_kiem_ngu_nghia - Semantic search qua Vector DB
4. lay_cam_xuc_thi_truong - Thống kê cảm xúc tổng hợp
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from news_ingestor.storage.repository import KhoTinTuc
from news_ingestor.storage.vector_store import KhoVector
from news_ingestor.processing.embeddings import BoTaoEmbeddings

logger = logging.getLogger(__name__)

# Khởi tạo MCP Server
server = Server("tin-tuc-tai-chinh")

# Storage instances (khởi tạo lazy)
_kho_tin_tuc: Optional[KhoTinTuc] = None
_kho_vector: Optional[KhoVector] = None
_bo_embedding: Optional[BoTaoEmbeddings] = None


def _lay_kho_tin_tuc() -> KhoTinTuc:
    global _kho_tin_tuc
    if _kho_tin_tuc is None:
        _kho_tin_tuc = KhoTinTuc()
    return _kho_tin_tuc


def _lay_kho_vector() -> KhoVector:
    global _kho_vector
    if _kho_vector is None:
        _kho_vector = KhoVector()
        _kho_vector.ket_noi()
    return _kho_vector


def _lay_bo_embedding() -> BoTaoEmbeddings:
    global _bo_embedding
    if _bo_embedding is None:
        _bo_embedding = BoTaoEmbeddings()
    return _bo_embedding


# ============================================
# ĐĂNG KÝ DANH SÁCH TOOLS
# ============================================

@server.list_tools()
async def danh_sach_tools() -> list[Tool]:
    """Trả về danh sách tools có sẵn."""
    return [
        Tool(
            name="tim_tin_vi_mo",
            description=(
                "Tìm kiếm tin tức vĩ mô (lãi suất, tỷ giá, GDP, CPI, chính sách tiền tệ...) "
                "theo khung thời gian và chủ đề. Dùng khi cần đánh giá bối cảnh kinh tế vĩ mô."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "khung_thoi_gian": {
                        "type": "string",
                        "description": "Khung thời gian: '1d', '7d', '1m', '3m' (ngày/tuần/tháng)",
                        "default": "7d",
                    },
                    "chu_de": {
                        "type": "string",
                        "description": "Chủ đề tìm kiếm (VD: 'lãi suất', 'tỷ giá', 'GDP')",
                        "default": "",
                    },
                    "gioi_han": {
                        "type": "integer",
                        "description": "Số lượng kết quả tối đa",
                        "default": 20,
                    },
                },
            },
        ),
        Tool(
            name="lay_tin_doanh_nghiep",
            description=(
                "Lấy tin tức và chỉ số cảm xúc (sentiment) của một mã cổ phiếu cụ thể. "
                "Dùng khi cần đánh giá tình hình doanh nghiệp trước khi ra quyết định mua/bán."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ma_ck": {
                        "type": "string",
                        "description": "Mã chứng khoán (VD: 'FPT', 'VCB', 'VIC')",
                    },
                    "ngay_bat_dau": {
                        "type": "string",
                        "description": "Ngày bắt đầu (ISO format: YYYY-MM-DD). Mặc định: 7 ngày trước",
                        "default": "",
                    },
                    "ngay_ket_thuc": {
                        "type": "string",
                        "description": "Ngày kết thúc (ISO format: YYYY-MM-DD). Mặc định: hôm nay",
                        "default": "",
                    },
                    "gioi_han": {
                        "type": "integer",
                        "description": "Số lượng kết quả tối đa",
                        "default": 30,
                    },
                },
                "required": ["ma_ck"],
            },
        ),
        Tool(
            name="tim_kiem_ngu_nghia",
            description=(
                "Tìm kiếm tin tức bằng câu hỏi tự nhiên (semantic search). "
                "Sử dụng Vector Database để tìm tin có ngữ nghĩa tương đồng. "
                "Dùng khi cần tìm tin liên quan đến một chủ đề phức tạp."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cau_hoi": {
                        "type": "string",
                        "description": "Câu hỏi hoặc chủ đề tìm kiếm bằng ngôn ngữ tự nhiên",
                    },
                    "gioi_han": {
                        "type": "integer",
                        "description": "Số lượng kết quả tối đa",
                        "default": 10,
                    },
                },
                "required": ["cau_hoi"],
            },
        ),
        Tool(
            name="lay_cam_xuc_thi_truong",
            description=(
                "Lấy thống kê tổng hợp cảm xúc thị trường cho một mã cổ phiếu "
                "hoặc toàn bộ thị trường. Trả về: điểm trung bình, số tin tích cực/"
                "tiêu cực, xu hướng chung. Dùng để đánh giá tâm lý thị trường."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ma_ck": {
                        "type": "string",
                        "description": "Mã CK cụ thể hoặc để trống cho toàn thị trường",
                        "default": "",
                    },
                    "so_ngay": {
                        "type": "integer",
                        "description": "Số ngày gần nhất để thống kê",
                        "default": 7,
                    },
                },
            },
        ),
    ]


# ============================================
# XỬ LÝ GỌI TOOLS
# ============================================

@server.call_tool()
async def goi_tool(name: str, arguments: dict) -> list[TextContent]:
    """Xử lý lời gọi tool từ AI Agent."""
    try:
        if name == "tim_tin_vi_mo":
            return await _xu_ly_tim_tin_vi_mo(arguments)
        elif name == "lay_tin_doanh_nghiep":
            return await _xu_ly_lay_tin_doanh_nghiep(arguments)
        elif name == "tim_kiem_ngu_nghia":
            return await _xu_ly_tim_kiem_ngu_nghia(arguments)
        elif name == "lay_cam_xuc_thi_truong":
            return await _xu_ly_lay_cam_xuc(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"Lỗi: Tool '{name}' không tồn tại.",
            )]
    except Exception as e:
        logger.error(f"Lỗi xử lý tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Lỗi khi thực thi tool '{name}': {str(e)}",
        )]


async def _xu_ly_tim_tin_vi_mo(args: dict) -> list[TextContent]:
    """Xử lý tool tìm tin vĩ mô."""
    kho = _lay_kho_tin_tuc()
    khung_tg = args.get("khung_thoi_gian", "7d")
    chu_de = args.get("chu_de", "")
    gioi_han = args.get("gioi_han", 20)

    ket_qua = kho.tim_tin_vi_mo(
        khung_thoi_gian=khung_tg,
        chu_de=chu_de if chu_de else None,
        gioi_han=gioi_han,
    )

    if not ket_qua:
        return [TextContent(
            type="text",
            text=f"Không tìm thấy tin vĩ mô nào trong {khung_tg} về '{chu_de}'.",
        )]

    # Format kết quả
    output_lines = [f"📊 TIN TỨC VĨ MÔ ({len(ket_qua)} kết quả)\n"]
    for i, bai in enumerate(ket_qua, 1):
        cam_xuc_icon = "🟢" if bai.diem_cam_xuc > 0.1 else ("🔴" if bai.diem_cam_xuc < -0.1 else "⚪")
        output_lines.append(
            f"{i}. {cam_xuc_icon} [{bai.nguon_tin}] {bai.tieu_de}\n"
            f"   📅 {bai.thoi_gian_xuat_ban.strftime('%d/%m/%Y %H:%M')}\n"
            f"   💯 Cảm xúc: {bai.diem_cam_xuc:+.2f} ({bai.nhan_cam_xuc})\n"
            f"   📝 {bai.noi_dung_tom_tat[:150]}...\n"
        )

    return [TextContent(type="text", text="\n".join(output_lines))]


async def _xu_ly_lay_tin_doanh_nghiep(args: dict) -> list[TextContent]:
    """Xử lý tool lấy tin doanh nghiệp."""
    kho = _lay_kho_tin_tuc()
    ma_ck = args.get("ma_ck", "").upper()

    ngay_bd = None
    ngay_kt = None
    if args.get("ngay_bat_dau"):
        ngay_bd = datetime.fromisoformat(args["ngay_bat_dau"])
    if args.get("ngay_ket_thuc"):
        ngay_kt = datetime.fromisoformat(args["ngay_ket_thuc"])

    gioi_han = args.get("gioi_han", 30)

    ket_qua = kho.tim_theo_ma_ck(
        ma_ck=ma_ck,
        ngay_bat_dau=ngay_bd,
        ngay_ket_thuc=ngay_kt,
        gioi_han=gioi_han,
    )

    if not ket_qua:
        return [TextContent(
            type="text",
            text=f"Không tìm thấy tin tức nào cho mã {ma_ck}.",
        )]

    # Thống kê nhanh
    tong_diem = sum(b.diem_cam_xuc for b in ket_qua)
    tb = tong_diem / len(ket_qua) if ket_qua else 0

    output_lines = [
        f"📈 TIN TỨC DOANH NGHIỆP: {ma_ck} ({len(ket_qua)} kết quả)\n"
        f"📊 Cảm xúc trung bình: {tb:+.3f}\n"
    ]

    for i, bai in enumerate(ket_qua, 1):
        cam_xuc_icon = "🟢" if bai.diem_cam_xuc > 0.1 else ("🔴" if bai.diem_cam_xuc < -0.1 else "⚪")
        output_lines.append(
            f"{i}. {cam_xuc_icon} {bai.tieu_de}\n"
            f"   📅 {bai.thoi_gian_xuat_ban.strftime('%d/%m/%Y')} | "
            f"Nguồn: {bai.nguon_tin} | "
            f"Cảm xúc: {bai.diem_cam_xuc:+.2f}\n"
        )

    return [TextContent(type="text", text="\n".join(output_lines))]


async def _xu_ly_tim_kiem_ngu_nghia(args: dict) -> list[TextContent]:
    """Xử lý tool tìm kiếm ngữ nghĩa."""
    cau_hoi = args.get("cau_hoi", "")
    gioi_han = args.get("gioi_han", 10)

    if not cau_hoi:
        return [TextContent(type="text", text="Vui lòng nhập câu hỏi tìm kiếm.")]

    try:
        # Tạo embedding cho câu hỏi
        bo_emb = _lay_bo_embedding()
        vector = bo_emb.tao_embedding(cau_hoi)

        # Tìm kiếm trong Vector DB
        kho_vec = _lay_kho_vector()
        ket_qua = kho_vec.tim_kiem_ngu_nghia(
            vector_truy_van=vector,
            gioi_han=gioi_han,
        )

        if not ket_qua:
            return [TextContent(
                type="text",
                text=f"Không tìm thấy tin tức liên quan đến: '{cau_hoi}'",
            )]

        output_lines = [f"🔍 KẾT QUẢ TÌM KIẾM NGỮ NGHĨA: '{cau_hoi}'\n"]
        for i, r in enumerate(ket_qua, 1):
            output_lines.append(
                f"{i}. 📰 {r.get('tieu_de', 'N/A')}\n"
                f"   🎯 Độ tương đồng: {r.get('diem_tuong_dong', 0):.2%}\n"
                f"   📂 {r.get('nguon_tin', '')} | {r.get('danh_muc', '')}\n"
            )

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Lỗi semantic search: {e}")
        return [TextContent(
            type="text",
            text=f"Lỗi tìm kiếm ngữ nghĩa: {str(e)}. "
                 "Kiểm tra model embedding và Vector DB.",
        )]


async def _xu_ly_lay_cam_xuc(args: dict) -> list[TextContent]:
    """Xử lý tool lấy cảm xúc thị trường."""
    kho = _lay_kho_tin_tuc()
    ma_ck = args.get("ma_ck", "") or None
    so_ngay = args.get("so_ngay", 7)

    thong_ke = kho.lay_cam_xuc_thi_truong(ma_ck=ma_ck, so_ngay=so_ngay)

    # Emoji xu hướng
    xu_huong_icon = {
        "TÍCH CỰC": "📈🟢",
        "TIÊU CỰC": "📉🔴",
        "TRUNG TÍNH": "➡️⚪",
    }

    icon = xu_huong_icon.get(thong_ke.xu_huong, "⚪")

    output = (
        f"📊 THỐNG KÊ CẢM XÚC THỊ TRƯỜNG\n"
        f"{'─' * 40}\n"
        f"🏢 Mã CK: {thong_ke.ma_chung_khoan}\n"
        f"📅 Khoảng thời gian: {so_ngay} ngày gần nhất\n"
        f"{'─' * 40}\n"
        f"{icon} Xu hướng: {thong_ke.xu_huong}\n"
        f"📊 Điểm trung bình: {thong_ke.diem_trung_binh:+.4f}\n"
        f"📰 Tổng số tin: {thong_ke.tong_so_tin}\n"
        f"   🟢 Tích cực: {thong_ke.so_tin_tich_cuc}\n"
        f"   🔴 Tiêu cực: {thong_ke.so_tin_tieu_cuc}\n"
        f"   ⚪ Trung tính: {thong_ke.so_tin_trung_tinh}\n"
    )

    return [TextContent(type="text", text=output)]


# ============================================
# KHỞI CHẠY SERVER
# ============================================

async def chay_server() -> None:
    """Khởi chạy MCP Server qua stdio."""
    from news_ingestor.storage.database import lay_quan_ly_db

    # Khởi tạo database
    db = lay_quan_ly_db()
    db.khoi_tao_bang()

    logger.info("Khởi động MCP Server: tin-tuc-tai-chinh")

    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)

