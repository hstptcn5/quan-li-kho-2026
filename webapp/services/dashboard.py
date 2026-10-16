# -*- coding: utf-8 -*-
"""Dữ liệu màn hình Tổng quan: logic thuần, không phụ thuộc Tkinter hay HTTP.

``build_dashboard_snapshot`` được chuyển nguyên văn từ ``ui_dashboard.py`` để
bản Tkinter và bản web dùng chung một cách phân loại cảnh báo.
"""

from __future__ import annotations

import datetime as dt


LOW_STOCK_THRESHOLD = 10.0
WARNING_DAYS = 90
DEFAULT_LIMIT = 80
MAX_LIMIT = 500
ACTIVITY_LIMIT = 10
VALID_FILTERS = ("all", "expired", "near", "low")


def _parse_iso_date(value):
    if not value:
        return None
    try:
        return dt.datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def build_dashboard_snapshot(inventory_rows, *, today=None, warning_days=WARNING_DAYS):
    """Build a deterministic display model from current fund-separated stock.

    This helper performs no writes and deliberately keeps fund source visible.
    One warning row represents one product/batch/fund balance, while active-lot
    counts de-duplicate fund splits for the same physical lot.
    """
    today = today or dt.date.today()
    warning_until = today + dt.timedelta(days=int(warning_days))

    positive_rows = []
    active_lots = set()
    near_lots = set()
    expired_lots = set()
    low_keys = set()
    warning_rows = []

    for raw in inventory_rows or []:
        row = dict(raw)
        stock = float(row.get("stockBase") or 0)
        if stock <= 0:
            continue

        product_id = row.get("productId")
        batch_id = row.get("batchId")
        fund = row.get("fundSource") or ""
        lot_key = (product_id, batch_id)
        fund_key = (product_id, batch_id, fund)
        expiry = _parse_iso_date(row.get("expiryDate"))

        active_lots.add(lot_key)
        positive_rows.append(row)

        status = None
        severity = 99
        days_left = None
        if expiry is not None:
            days_left = (expiry - today).days
            if expiry < today:
                status = "Đã hết hạn"
                severity = 0
                expired_lots.add(lot_key)
            elif expiry == today:
                status = "Hết hạn hôm nay"
                severity = 1
                near_lots.add(lot_key)
            elif expiry <= warning_until:
                status = f"Cận hạn {days_left} ngày"
                severity = 2
                near_lots.add(lot_key)

        if stock <= LOW_STOCK_THRESHOLD:
            low_keys.add(fund_key)
            if status is None:
                status = "Tồn thấp ≤10"
                severity = 3

        if status is not None:
            warning_rows.append({
                "productId": product_id,
                "batchId": batch_id,
                "productName": row.get("productName") or "",
                "lotNo": row.get("lotNo") or "",
                "expiryDate": row.get("expiryDate") or "",
                "fundSource": fund,
                "stockBase": stock,
                "status": status,
                "severity": severity,
                "daysLeft": days_left,
            })

    warning_rows.sort(
        key=lambda item: (
            item["severity"],
            _parse_iso_date(item.get("expiryDate")) or dt.date.max,
            str(item.get("productName") or "").lower(),
            str(item.get("fundSource") or "").lower(),
        )
    )

    return {
        "active_lot_count": len(active_lots),
        "near_expiry_count": len(near_lots),
        "expired_count": len(expired_lots),
        "low_stock_count": len(low_keys),
        "warning_rows": warning_rows,
        "positive_rows": positive_rows,
    }


def warning_category(severity):
    """Nhóm của chip lọc: expired (severity <= 1), near (2), low (còn lại)."""
    severity = int(severity)
    if severity <= 1:
        return "expired"
    if severity == 2:
        return "near"
    return "low"


def validate_dashboard_params(flt, limit):
    """Kiểm tra tham số trước khi chạm DB; ném ValueError với thông báo tiếng Việt."""
    if flt not in VALID_FILTERS:
        raise ValueError("Tham số filter không hợp lệ")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"Tham số limit phải là số nguyên từ 1 đến {MAX_LIMIT}")


def build_dashboard_payload(db, *, flt="all", limit=DEFAULT_LIMIT, today=None):
    """Dựng dữ liệu JSON của /api/dashboard (chưa có khóa ``success``)."""
    validate_dashboard_params(flt, limit)

    summary = db.dashboard_summary(WARNING_DAYS)
    snapshot = build_dashboard_snapshot(db.get_inventory(), today=today, warning_days=WARNING_DAYS)

    all_rows = snapshot["warning_rows"]
    counts = {"all": len(all_rows), "expired": 0, "near": 0, "low": 0}
    for row in all_rows:
        counts[warning_category(row["severity"])] += 1
    if flt == "all":
        selected = all_rows
    else:
        selected = [row for row in all_rows if warning_category(row["severity"]) == flt]

    activities = [
        {
            "timestamp": row.get("timestamp") or "",
            "action": row.get("action") or "",
            "details": row.get("details") or "",
        }
        for row in db.q(
            "SELECT timestamp, action, details FROM audit_logs "
            "ORDER BY datetime(timestamp) DESC, id DESC LIMIT ?",
            (ACTIVITY_LIMIT,),
        )
    ]

    latest = db.q(
        "SELECT logDate, session, locationName, temperature, humidity, recordedBy "
        "FROM temperature_logs ORDER BY DATE(logDate) DESC, id DESC LIMIT 1"
    )
    latest_temperature = None
    if latest:
        row = latest[0]
        humidity = row.get("humidity")
        latest_temperature = {
            "logDate": row.get("logDate") or "",
            "session": row.get("session") or "",
            "locationName": row.get("locationName") or "",
            "temperature": float(row.get("temperature") or 0),
            "humidity": None if humidity is None else float(humidity),
            "recordedBy": row.get("recordedBy") or "",
        }

    return {
        "warningDays": WARNING_DAYS,
        "lowStockThreshold": LOW_STOCK_THRESHOLD,
        "cards": {
            "productCount": int(summary.get("product_count") or 0),
            "activeLotCount": snapshot["active_lot_count"],
            "nearExpiryCount": snapshot["near_expiry_count"],
            "expiredCount": snapshot["expired_count"],
            "lowStockCount": snapshot["low_stock_count"],
        },
        "warnings": {"counts": counts, "rows": selected[:limit]},
        "activities": activities,
        "runtime": {
            "lastBackup": summary.get("last_backup"),
            "latestTemperature": latest_temperature,
            # Khác bản Tkinter có chủ ý: đếm thật thay vì đếm trên danh sách tồn dương.
            "negativeStockRows": int(summary.get("negative_count") or 0),
        },
    }
