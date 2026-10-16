# -*- coding: utf-8 -*-
"""Smoke test chạy trong cửa sổ pywebview thật (``quanly_web.py --smoke``).

Chạy qua ``release_web_smoke_check.py`` với DB tạm. Biến môi trường
``QLK_SMOKE_EXPECT`` (JSON ``{"counts": {...}, "literal": "..."}``) bật phần kiểm tra
chip lọc và hiển thị an toàn; không có biến này chỉ kiểm tra nền (hiển thị, không lỗi).
"""

from __future__ import annotations

import json
import os
import time

TIMEOUT_SECONDS = 30.0
POLL_SECONDS = 0.25

STATE = (
    "(function () {"
    " var table = document.querySelector('[data-testid=\"warning-table\"]');"
    " var chips = Array.prototype.slice.call(document.querySelectorAll('[data-testid^=\"chip-\"]'));"
    " var rows = table ? Array.prototype.slice.call(table.querySelectorAll('tbody tr')) : [];"
    " return JSON.stringify({"
    "  ready: !!document.querySelector('[data-testid=\"dashboard-ready\"]'),"
    "  error: !!document.querySelector('[data-testid=\"dashboard-error\"]'),"
    "  title: (document.querySelector('.page-head__title') || {}).textContent || '',"
    "  activeNav: (document.querySelector('a.nav--active') || {}).textContent || '',"
    "  chipLabels: chips.map(function (b) { return b.textContent.trim(); }),"
    "  pressed: chips.filter(function (b) { return b.getAttribute('aria-pressed') === 'true'; })"
    "    .map(function (b) { return b.getAttribute('data-testid').replace('chip-', ''); }),"
    "  severities: rows.map(function (r) { return r.getAttribute('data-severity'); }),"
    "  tableText: table ? table.textContent : '',"
    "  boldCount: table ? table.querySelectorAll('b').length : 0,"
    "  diagnostics: window.__qlk || null"
    " });"
    "})()"
)
RAPID_CLICKS = (
    "['expired', 'near', 'low'].forEach(function (name) {"
    " document.querySelector('[data-testid=\"chip-' + name + '\"]').click(); }); true"
)
OPEN_UNAVAILABLE_ROUTE = "window.location.hash = '#/products'; true"


def click_script(name):
    return f"document.querySelector('[data-testid=\"chip-{name}\"]').click(); true"


class SmokeFailure(AssertionError):
    """Một kiểm tra của smoke test không đạt."""


def _load_expectation():
    raw = os.environ.get("QLK_SMOKE_EXPECT")
    return json.loads(raw) if raw else None


def _eval(window, script):
    try:
        return window.evaluate_js(script)
    except Exception:
        return None


def _state(window):
    raw = _eval(window, STATE)
    try:
        return json.loads(raw) if raw else None
    except (TypeError, ValueError):
        return None


def _wait_state(window, predicate, what):
    deadline = time.time() + TIMEOUT_SECONDS
    last = None
    while time.time() < deadline:
        last = _state(window)
        if last is not None and predicate(last):
            return last
        time.sleep(POLL_SECONDS)
    raise SmokeFailure(
        f"Quá thời gian chờ: {what}. Trạng thái cuối: {json.dumps(last, ensure_ascii=False)[:600]}"
    )


def _expect(condition, message):
    if not condition:
        raise SmokeFailure(message)


def _expect_clean(state):
    diagnostics = state.get("diagnostics") or {}
    _expect(diagnostics.get("cspViolations") == [], f"Vi phạm CSP: {diagnostics.get('cspViolations')}")
    _expect(diagnostics.get("errors") == [], f"Lỗi JavaScript: {diagnostics.get('errors')}")


def _filter_scenarios(window, counts):
    for name, allowed in (("expired", ("0", "1")), ("near", ("2",)), ("low", ("3",))):
        _eval(window, click_script(name))
        state = _wait_state(
            window, lambda s, n=name: s["ready"] and s["pressed"] == [n], f"chip {name} được chọn và tải xong"
        )
        _expect(
            len(state["severities"]) == counts[name],
            f"Chip {name}: {len(state['severities'])} dòng, kỳ vọng {counts[name]}",
        )
        _expect(
            all(severity in allowed for severity in state["severities"]),
            f"Chip {name} có dòng thuộc nhóm khác: {state['severities']}",
        )

    # Bấm 3 chip trong cùng một nhịp: kết quả cuối phải khớp chip cuối cùng (low).
    _eval(window, RAPID_CLICKS)
    _wait_state(window, lambda s: s["ready"] and s["pressed"] == ["low"], "chip cuối (low) sau khi bấm nhanh")
    time.sleep(1.0)  # để các phản hồi muộn (nếu có) kịp đến và thử ghi đè
    state = _state(window)
    _expect(
        state is not None and state["pressed"] == ["low"] and state["severities"] == ["3"] * counts["low"],
        f"Sau khi bấm nhanh, bảng không khớp chip cuối cùng: {state}",
    )

    _eval(window, click_script("all"))
    state = _wait_state(window, lambda s: s["ready"] and s["pressed"] == ["all"], "chip Tất cả")
    _expect(len(state["severities"]) == counts["all"], f"Chip Tất cả: {len(state['severities'])} dòng")


def _run(window, expect):
    state = _wait_state(window, lambda s: s["ready"], "màn hình Tổng quan sẵn sàng")
    _expect(not state["error"], "Tổng quan hiện trạng thái lỗi")
    _expect("Tổng quan vận hành kho" in state["title"], f"Tiêu đề không đúng: {state['title']!r}")
    _expect_clean(state)

    if expect:
        counts = expect["counts"]
        labels = [
            f"Tất cả {counts['all']}", f"Hết hạn {counts['expired']}",
            f"Cận hạn {counts['near']}", f"Tồn thấp {counts['low']}",
        ]
        _expect(state["chipLabels"] == labels, f"Nhãn chip {state['chipLabels']} khác kỳ vọng {labels}")
        literal = expect.get("literal")
        if literal:
            _expect(literal in state["tableText"], f"Bảng không hiện nguyên văn {literal!r}")
            _expect(state["boldCount"] == 0, "Bảng có thẻ <b>: văn bản bị hiểu thành HTML")
        if counts["all"] > 0:
            _filter_scenarios(window, counts)

    _eval(window, OPEN_UNAVAILABLE_ROUTE)
    time.sleep(0.5)
    state = _wait_state(window, lambda s: s["ready"], "Tổng quan còn sau khi mở #/products")
    _expect("Tổng quan" in state["activeNav"], "Mục điều hướng đang chọn không còn là Tổng quan")
    _expect_clean(state)


def run_smoke(window) -> int:
    try:
        _run(window, _load_expectation())
    except SmokeFailure as exc:
        print(f"WEB_SMOKE_FAIL: {exc}", flush=True)
        return 1
    print("WEB_SMOKE_OK", flush=True)
    return 0
