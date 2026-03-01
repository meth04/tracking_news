"""Utilities đánh giá chất lượng pipeline và classifier impact."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from news_ingestor.models.article import BaiBao


@dataclass
class KetQuaDanhGiaImpact:
    """Kết quả đánh giá classifier impact trên tập gán nhãn."""

    so_mau: int
    dung: int
    accuracy: float
    confusion: dict[str, dict[str, int]]


@dataclass
class BaoCaoDanhGiaPipeline:
    """Báo cáo KPI pipeline trên dữ liệu đã lưu."""

    generated_at: str
    window_days: int
    total_articles: int
    unique_sources: int
    coverage: dict[str, float]
    sentiment_distribution: dict[str, int]
    sentiment_average: float
    impact_distribution: dict[str, int]
    high_impact_ratio: float
    avg_original_length: float
    avg_summary_length: float


def _lam_tron(so: float, chu_so: int = 4) -> float:
    return round(float(so), chu_so)


def _chuan_hoa_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def danh_gia_impact_classifier(
    du_doan: list[dict[str, str]],
    nhan_thuc_te: list[str],
) -> KetQuaDanhGiaImpact:
    """Đánh giá độ chính xác phân lớp impact level.

    Args:
        du_doan: Danh sách dict kết quả classifier, cần có key ``impact_level``.
        nhan_thuc_te: Danh sách nhãn thực tế tương ứng (LOW/MEDIUM/HIGH).
    """
    if len(du_doan) != len(nhan_thuc_te):
        raise ValueError("Kích thước du_doan và nhan_thuc_te phải bằng nhau")

    labels = ["LOW", "MEDIUM", "HIGH"]
    confusion: dict[str, dict[str, int]] = {
        label: {inner: 0 for inner in labels} for label in labels
    }

    dung = 0
    for ket_qua, y_true in zip(du_doan, nhan_thuc_te, strict=False):
        y_pred = str(ket_qua.get("impact_level", "LOW")).upper()
        if y_true not in confusion:
            confusion[y_true] = {inner: 0 for inner in labels}
        if y_pred not in confusion[y_true]:
            confusion[y_true][y_pred] = 0
        confusion[y_true][y_pred] += 1
        if y_true == y_pred:
            dung += 1

    tong = len(nhan_thuc_te)
    accuracy = _lam_tron(dung / tong if tong else 0.0)

    return KetQuaDanhGiaImpact(
        so_mau=tong,
        dung=dung,
        accuracy=accuracy,
        confusion=confusion,
    )


def _dem_phan_bo_sentiment(ds_bai: list[BaiBao]) -> dict[str, int]:
    dem = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for bai in ds_bai:
        nhan = str(bai.nhan_cam_xuc)
        if nhan not in dem:
            dem[nhan] = 0
        dem[nhan] += 1
    return dem


def _dem_phan_bo_impact(ds_bai: list[BaiBao]) -> dict[str, int]:
    dem = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for bai in ds_bai:
        muc = str(bai.impact_level).upper()
        if muc not in dem:
            dem[muc] = 0
        dem[muc] += 1
    return dem


def tao_bao_cao_pipeline(ds_bai: list[BaiBao], so_ngay: int) -> BaoCaoDanhGiaPipeline:
    """Tổng hợp KPI pipeline từ danh sách bài báo đã ingest."""
    if so_ngay <= 0:
        raise ValueError("so_ngay phải lớn hơn 0")

    moc = datetime.now(tz=timezone.utc) - timedelta(days=so_ngay)
    cua_so = [
        b
        for b in ds_bai
        if _chuan_hoa_utc(b.thoi_gian_xuat_ban) >= moc
    ]

    tong = len(cua_so)
    if tong == 0:
        return BaoCaoDanhGiaPipeline(
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            window_days=so_ngay,
            total_articles=0,
            unique_sources=0,
            coverage={
                "has_content_ratio": 0.0,
                "has_summary_ratio": 0.0,
                "has_sentiment_ratio": 0.0,
                "has_tickers_ratio": 0.0,
                "has_vector_ratio": 0.0,
            },
            sentiment_distribution={"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0},
            sentiment_average=0.0,
            impact_distribution={"LOW": 0, "MEDIUM": 0, "HIGH": 0},
            high_impact_ratio=0.0,
            avg_original_length=0.0,
            avg_summary_length=0.0,
        )

    so_co_noi_dung = sum(1 for b in cua_so if bool(b.noi_dung_goc.strip()))
    so_co_tom_tat = sum(1 for b in cua_so if bool(b.noi_dung_tom_tat.strip()))
    so_co_sentiment = sum(1 for b in cua_so if abs(float(b.diem_cam_xuc)) > 0.0)
    so_co_ticker = sum(1 for b in cua_so if len(b.ma_chung_khoan_lien_quan) > 0)
    so_co_vector = sum(1 for b in cua_so if b.vector_id is not None and b.vector_id != "")

    sentiment_dist = _dem_phan_bo_sentiment(cua_so)
    impact_dist = _dem_phan_bo_impact(cua_so)

    sentiment_tb = _lam_tron(sum(float(b.diem_cam_xuc) for b in cua_so) / tong)
    high_impact = sum(1 for b in cua_so if b.is_high_impact)

    do_dai_goc_tb = _lam_tron(sum(len(b.noi_dung_goc or "") for b in cua_so) / tong, 2)
    do_dai_tom_tat_tb = _lam_tron(sum(len(b.noi_dung_tom_tat or "") for b in cua_so) / tong, 2)

    return BaoCaoDanhGiaPipeline(
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        window_days=so_ngay,
        total_articles=tong,
        unique_sources=len({b.nguon_tin for b in cua_so}),
        coverage={
            "has_content_ratio": _lam_tron(so_co_noi_dung / tong),
            "has_summary_ratio": _lam_tron(so_co_tom_tat / tong),
            "has_sentiment_ratio": _lam_tron(so_co_sentiment / tong),
            "has_tickers_ratio": _lam_tron(so_co_ticker / tong),
            "has_vector_ratio": _lam_tron(so_co_vector / tong),
        },
        sentiment_distribution=sentiment_dist,
        sentiment_average=sentiment_tb,
        impact_distribution=impact_dist,
        high_impact_ratio=_lam_tron(high_impact / tong),
        avg_original_length=do_dai_goc_tb,
        avg_summary_length=do_dai_tom_tat_tb,
    )
