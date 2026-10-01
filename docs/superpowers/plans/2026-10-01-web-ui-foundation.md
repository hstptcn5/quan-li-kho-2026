# Giao diện web: nền tảng (P1) — Kế hoạch triển khai

> **Dành cho người thực thi (agent):** BẮT BUỘC dùng `superpowers:subagent-driven-development` (khuyến nghị) hoặc `superpowers:executing-plans` để thực hiện kế hoạch này theo từng task. Các bước dùng cú pháp checkbox (`- [ ]`) để theo dõi.

**Mục tiêu:** Dựng nền tảng giao diện web dùng chung (thư mục `web/`, backend `webapp/`, điểm vào `quanly_web.py`) và đưa màn hình **Tổng quan** (bố cục B, chỉ đọc) đi qua toàn bộ chuỗi API → bảo mật → cửa sổ pywebview → đóng gói `.exe` → smoke test trong CI.

**Kiến trúc:** Một backend Python thuần thư viện chuẩn, router có `scope` (`local`|`lan`), listener `127.0.0.1` cổng ngẫu nhiên xác thực bằng boot token dùng một lần rồi cookie `HttpOnly`. Giao diện là HTML/CSS/ES modules + Preact+htm đặt sẵn trong repo, không build, không Node. Bản Tkinter (`quanly_xnt.py`) giữ nguyên và dùng chung `pharm.db`.

**Công nghệ:** Python 3.10 (CI), `pywebview` (Edge WebView2), Preact+htm (`htm@3.1.1/preact/standalone.module.js`), PyInstaller (đã có), `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-01-web-ui-foundation-design.md` (mockup tham chiếu: `docs/superpowers/specs/2026-10-01-dashboard-layout-b-mockup.html`). Người thực thi đọc cả hai trước khi bắt đầu.

## Ràng buộc chung

Mọi task đều phải thỏa các điều sau (giá trị chép nguyên văn từ spec):

- Python 3.10 là phiên bản được CI kiểm thử; backend `webapp/` chỉ dùng thư viện chuẩn. Phụ thuộc mới duy nhất là `pywebview` (ghim phiên bản).
- Giao diện: Preact+htm đặt sẵn trong `web/js/vendor/`, **không build, không Node, chạy offline**, không tải font hay thư viện từ mạng lúc chạy.
- Listener cục bộ: bind `127.0.0.1`, cổng 0 (hệ điều hành cấp); `Host` chỉ chấp nhận `127.0.0.1:<port>` hoặc `localhost:<port>`; request không phải GET/HEAD phải cùng origin; cookie phiên `HttpOnly; SameSite=Strict; Path=/`.
- Header bảo mật cố định: `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`; `Cache-Control: no-store` cho API, `no-cache` cho file tĩnh.
- Trần body 1 MiB; mỗi request tự mở và đóng kết nối SQLite riêng (quy tắc H3.1); P1 **chỉ đọc DB**, không có endpoint ghi.
- Mỗi route khai báo `scope`; route `local` bị từ chối (403) khi yêu cầu đến từ listener `lan`.
- API `/api/dashboard`: `filter` ∈ `all|expired|near|low` (mặc định `all`); `limit` mặc định 80, tối đa 500, áp dụng **sau** khi lọc; tham số sai trả 400.
- Ngày hiển thị `DD-MM-YYYY`; chuỗi động đi qua Preact (tự escape): **cấm** `innerHTML`, `eval`, `new Function`, thuộc tính `on*=`, `<script>`/`<style>` inline và `style="..."` trong `web/`.
- Token màu chuyển 1:1 từ `ui_design.py`, **ngoại lệ duy nhất** `--text-muted: #5F6F85`; mọi cặp chữ/nền phải đạt WCAG AA (≥ 4,5:1).
- Hành vi bản Tkinter và `server.py` không đổi; toàn bộ test cũ phải xanh sau mỗi task.
- Mọi lệnh chạy bằng `py -3.10` và đặt `PYTHONIOENCODING=utf-8`. `config.py` tạo thư mục dữ liệu ngay khi import, nên **luôn** đặt `LOCALAPPDATA` sang thư mục tạm khi chạy test hoặc app thử, để không chạm DB thật:

  ```bash
  export PYTHONIOENCODING=utf-8
  mkdir -p "$TEMP/qlk_plan_appdata"
  export LOCALAPPDATA="$(cygpath -w "$TEMP/qlk_plan_appdata")"
  ```
- Commit: không bao giờ `git add -A`; chỉ add đúng file của task (đặc biệt không add `opencode.json`). Thông điệp commit kết thúc bằng dòng `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Không push, không tạo PR khi chưa được chủ dự án đồng ý.

## Review Focus

Năm tình huống mà spec ngụ ý nhưng ít task nào kiểm tra trực tiếp, dễ gây lỗi cho người dùng nhất (mỗi dòng có test gắn vào task sở hữu code):

1. **DB đang bị khóa hoặc lỗi khi mở Tổng quan** (bản Tkinter đang ghi): người dùng mong thấy thông báo lỗi chung kèm nút "Thử lại", không lộ đường dẫn hay nội dung lỗi nội bộ. → Task 8 (`test_database_error_is_reported_without_internal_details`), Task 11 (`ErrorState`).
2. **Cài mới, DB trống:** Tổng quan hiện số 0 và trạng thái trống, không báo lỗi. → Task 3 (`test_empty_database_gives_zero_cards`), Task 12 (smoke chạy cả với DB trống).
3. **Tên thuốc, số lô, nguồn kinh phí chứa ký tự đặc biệt** (`<b>`, dấu nháy, `&`, chuỗi rất dài): hiện đúng như chữ, không thành thẻ HTML. → Task 3 (`test_hostile_text_is_returned_verbatim`), Task 8 (round trip JSON), Task 10 (cấm `innerHTML`), Task 12 (smoke kiểm tra DOM).
4. **Tham số truy vấn và header bất thường** (`filter=bogus`, `limit=0/501/abc`, `Content-Length` âm hoặc quá lớn, `Transfer-Encoding: chunked`, `Host` lạ): bị từ chối rõ ràng bằng 400/403/413, không treo, không 500. → Task 3, Task 7, Task 8.
5. **Bấm chip lọc liên tiếp nhanh, hoặc mở `#/products` chưa có bản web:** màn hình cuối cùng khớp chip được chọn sau cùng (không bị phản hồi cũ ghi đè), địa chỉ chưa có bản web vẫn giữ Tổng quan. → Task 11 (code `requestId`), Task 12 (smoke bấm 3 chip trong một lượt rồi kiểm tra).

## Bản đồ file

| File | Trách nhiệm | Task |
|---|---|---|
| `http_limits.py` (mới) | Giới hạn framing HTTP dùng chung (trần body, timeout, kiểm header), tách khỏi `mobile_http_hardening.py` để backend mới không phải import `server.py` | 2 |
| `webapp/__init__.py`, `webapp/services/__init__.py`, `webapp/api/__init__.py` (mới) | Gói backend | 3, 8 |
| `webapp/services/dashboard.py` (mới) | `build_dashboard_snapshot` (chuyển từ `ui_dashboard.py`) và `build_dashboard_payload` | 3 |
| `webapp/routing.py` (mới) | `Router`, `Request`, `Response`, `HttpError`, `json_response`, scope | 4 |
| `webapp/security.py` (mới) | Header bảo mật, kiểm `Host`/`Origin` | 5 |
| `webapp/auth.py` (mới) | `LocalSession`: boot token dùng một lần, cookie phiên | 5 |
| `webapp/static.py` (mới) | Phục vụ `web/` an toàn | 6 |
| `webapp/listener.py` (mới) | `LocalListener` (ThreadingHTTPServer loopback) | 7 |
| `webapp_testkit.py` (mới, không phải test) | Harness HTTP dùng chung cho test | 7 |
| `webapp/api/dashboard.py`, `webapp/app.py` (mới) | Endpoint `/api/dashboard`, `build_router` | 8 |
| `webapp/runtime.py` (mới) | `app_root()`, `webview2_runtime_version()` | 9 |
| `quanly_web.py`, `run_web.bat` (mới) | Điểm vào: cửa sổ pywebview, `--serve`, `--smoke` | 9, 12 |
| `web/css/*.css`, `web/js/{format,api,nav}.js`, `web/js/vendor/*` (mới) | Token thiết kế, CSS nền, tiện ích JS, thư viện đặt sẵn | 10 |
| `web/js/components/*.js`, `web/js/views/dashboard.js`, `web/js/app.js`, `web/index.html` (mới) | Component, màn hình Tổng quan, khởi động | 11 |
| `webapp/smoke.py`, `scripts/web_smoke_seed.py`, `release_web_smoke_check.py` (mới) | Smoke test trong cửa sổ, DB mẫu, trình chạy smoke (nguồn và đóng gói) | 12, 13 |
| `build_web_release.py` (mới) | Build `dist/QuanLyKhoWeb/` | 13 |
| `requirements.txt`, `.github/workflows/tests.yml`, `README.md`, `.gitignore` (sửa) | Phụ thuộc, CI, tài liệu | 9, 14 |
| `test_http_limits.py`, `test_webapp_dashboard.py`, `test_webapp_routing.py`, `test_webapp_local_auth.py`, `test_webapp_static.py`, `test_webapp_listener.py`, `test_webapp_runtime.py`, `test_quanly_web.py`, `test_web_assets_policy.py` (mới) | Test theo mục 9 của spec (phần listener tách thành `test_webapp_listener.py`) | 2–13 |

---

### Task 0: Chuẩn bị nhánh

**Files:** không có file mã nguồn.

- [ ] **Step 1: Xác nhận đang đứng trên nhánh spec và cây làm việc sạch**

Run: `git switch web-ui/p1-foundation-spec && git status --short`
Expected: chỉ còn `?? opencode.json` (và có thể có thay đổi chưa commit của chính kế hoạch/spec này).

- [ ] **Step 2: Tạo nhánh triển khai**

Run: `git switch -c web-ui/p1-foundation`
Expected: `Switched to a new branch 'web-ui/p1-foundation'`. Toàn bộ task sau commit trên nhánh này.

---

### Task 1: Spike đóng gói pywebview (mã bỏ đi) và cổng quyết định

Mục đích: xác nhận trước khi viết gì khác rằng pywebview + WebView2 chạy được **sau khi đóng gói bằng PyInstaller** và trên runner CI. Mã spike là **bỏ đi**, không commit; chỉ commit ghi chú kết quả.

**Files:**
- Tạo (ngoài repo, bỏ đi): `$TEMP/qlk_spike/webview_hello.py`
- Tạo (commit): `docs/superpowers/plans/2026-10-01-web-ui-p1-spike-result.md`

**Interfaces:**
- Consumes: không có.
- Produces: phiên bản `pywebview` đã kiểm chứng (dùng ở Task 9 để ghim trong `requirements.txt`); xác nhận chữ ký `webview.create_window(...)`, `webview.start(func, args, gui="edgechromium", private_mode=True, debug=False)`, `window.evaluate_js(...)`, `window.destroy()` hoạt động; quyết định "tiếp tục với pywebview" hoặc "dừng và đổi phương án".

- [ ] **Step 1: Dựng môi trường riêng và cài thư viện**

```bash
mkdir -p "$TEMP/qlk_spike" && cd "$TEMP/qlk_spike"
py -3.10 -m venv venv
./venv/Scripts/python.exe -m pip install --upgrade pip
./venv/Scripts/python.exe -m pip install pywebview pyinstaller pip-audit
./venv/Scripts/python.exe -m pip show pywebview | grep -E "^(Name|Version)"
./venv/Scripts/python.exe -m pip list | grep -iE "pythonnet|clr|proxy|bottle|typing"
./venv/Scripts/python.exe -m pip_audit --progress-spinner off
```

Expected: in ra phiên bản `pywebview` (ghi lại, ví dụ `Version: X.Y.Z`) và phiên bản các phụ thuộc Windows (`pythonnet`, `clr_loader`…). `pip_audit` cuối cùng nên báo `No known vulnerabilities found`. Nếu báo lỗ hổng ở `pywebview` hoặc phụ thuộc trực tiếp, ghi lại và thử phiên bản khác (`pip install "pywebview==<phiên bản khác>"`) trước khi đi tiếp.

- [ ] **Step 2: Viết mã spike**

Tạo `$TEMP/qlk_spike/webview_hello.py` (đại diện đúng cách app thật sẽ dùng: máy chủ loopback, trang module script dưới CSP chặt, `evaluate_js`, `destroy`):

```python
import argparse
import http.server
import sys
import threading
import time

import webview

PAGE = (
    b"<!doctype html><meta charset=utf-8><title>spike</title>"
    b"<div id=ok>hello</div><script type=module src=/ok.js></script>"
)
SCRIPT = b"document.getElementById('ok').dataset.ready = '1';"


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ok.js":
            body, ctype = SCRIPT, "text/javascript; charset=utf-8"
        else:
            body, ctype = PAGE, "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.parse_args()

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/"

    result = {"ok": False}
    window = webview.create_window("spike", url, width=900, height=600, min_size=(640, 480))

    def probe(win):
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                if win.evaluate_js("document.getElementById('ok').dataset.ready") == "1":
                    result["ok"] = True
                    break
            except Exception:
                pass
            time.sleep(0.5)
        win.destroy()

    webview.start(probe, window, gui="edgechromium", private_mode=True, debug=False)
    httpd.shutdown()
    print("SPIKE_OK" if result["ok"] else "SPIKE_FAIL")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Chạy từ mã nguồn**

Run: `cd "$TEMP/qlk_spike" && ./venv/Scripts/python.exe webview_hello.py --smoke; echo "exit=$?"`
Expected: một cửa sổ nhỏ mở rồi tự đóng sau vài giây; in `SPIKE_OK` và `exit=0`.
Nếu `SPIKE_FAIL` hoặc lỗi: ghi nguyên văn lỗi vào ghi chú kết quả (Step 6) và đi tới Step 7 (cổng quyết định) với kết luận FAIL.

- [ ] **Step 4: Đóng gói bằng PyInstaller và chạy bản đóng gói**

```bash
cd "$TEMP/qlk_spike"
./venv/Scripts/python.exe -m PyInstaller --noconfirm --clean --onedir --console --name spike_webview webview_hello.py
./dist/spike_webview/spike_webview.exe --smoke; echo "exit=$?"
```

Expected: `SPIKE_OK` và `exit=0`. Nếu bản đóng gói thiếu module (lỗi dạng `ModuleNotFoundError`, `clr`, hoặc `Python.Runtime`), thử lại một lần với các cờ này rồi ghi lại cờ nào cần thiết:

```bash
./venv/Scripts/python.exe -m PyInstaller --noconfirm --clean --onedir --console --name spike_webview \
  --collect-all webview --collect-all clr_loader --hidden-import clr webview_hello.py
```

- [ ] **Step 5: Chạy trên runner CI (cần chủ dự án đồng ý push một nhánh tạm)**

Hỏi chủ dự án trước khi push. Nếu được đồng ý, tạo nhánh tạm `spike/webview-ci` từ `main` (không từ nhánh triển khai), thêm `spike/webview_hello.py` (bản ở Step 2) và `.github/workflows/spike-webview.yml`:

```yaml
name: Spike webview
on:
  push:
    branches: [spike/webview-ci]
jobs:
  spike:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - name: Ensure WebView2 runtime
        shell: pwsh
        run: |
          $key = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
          if (Test-Path $key) { "WebView2 runtime present: $((Get-ItemProperty $key).pv)"; exit 0 }
          Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile "$env:RUNNER_TEMP\MicrosoftEdgeWebview2Setup.exe"
          Start-Process -FilePath "$env:RUNNER_TEMP\MicrosoftEdgeWebview2Setup.exe" -ArgumentList '/silent','/install' -Wait
          if (-not (Test-Path $key)) { throw 'WebView2 runtime installation failed' }
      - run: python -m pip install pywebview pyinstaller
      - run: python -m PyInstaller --noconfirm --clean --onedir --console --name spike_webview spike/webview_hello.py
      - name: Run packaged spike
        run: ./dist/spike_webview/spike_webview.exe --smoke
```

Sau khi lần chạy kết thúc, đọc kết quả: `gh run list --branch spike/webview-ci --limit 1` rồi `gh run view <id> --log | tail -40`. Expected: bước "Run packaged spike" in `SPIKE_OK`. Ghi lại: runner có sẵn WebView2 hay phải cài ở bước "Ensure WebView2 runtime". Xóa nhánh tạm sau khi xong: `git push origin --delete spike/webview-ci`.

Nếu chủ dự án không đồng ý push, ghi "CI: chưa kiểm chứng" vào ghi chú và báo rõ ở Step 7.

- [ ] **Step 6: Ghi chú kết quả**

Tạo `docs/superpowers/plans/2026-10-01-web-ui-p1-spike-result.md` với số liệu thật đã đo (không để trống):

```markdown
# Kết quả spike pywebview (P1)

Ngày chạy: <YYYY-MM-DD>

| Hạng mục | Kết quả |
|---|---|
| Phiên bản pywebview | <phiên bản từ Step 1> |
| Phiên bản pythonnet / clr_loader | <từ Step 1> |
| pip-audit | <No known vulnerabilities found / liệt kê lỗ hổng> |
| Chạy từ mã nguồn (Step 3) | <SPIKE_OK / SPIKE_FAIL + lỗi> |
| Chạy bản PyInstaller (Step 4) | <SPIKE_OK / SPIKE_FAIL + cờ bổ sung cần dùng nếu có> |
| Chạy trên runner CI (Step 5) | <SPIKE_OK / SPIKE_FAIL / chưa kiểm chứng> |
| Runner có sẵn WebView2 | <có / không, phải cài> |

**Quyết định:** <TIẾP TỤC với pywebview / DỪNG: chuyển phương án Edge --app>
```

- [ ] **Step 7: Cổng quyết định**

- Nếu Step 3 và Step 4 đều `SPIKE_OK` (và Step 5 `SPIKE_OK` hoặc được chủ dự án chấp nhận "chưa kiểm chứng"): tiếp tục Task 2.
- Nếu Step 3 hoặc Step 4 thất bại, hoặc Step 5 thất bại: **DỪNG**, báo cáo cho chủ dự án kèm ghi chú kết quả, và đề nghị chuyển sang phương án dự phòng trong spec (mục 10): chế độ `msedge --app=<URL>` với hồ sơ tạm riêng. Phương án này chỉ thay hàm `run_window` ở Task 9; các task còn lại giữ nguyên. Không tự ý đổi phương án khi chưa có đồng ý.

- [ ] **Step 8: Commit ghi chú kết quả**

```bash
git add docs/superpowers/plans/2026-10-01-web-ui-p1-spike-result.md
git commit -F - <<'EOF'
Record pywebview packaging spike result

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 2: Tách giới hạn HTTP dùng chung (`http_limits.py`)

Lý do: backend mới cần `validate_request_body_headers` nhưng import `mobile_http_hardening` sẽ kéo theo `server.py` cũ (và `mobile_templates`, `reportlab`…). Tách ra module nhẹ, `mobile_http_hardening` import lại để mọi tên cũ vẫn dùng được.

**Files:**
- Tạo: `http_limits.py`
- Sửa: `mobile_http_hardening.py` (xóa 3 khối, thêm 1 import)
- Test: `test_http_limits.py`

**Interfaces:**
- Consumes: không có.
- Produces (dùng ở Task 7): `http_limits.MAX_REQUEST_BODY_BYTES: int`, `http_limits.REQUEST_SOCKET_TIMEOUT_SECONDS: float`, `http_limits.REQUEST_QUEUE_SIZE: int`, `http_limits.RequestBodyPolicyError(status_code: int, message: str)` (thuộc tính `.status_code`, `.message`), `http_limits.validate_request_body_headers(headers) -> int`.

- [ ] **Step 1: Viết test thất bại**

Tạo `test_http_limits.py`:

```python
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import unittest

import http_limits
import mobile_http_hardening as hardening

ROOT = os.path.dirname(os.path.abspath(__file__))


class HttpLimitsTests(unittest.TestCase):
    def test_module_loads_without_pulling_in_the_legacy_server(self):
        code = (
            "import sys, http_limits; "
            "bad = [m for m in ('server', 'config', 'database', 'mobile_templates') if m in sys.modules]; "
            "assert not bad, bad"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mobile_hardening_reexports_the_same_objects(self):
        for name in (
            "MAX_REQUEST_BODY_BYTES",
            "REQUEST_SOCKET_TIMEOUT_SECONDS",
            "REQUEST_QUEUE_SIZE",
            "RequestBodyPolicyError",
            "validate_request_body_headers",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(hardening, name), getattr(http_limits, name))

    def test_validation_behaviour_is_unchanged(self):
        self.assertEqual(http_limits.validate_request_body_headers({}), 0)
        self.assertEqual(
            http_limits.validate_request_body_headers({"Content-Length": " 128 "}), 128
        )
        for headers, status in (
            ({"Content-Length": "abc"}, 400),
            ({"Content-Length": "-1"}, 400),
            ({"Content-Length": str(http_limits.MAX_REQUEST_BODY_BYTES + 1)}, 413),
            ({"Transfer-Encoding": "chunked"}, 400),
        ):
            with self.subTest(headers=headers):
                with self.assertRaises(http_limits.RequestBodyPolicyError) as ctx:
                    http_limits.validate_request_body_headers(headers)
                self.assertEqual(ctx.exception.status_code, status)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_http_limits -v`
Expected: lỗi `ModuleNotFoundError: No module named 'http_limits'` (cả file không import được).

- [ ] **Step 3: Tạo `http_limits.py`**

```python
# -*- coding: utf-8 -*-
"""Giới hạn framing HTTP dùng chung cho server di động (LAN) và backend web cục bộ.

Module này cố ý không import code ứng dụng, để backend mới dùng được mà không
phải nạp ``server.py`` cũ.
"""

from __future__ import annotations


MAX_REQUEST_BODY_BYTES = 1024 * 1024
REQUEST_SOCKET_TIMEOUT_SECONDS = 15.0
REQUEST_QUEUE_SIZE = 32


class RequestBodyPolicyError(ValueError):
    """Raised when request framing violates the bounded POST-body policy."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = int(status_code)
        self.message = str(message)


def validate_request_body_headers(headers) -> int:
    """Return a safe Content-Length or raise ``RequestBodyPolicyError``.

    The legacy request handlers understand fixed-length JSON bodies only. An
    unsupported Transfer-Encoding is therefore rejected instead of being
    ambiguously interpreted as an empty or partial request.
    """
    transfer_encoding = str(headers.get("Transfer-Encoding", "") or "").strip().lower()
    if transfer_encoding and transfer_encoding != "identity":
        raise RequestBodyPolicyError(
            400,
            "Transfer-Encoding không được hỗ trợ; vui lòng gửi Content-Length cố định",
        )

    raw_length = headers.get("Content-Length")
    if raw_length in (None, ""):
        return 0

    try:
        content_length = int(str(raw_length).strip())
    except (TypeError, ValueError):
        raise RequestBodyPolicyError(400, "Content-Length không hợp lệ")

    if content_length < 0:
        raise RequestBodyPolicyError(400, "Content-Length không được âm")
    if content_length > MAX_REQUEST_BODY_BYTES:
        raise RequestBodyPolicyError(
            413,
            f"Dữ liệu gửi lên vượt quá giới hạn {MAX_REQUEST_BODY_BYTES // (1024 * 1024)} MiB",
        )
    return content_length
```

- [ ] **Step 4: Cho `mobile_http_hardening.py` import lại và xóa bản cũ**

Chạy script một lần để xóa 3 khối (đã neo theo tên) và thêm import:

```bash
py -3.10 - <<'EOF'
import io
path = "mobile_http_hardening.py"
s = io.open(path, encoding="utf-8").read()

consts = (
    "MAX_REQUEST_BODY_BYTES = 1024 * 1024\n"
    "REQUEST_SOCKET_TIMEOUT_SECONDS = 15.0\n"
    "REQUEST_QUEUE_SIZE = 32\n"
)
imports = (
    "from http_limits import (  # noqa: F401 (re-exported: callers use hardening.<name>)\n"
    "    MAX_REQUEST_BODY_BYTES,\n"
    "    REQUEST_QUEUE_SIZE,\n"
    "    REQUEST_SOCKET_TIMEOUT_SECONDS,\n"
    "    RequestBodyPolicyError,\n"
    "    validate_request_body_headers,\n"
    ")\n"
)
assert s.count(consts) == 1
s = s.replace(consts, imports)

a = s.index("class RequestBodyPolicyError(ValueError):")
b = s.index("def safe_server_print")
s = s[:a] + s[b:]

a = s.index("def validate_request_body_headers(headers) -> int:")
b = s.index("def configure_client_socket")
s = s[:a] + s[b:]

io.open(path, "w", encoding="utf-8", newline="\n").write(s)
print("mobile_http_hardening.py updated")
EOF
grep -nE "^class RequestBodyPolicyError|^def validate_request_body_headers|^MAX_REQUEST_BODY_BYTES" mobile_http_hardening.py || echo "old definitions removed"
```

Expected: `mobile_http_hardening.py updated` rồi `old definitions removed`.

- [ ] **Step 5: Chạy test mới và test di động liên quan**

Run: `py -3.10 -m unittest test_http_limits test_mobile_http_hardening test_mobile_thread_db_integration test_mobile_cookie_security -v 2>&1 | tail -15`
Expected: `OK` (tất cả pass, gồm 3 test mới).

- [ ] **Step 6: Commit**

```bash
git add http_limits.py mobile_http_hardening.py test_http_limits.py
git commit -F - <<'EOF'
Extract shared HTTP framing limits into http_limits

The new local web backend needs the body-size and header validation but
must not import the legacy server module. mobile_http_hardening re-exports
the same names, so existing callers and tests are unchanged.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 3: Service Tổng quan (`webapp/services/dashboard.py`)

**Files:**
- Tạo: `webapp/__init__.py`, `webapp/services/__init__.py`, `webapp/services/dashboard.py`
- Sửa: `ui_dashboard.py` (xóa định nghĩa, import lại từ service)
- Test: `test_webapp_dashboard.py` (tạo ở task này; Task 8 thêm lớp API vào cùng file)

**Interfaces:**
- Consumes: `database.DB` (`dashboard_summary(days)`, `get_inventory()`, `q(sql, params)`), `date_utils` không dùng.
- Produces (dùng ở Task 8): hằng `LOW_STOCK_THRESHOLD = 10.0`, `WARNING_DAYS = 90`, `DEFAULT_LIMIT = 80`, `MAX_LIMIT = 500`, `VALID_FILTERS = ("all","expired","near","low")`; hàm `build_dashboard_snapshot(inventory_rows, *, today=None, warning_days=WARNING_DAYS) -> dict` (giống hệt bản cũ), `warning_category(severity) -> str`, `validate_dashboard_params(flt, limit) -> None` (ném `ValueError` với thông báo tiếng Việt), `build_dashboard_payload(db, *, flt="all", limit=DEFAULT_LIMIT, today=None) -> dict` theo đúng hợp đồng JSON ở mục 6 của spec (chưa có khóa `success`).

- [ ] **Step 1: Tạo gói và chuyển hàm sang service (refactor có lưới an toàn)**

Tạo `webapp/__init__.py`:

```python
# -*- coding: utf-8 -*-
"""Backend web cục bộ cho giao diện mới (P1). Chỉ dùng thư viện chuẩn."""
```

Tạo `webapp/services/__init__.py`:

```python
# -*- coding: utf-8 -*-
"""Logic thuần (không phụ thuộc Tkinter hay HTTP)."""
```

Tạo `webapp/services/dashboard.py` với phần chuyển nguyên văn (chưa có phần mới):

```python
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
```

Sửa `ui_dashboard.py`: bỏ các định nghĩa cũ và import lại từ service (giữ nguyên tên để `test_ui_dashboard.py` vẫn import từ `ui_dashboard`):

```bash
py -3.10 - <<'EOF'
import io
path = "ui_dashboard.py"
s = io.open(path, encoding="utf-8").read()

anchor = "from ui_design import COLORS, TYPOGRAPHY\n"
assert s.count(anchor) == 1
s = s.replace(
    anchor,
    anchor + "from webapp.services.dashboard import LOW_STOCK_THRESHOLD, WARNING_DAYS, build_dashboard_snapshot  # noqa: F401 (re-exported)\n",
)

start = s.index("LOW_STOCK_THRESHOLD = 10.0")
end = s.index("class DashboardUiMixin")
s = s[:start] + s[end:]

io.open(path, "w", encoding="utf-8", newline="\n").write(s)
print("ui_dashboard.py updated")
EOF
sed -n 9,24p ui_dashboard.py
```

Expected: phần đầu file còn các import, một dòng `from webapp.services.dashboard import …`, hai dòng trống rồi `class DashboardUiMixin:`; không còn `def build_dashboard_snapshot`.

- [ ] **Step 2: Chạy test Tkinter cũ để xác nhận refactor không đổi hành vi**

Run: `py -3.10 -m unittest test_ui_dashboard -v 2>&1 | tail -8`
Expected: `OK` (các test cũ của `build_dashboard_snapshot` vẫn pass, nay đi qua service).

- [ ] **Step 3: Viết test thất bại cho `build_dashboard_payload`**

Tạo `test_webapp_dashboard.py`:

```python
# -*- coding: utf-8 -*-
import datetime as dt
import os
import tempfile
import unittest

from database import DB
from webapp.services import dashboard as service

HOSTILE_NAME = "<img src=x onerror=alert(1)> \"quote\" & 'apos' " + "Ư" * 300


class SeededDatabaseCase(unittest.TestCase):
    """Bốn sản phẩm: hết hạn, cận hạn, tồn thấp, bình thường (ngày tính theo hôm nay)."""

    def setUp(self):
        self.today = dt.date.today()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = os.path.join(self.tmp.name, "dashboard.db")
        self.db = DB(self.db_path)
        self.addCleanup(self.db.conn.close)
        self.add_product(1, "Thuốc hết hạn", "L-EXP", -10, 20)
        self.add_product(2, "Thuốc cận hạn", "L-NEAR", 30, 50)
        self.add_product(3, "Vật tư tồn thấp", "L-LOW", 800, 5)
        self.add_product(4, "Thuốc bình thường", "L-OK", 900, 100)

    def iso(self, days_from_today):
        return (self.today + dt.timedelta(days=days_from_today)).isoformat()

    def add_product(self, product_id, name, lot, expiry_offset_days, qty, fund="BHYT"):
        self.db.conn.execute(
            "INSERT INTO products(id, name, defaultUnit) VALUES(?, ?, 'Viên')", (product_id, name)
        )
        self.db.conn.execute(
            "INSERT INTO product_units(productId, unitCode, toBaseQty, price) VALUES(?, 'Viên', 1, 0)",
            (product_id,),
        )
        self.db.conn.commit()
        self.db.record_purchase(
            [{
                "productId": product_id, "productName": name, "qty": qty, "unitCode": "Viên",
                "lotNo": lot, "expiryDate": self.iso(expiry_offset_days), "cost": 1000,
                "fundSource": fund,
            }],
            "NCC", "Nhập kho", "",
        )


class DashboardServiceTests(SeededDatabaseCase):
    def test_cards_match_the_tkinter_dashboard_logic(self):
        summary = self.db.dashboard_summary(service.WARNING_DAYS)
        snapshot = service.build_dashboard_snapshot(self.db.get_inventory(), warning_days=service.WARNING_DAYS)
        payload = service.build_dashboard_payload(self.db)
        self.assertEqual(payload["cards"], {
            "productCount": int(summary["product_count"]),
            "activeLotCount": snapshot["active_lot_count"],
            "nearExpiryCount": snapshot["near_expiry_count"],
            "expiredCount": snapshot["expired_count"],
            "lowStockCount": snapshot["low_stock_count"],
        })
        self.assertEqual(
            payload["cards"],
            {"productCount": 4, "activeLotCount": 4, "nearExpiryCount": 1, "expiredCount": 1, "lowStockCount": 1},
        )

    def test_counts_cover_the_whole_warning_set(self):
        payload = service.build_dashboard_payload(self.db)
        self.assertEqual(payload["warnings"]["counts"], {"all": 3, "expired": 1, "near": 1, "low": 1})
        self.assertEqual(payload["warningDays"], 90)
        self.assertEqual(payload["lowStockThreshold"], 10)

    def test_rows_follow_the_contract_and_severity_order(self):
        rows = service.build_dashboard_payload(self.db)["warnings"]["rows"]
        self.assertEqual([r["severity"] for r in rows], [0, 2, 3])
        self.assertEqual(
            set(rows[0]),
            {"productId", "batchId", "productName", "lotNo", "expiryDate", "fundSource",
             "stockBase", "status", "severity", "daysLeft"},
        )
        self.assertEqual(rows[0]["productName"], "Thuốc hết hạn")
        self.assertEqual(rows[0]["status"], "Đã hết hạn")

    def test_filter_selects_one_group_and_leaves_counts_unchanged(self):
        for flt, severity in (("expired", 0), ("near", 2), ("low", 3)):
            with self.subTest(flt=flt):
                warnings = service.build_dashboard_payload(self.db, flt=flt)["warnings"]
                self.assertEqual([r["severity"] for r in warnings["rows"]], [severity])
                self.assertEqual(warnings["counts"], {"all": 3, "expired": 1, "near": 1, "low": 1})

    def test_limit_is_applied_after_the_filter(self):
        # Nếu cắt trước rồi mới lọc, dòng "low" (xếp sau cùng) sẽ biến mất.
        warnings = service.build_dashboard_payload(self.db, flt="low", limit=1)["warnings"]
        self.assertEqual([r["productName"] for r in warnings["rows"]], ["Vật tư tồn thấp"])
        all_rows = service.build_dashboard_payload(self.db, limit=1)["warnings"]["rows"]
        self.assertEqual(len(all_rows), 1)

    def test_invalid_parameters_are_rejected(self):
        for kwargs in (
            {"flt": "bogus"}, {"flt": ""}, {"flt": None},
            {"limit": 0}, {"limit": -1}, {"limit": service.MAX_LIMIT + 1},
            {"limit": True}, {"limit": "5"}, {"limit": 2.5},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    service.build_dashboard_payload(self.db, **kwargs)

    def test_limit_boundaries_are_accepted(self):
        service.build_dashboard_payload(self.db, limit=1)
        service.build_dashboard_payload(self.db, limit=service.MAX_LIMIT)

    def test_hostile_text_is_returned_verbatim(self):
        self.add_product(5, HOSTILE_NAME, "L-<b>", -5, 7, fund="Quỹ <i>x</i>")
        rows = service.build_dashboard_payload(self.db)["warnings"]["rows"]
        hostile = [r for r in rows if r["productId"] == 5][0]
        self.assertEqual(hostile["productName"], HOSTILE_NAME)
        self.assertEqual(hostile["lotNo"], "L-<b>")
        self.assertEqual(hostile["fundSource"], "Quỹ <i>x</i>")

    def test_activities_are_the_ten_newest_audit_rows(self):
        for i in range(12):
            self.db.conn.execute(
                "INSERT INTO audit_logs(timestamp, action, details) VALUES(?, ?, ?)",
                (f"2099-01-{i + 1:02d} 08:00:00", f"ACT{i}", f"chi tiết {i}"),  # tương lai: luôn mới hơn các dòng NHAP_KHO lúc dựng dữ liệu
            )
        self.db.conn.commit()
        activities = service.build_dashboard_payload(self.db)["activities"]
        self.assertEqual(len(activities), 10)
        self.assertEqual([a["action"] for a in activities][:3], ["ACT11", "ACT10", "ACT9"])
        self.assertEqual(set(activities[0]), {"timestamp", "action", "details"})

    def test_runtime_reports_backup_temperature_and_negative_stock(self):
        runtime = service.build_dashboard_payload(self.db)["runtime"]
        self.assertEqual(set(runtime), {"lastBackup", "latestTemperature", "negativeStockRows"})
        self.assertIsNone(runtime["latestTemperature"])
        self.assertEqual(runtime["negativeStockRows"], 0)

        self.db.add_temperature_log("2026-09-30", "Sáng", "Kho lạnh 1", 24.5, 55.0, "Thủ kho")
        # Bỏ qua bất biến tồn không âm bằng SQL trực tiếp để kiểm tra đếm thật.
        self.db.conn.execute(
            "INSERT INTO stock_movements(productId, batchId, unitCode, qty, qtyBase, type) "
            "SELECT productId, id, 'Viên', -500, -500, 'ADJUST' FROM batches WHERE lotNo='L-OK'"
        )
        self.db.conn.commit()
        runtime = service.build_dashboard_payload(self.db)["runtime"]
        self.assertEqual(
            runtime["latestTemperature"],
            {"logDate": "2026-09-30", "session": "Sáng", "locationName": "Kho lạnh 1",
             "temperature": 24.5, "humidity": 55.0, "recordedBy": "Thủ kho"},
        )
        self.assertEqual(runtime["negativeStockRows"], 1)
        last_backup = runtime["lastBackup"]
        self.assertTrue(last_backup is None or set(last_backup) == {"file", "created"})


class EmptyDatabaseTests(unittest.TestCase):
    def test_empty_database_gives_zero_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DB(os.path.join(tmp, "empty.db"))
            try:
                payload = service.build_dashboard_payload(db)
            finally:
                db.conn.close()
        self.assertEqual(
            payload["cards"],
            {"productCount": 0, "activeLotCount": 0, "nearExpiryCount": 0, "expiredCount": 0, "lowStockCount": 0},
        )
        self.assertEqual(payload["warnings"], {"counts": {"all": 0, "expired": 0, "near": 0, "low": 0}, "rows": []})
        self.assertEqual(payload["activities"], [])
        self.assertIsNone(payload["runtime"]["latestTemperature"])


class WarningCategoryTests(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(service.warning_category(0), "expired")
        self.assertEqual(service.warning_category(1), "expired")
        self.assertEqual(service.warning_category(2), "near")
        self.assertEqual(service.warning_category(3), "low")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_webapp_dashboard -v 2>&1 | tail -15`
Expected: lỗi `AttributeError: module 'webapp.services.dashboard' has no attribute 'build_dashboard_payload'` (hoặc `warning_category`) ở mọi test.

- [ ] **Step 5: Cài đặt `warning_category`, `validate_dashboard_params`, `build_dashboard_payload`**

Thêm vào cuối `webapp/services/dashboard.py`:

```python


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
```

- [ ] **Step 6: Chạy test để thấy đạt**

Run: `py -3.10 -m unittest test_webapp_dashboard test_ui_dashboard -v 2>&1 | tail -8`
Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add webapp/__init__.py webapp/services/__init__.py webapp/services/dashboard.py ui_dashboard.py test_webapp_dashboard.py
git commit -F - <<'EOF'
Add dashboard service shared by the Tkinter and web UIs

build_dashboard_snapshot moves verbatim from ui_dashboard.py (re-exported
there, existing tests unchanged). build_dashboard_payload adds the JSON
model with filter/limit (limit applied after filtering), full-set counts,
activities and runtime status.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 4: Router có scope (`webapp/routing.py`)

**Files:**
- Tạo: `webapp/routing.py`
- Test: `test_webapp_routing.py`

**Interfaces:**
- Consumes: không có.
- Produces (dùng ở Task 5–8): `SCOPE_LOCAL = "local"`, `SCOPE_LAN = "lan"`; `HttpError(status: int, message: str)`; `Request(method, path, query: Mapping[str,str], headers: Mapping[str,str], body: bytes, scope: str)` (dataclass bất biến); `Response(status=200, body=b"", content_type="application/json; charset=utf-8", headers={})`; `json_response(payload, status=200, headers=None) -> Response` (luôn có `Cache-Control: no-store`); `error_response(status, message, headers=None, **extra) -> Response` (JSON `{"success": False, "message": ..., **extra}`); `Router.add(method, path, handler, scopes=(SCOPE_LOCAL,))`; `Router.dispatch(request) -> Response` (404 không có path, 405 sai method kèm `Allow`, 403 sai scope, `HttpError` → JSON lỗi, lỗi bất kỳ khác → 500 "Lỗi hệ thống" và ghi log, không lộ nội dung lỗi).

- [ ] **Step 1: Viết test thất bại**

Tạo `test_webapp_routing.py`:

```python
# -*- coding: utf-8 -*-
import json
import unittest

from webapp.routing import (
    SCOPE_LAN,
    SCOPE_LOCAL,
    HttpError,
    Request,
    Response,
    Router,
    json_response,
)


def make_request(method="GET", path="/api/x", scope=SCOPE_LOCAL):
    return Request(method=method, path=path, query={}, headers={}, body=b"", scope=scope)


def body_of(response):
    return json.loads(response.body.decode("utf-8"))


class RouterTests(unittest.TestCase):
    def test_dispatches_to_the_matching_handler(self):
        router = Router()
        router.add("GET", "/api/x", lambda request: json_response({"success": True, "path": request.path}))
        response = router.dispatch(make_request())
        self.assertEqual(response.status, 200)
        self.assertEqual(body_of(response), {"success": True, "path": "/api/x"})

    def test_local_only_route_is_forbidden_from_the_lan_scope(self):
        router = Router()
        router.add("GET", "/api/admin", lambda request: json_response({"success": True}))
        response = router.dispatch(make_request(path="/api/admin", scope=SCOPE_LAN))
        self.assertEqual(response.status, 403)
        self.assertFalse(body_of(response)["success"])

    def test_route_declared_for_lan_is_allowed_from_lan_and_local_only_when_listed(self):
        router = Router()
        router.add("GET", "/api/lan", lambda request: json_response({"success": True}), scopes=(SCOPE_LAN,))
        router.add("GET", "/api/both", lambda request: json_response({"success": True}), scopes=(SCOPE_LOCAL, SCOPE_LAN))
        self.assertEqual(router.dispatch(make_request(path="/api/lan", scope=SCOPE_LAN)).status, 200)
        self.assertEqual(router.dispatch(make_request(path="/api/lan", scope=SCOPE_LOCAL)).status, 403)
        self.assertEqual(router.dispatch(make_request(path="/api/both", scope=SCOPE_LAN)).status, 200)
        self.assertEqual(router.dispatch(make_request(path="/api/both", scope=SCOPE_LOCAL)).status, 200)

    def test_unknown_path_is_404(self):
        self.assertEqual(Router().dispatch(make_request(path="/api/none")).status, 404)

    def test_wrong_method_is_405_with_allow_header(self):
        router = Router()
        router.add("GET", "/api/x", lambda request: json_response({"success": True}))
        router.add("POST", "/api/x", lambda request: json_response({"success": True}))
        response = router.dispatch(make_request(method="DELETE"))
        self.assertEqual(response.status, 405)
        self.assertEqual(response.headers["Allow"], "GET, POST")

    def test_http_error_becomes_a_json_error(self):
        def handler(request):
            raise HttpError(400, "Tham số sai")

        router = Router()
        router.add("GET", "/api/x", handler)
        response = router.dispatch(make_request())
        self.assertEqual(response.status, 400)
        self.assertEqual(body_of(response), {"success": False, "message": "Tham số sai"})

    def test_unexpected_exception_hides_internal_details(self):
        def handler(request):
            raise RuntimeError(r"không mở được C:\Users\secret\pharm.db")

        router = Router()
        router.add("GET", "/api/x", handler)
        with self.assertLogs("webapp.routing", level="ERROR"):
            response = router.dispatch(make_request())
        self.assertEqual(response.status, 500)
        self.assertEqual(body_of(response), {"success": False, "message": "Lỗi hệ thống"})
        self.assertNotIn(b"secret", response.body)

    def test_json_response_is_utf8_and_never_cached(self):
        response = json_response({"tên": "Thuốc Ư"})
        self.assertIsInstance(response, Response)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIn("Thuốc Ư".encode("utf-8"), response.body)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_webapp_routing -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'webapp.routing'`.

- [ ] **Step 3: Cài đặt**

Tạo `webapp/routing.py`:

```python
# -*- coding: utf-8 -*-
"""Router nhỏ cho backend web: mỗi route khai báo scope (local | lan)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Tuple

SCOPE_LOCAL = "local"
SCOPE_LAN = "lan"

log = logging.getLogger(__name__)


class HttpError(Exception):
    """Handler ném lỗi này để trả JSON lỗi với mã HTTP tương ứng."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = int(status)
        self.message = str(message)


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    query: Mapping[str, str]
    headers: Mapping[str, str]
    body: bytes
    scope: str


@dataclass
class Response:
    status: int = 200
    body: bytes = b""
    content_type: str = "application/json; charset=utf-8"
    headers: Dict[str, str] = field(default_factory=dict)


def json_response(payload, status: int = 200, headers=None) -> Response:
    merged = {"Cache-Control": "no-store"}
    merged.update(headers or {})
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return Response(status=status, body=body, headers=merged)


def error_response(status: int, message: str, headers=None, **extra) -> Response:
    payload = {"success": False, "message": message}
    payload.update(extra)
    return json_response(payload, status, headers)


class Router:
    def __init__(self):
        self._routes: Dict[str, Dict[str, Tuple[Callable[[Request], Response], frozenset]]] = {}

    def add(self, method, path, handler, scopes=(SCOPE_LOCAL,)):
        self._routes.setdefault(path, {})[method.upper()] = (handler, frozenset(scopes))

    def dispatch(self, request: Request) -> Response:
        by_method = self._routes.get(request.path)
        if by_method is None:
            return error_response(404, "Không tìm thấy")
        entry = by_method.get(request.method.upper())
        if entry is None:
            return error_response(
                405, "Phương thức không được hỗ trợ", headers={"Allow": ", ".join(sorted(by_method))}
            )
        handler, scopes = entry
        if request.scope not in scopes:
            return error_response(403, "Không được phép truy cập")
        try:
            return handler(request)
        except HttpError as exc:
            return error_response(exc.status, exc.message)
        except Exception:
            log.exception("Lỗi không xử lý được ở %s %s", request.method, request.path)
            return error_response(500, "Lỗi hệ thống")
```

- [ ] **Step 4: Chạy test để thấy đạt**

Run: `py -3.10 -m unittest test_webapp_routing -v 2>&1 | tail -6`
Expected: `OK` (8 test).

- [ ] **Step 5: Commit**

```bash
git add webapp/routing.py test_webapp_routing.py
git commit -F - <<'EOF'
Add scope-aware router for the local web backend

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 5: Header bảo mật, kiểm Host/Origin và phiên cục bộ

**Files:**
- Tạo: `webapp/security.py`, `webapp/auth.py`
- Test: `test_webapp_local_auth.py`

**Interfaces:**
- Consumes: không có.
- Produces (dùng ở Task 7): `security.SECURITY_HEADERS: dict` (CSP, nosniff, no-referrer); `security.host_allowed(host_header, port) -> bool`; `security.origin_allowed(headers, port) -> bool` (chấp nhận `Origin` thuộc danh sách cho phép, hoặc không có `Origin` nhưng `Sec-Fetch-Site: same-origin`); `auth.COOKIE_NAME = "qlk_session"`; `auth.LocalSession` với `.boot_token: str`, `.redeem_boot_token(candidate: str) -> str | None` (trả token phiên đúng một lần, sau đó luôn `None`; token sai không làm mất token đúng), `.session_cookie_header() -> str`, `.is_authenticated(cookie_header: str) -> bool`.

- [ ] **Step 1: Viết test thất bại**

Tạo `test_webapp_local_auth.py`:

```python
# -*- coding: utf-8 -*-
import unittest

from webapp.auth import COOKIE_NAME, LocalSession
from webapp.security import SECURITY_HEADERS, host_allowed, origin_allowed


class HostAndOriginTests(unittest.TestCase):
    def test_host_must_be_loopback_with_the_listener_port(self):
        for host in ("127.0.0.1:5000", "localhost:5000", "LOCALHOST:5000"):
            with self.subTest(host=host):
                self.assertTrue(host_allowed(host, 5000))
        for host in (
            None, "", "127.0.0.1", "127.0.0.1:5001", "evil.example", "evil.example:5000",
            "127.0.0.1:5000.evil.example", "0.0.0.0:5000", "[::1]:5000",
        ):
            with self.subTest(host=host):
                self.assertFalse(host_allowed(host, 5000))

    def test_origin_must_be_same_origin(self):
        self.assertTrue(origin_allowed({"Origin": "http://127.0.0.1:5000"}, 5000))
        self.assertTrue(origin_allowed({"Origin": "http://localhost:5000"}, 5000))
        self.assertTrue(origin_allowed({"Sec-Fetch-Site": "same-origin"}, 5000))
        self.assertFalse(origin_allowed({}, 5000))
        self.assertFalse(origin_allowed({"Origin": "http://evil.example"}, 5000))
        self.assertFalse(origin_allowed({"Origin": "http://127.0.0.1:5001"}, 5000))
        self.assertFalse(origin_allowed({"Origin": "null"}, 5000))
        self.assertFalse(origin_allowed({"Sec-Fetch-Site": "cross-site"}, 5000))
        # Origin hợp lệ không cứu được Sec-Fetch-Site sai, nhưng Origin sai thì luôn bị chặn.
        self.assertFalse(origin_allowed({"Origin": "http://evil.example", "Sec-Fetch-Site": "same-origin"}, 5000))

    def test_security_headers_are_the_specified_policy(self):
        self.assertEqual(
            SECURITY_HEADERS["Content-Security-Policy"],
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'",
        )
        self.assertEqual(SECURITY_HEADERS["X-Content-Type-Options"], "nosniff")
        self.assertEqual(SECURITY_HEADERS["Referrer-Policy"], "no-referrer")


class LocalSessionTests(unittest.TestCase):
    def test_boot_token_is_single_use_and_returns_the_session_token(self):
        session = LocalSession()
        first = session.redeem_boot_token(session.boot_token)
        self.assertTrue(first)
        self.assertIsNone(session.redeem_boot_token(session.boot_token))

    def test_wrong_token_does_not_consume_the_real_one(self):
        session = LocalSession()
        for wrong in ("", "x", session.boot_token[:-1], session.boot_token + "a", "Ư" * 20):
            with self.subTest(wrong=wrong):
                self.assertIsNone(session.redeem_boot_token(wrong))
        self.assertTrue(session.redeem_boot_token(session.boot_token))

    def test_cookie_header_has_the_required_attributes(self):
        header = LocalSession().session_cookie_header()
        self.assertTrue(header.startswith(COOKIE_NAME + "="))
        for attribute in ("Path=/", "HttpOnly", "SameSite=Strict"):
            self.assertIn(attribute, header)
        self.assertNotIn("Max-Age", header)
        self.assertNotIn("Expires", header)

    def test_cookie_authentication(self):
        session = LocalSession()
        cookie = session.session_cookie_header().split(";", 1)[0]
        self.assertTrue(session.is_authenticated(cookie))
        self.assertTrue(session.is_authenticated("other=1; " + cookie))
        for bad in ("", None, COOKIE_NAME + "=", COOKIE_NAME + "=wrong", cookie + "x", "garbage;;;", "=="):
            with self.subTest(bad=bad):
                self.assertFalse(session.is_authenticated(bad))

    def test_two_sessions_do_not_accept_each_others_cookies(self):
        a, b = LocalSession(), LocalSession()
        self.assertNotEqual(a.boot_token, b.boot_token)
        self.assertFalse(b.is_authenticated(a.session_cookie_header().split(";", 1)[0]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_webapp_local_auth -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'webapp.auth'`.

- [ ] **Step 3: Cài đặt**

Tạo `webapp/security.py`:

```python
# -*- coding: utf-8 -*-
"""Header bảo mật cố định và kiểm Host/Origin cho listener cục bộ."""

from __future__ import annotations

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'"
)

SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


def _allowed_hosts(port: int):
    return {f"127.0.0.1:{port}", f"localhost:{port}"}


def host_allowed(host_header, port: int) -> bool:
    """Chống DNS rebinding: chỉ nhận đúng host loopback kèm cổng của listener."""
    return str(host_header or "").lower() in _allowed_hosts(port)


def origin_allowed(headers, port: int) -> bool:
    """Request ghi dữ liệu phải cùng origin: Origin hợp lệ, hoặc không có Origin
    nhưng trình duyệt báo ``Sec-Fetch-Site: same-origin``."""
    origin = headers.get("Origin")
    if origin is not None:
        return str(origin).lower() in {f"http://{host}" for host in _allowed_hosts(port)}
    return str(headers.get("Sec-Fetch-Site") or "").lower() == "same-origin"
```

Tạo `webapp/auth.py`:

```python
# -*- coding: utf-8 -*-
"""Phiên cục bộ: boot token dùng một lần đổi lấy cookie phiên HttpOnly."""

from __future__ import annotations

import hmac
import secrets
import threading
from http.cookies import CookieError, SimpleCookie

COOKIE_NAME = "qlk_session"


def _same(a: str, b: str) -> bool:
    return hmac.compare_digest(str(a).encode("utf-8"), str(b).encode("utf-8"))


class LocalSession:
    """Một phiên cho một lần chạy ứng dụng.

    ``boot_token`` chỉ đổi được một lần (cửa sổ pywebview mở ``/boot/<token>``);
    token sai không làm mất token đúng, vì token có 256 bit và việc tiêu hủy khi
    đoán sai chỉ giúp kẻ khác phá được lần khởi động hợp lệ.
    """

    def __init__(self):
        self.boot_token = secrets.token_urlsafe(32)
        self._session_token = secrets.token_urlsafe(32)
        self._boot_available = True
        self._lock = threading.Lock()

    def redeem_boot_token(self, candidate):
        with self._lock:
            if not self._boot_available or not _same(candidate, self.boot_token):
                return None
            self._boot_available = False
            return self._session_token

    def session_cookie_header(self) -> str:
        # Cookie phiên (không Max-Age/Expires): hết hạn khi đóng ứng dụng.
        return f"{COOKIE_NAME}={self._session_token}; Path=/; HttpOnly; SameSite=Strict"

    def is_authenticated(self, cookie_header) -> bool:
        jar = SimpleCookie()
        try:
            jar.load(cookie_header or "")
        except CookieError:
            return False
        morsel = jar.get(COOKIE_NAME)
        return morsel is not None and bool(morsel.value) and _same(morsel.value, self._session_token)
```

- [ ] **Step 4: Chạy test để thấy đạt**

Run: `py -3.10 -m unittest test_webapp_local_auth -v 2>&1 | tail -6`
Expected: `OK` (8 test).

- [ ] **Step 5: Commit**

```bash
git add webapp/security.py webapp/auth.py test_webapp_local_auth.py
git commit -F - <<'EOF'
Add local session auth and Host/Origin checks

Single-use boot token exchanged for an HttpOnly session cookie, loopback
Host allowlist (DNS rebinding), same-origin check for unsafe methods and
the fixed security headers.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 6: Phục vụ file tĩnh an toàn (`webapp/static.py`)

**Files:**
- Tạo: `webapp/static.py`
- Test: `test_webapp_static.py`

**Interfaces:**
- Consumes: `webapp.routing.Response`.
- Produces (dùng ở Task 7): `static.CONTENT_TYPES: dict[str, str]` (đúng 7 phần mở rộng cho phép), `static.resolve_static(web_root, url_path) -> Path | None`, `static.serve_static(web_root, url_path) -> Response` (200 với `Cache-Control: no-cache`, hoặc 404 `text/plain` với `no-store`; `/` → `index.html`).

- [ ] **Step 1: Viết test thất bại**

Tạo `test_webapp_static.py`:

```python
# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from pathlib import Path

from webapp.static import CONTENT_TYPES, resolve_static, serve_static


class StaticServingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.web = base / "web"
        (self.web / "css").mkdir(parents=True)
        (self.web / "js").mkdir()
        (self.web / "index.html").write_text("<!doctype html><p>trang chủ</p>", encoding="utf-8")
        (self.web / "css" / "a.css").write_text("body{}", encoding="utf-8")
        (self.web / "js" / "a.js").write_text("export const a = 1;", encoding="utf-8")
        (self.web / "notes.txt").write_text("không được phục vụ", encoding="utf-8")
        (self.web / ".hidden.js").write_text("x", encoding="utf-8")
        (base / "secret.txt").write_text("bí mật", encoding="utf-8")

    def test_root_serves_index_html(self):
        response = serve_static(self.web, "/")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("trang chủ".encode("utf-8"), response.body)
        self.assertEqual(response.headers["Cache-Control"], "no-cache")

    def test_content_types_for_allowed_extensions(self):
        self.assertEqual(serve_static(self.web, "/css/a.css").content_type, "text/css; charset=utf-8")
        self.assertEqual(serve_static(self.web, "/js/a.js").content_type, "text/javascript; charset=utf-8")
        self.assertEqual(
            sorted(CONTENT_TYPES),
            [".css", ".html", ".ico", ".js", ".png", ".svg", ".woff2"],
        )

    def test_path_escape_attempts_are_all_404(self):
        attempts = [
            "/../secret.txt",
            "/%2e%2e/secret.txt",
            "/css/../../secret.txt",
            "/css/%2e%2e/%2e%2e/secret.txt",
            "/js//a.js",
            "/js\\a.js",
            "/%5cjs%5ca.js",
            "/C:/Windows/win.ini",
            "/js/a.js\x00",
            "/%00",
            "/js/a.js::$DATA",
            "/.hidden.js",
            "/css/",
            "/css",
            "/js/missing.js",
            "/notes.txt",
        ]
        for path in attempts:
            with self.subTest(path=path):
                response = serve_static(self.web, path)
                self.assertEqual(response.status, 404)
                self.assertNotIn("bí mật".encode("utf-8"), response.body)
                self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_resolve_never_leaves_the_web_root(self):
        for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/css/../../secret.txt"):
            self.assertIsNone(resolve_static(self.web, path))
        resolved = resolve_static(self.web, "/js/a.js")
        self.assertEqual(resolved, (self.web / "js" / "a.js").resolve())

    def test_symlinks_are_refused(self):
        link = self.web / "js" / "link.js"
        try:
            os.symlink(self.web.parent / "secret.txt", link)
        except (OSError, NotImplementedError):
            self.skipTest("Không tạo được symlink (thiếu quyền trên Windows)")
        self.assertEqual(serve_static(self.web, "/js/link.js").status, 404)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_webapp_static -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'webapp.static'`.

- [ ] **Step 3: Cài đặt**

Tạo `webapp/static.py`:

```python
# -*- coding: utf-8 -*-
"""Phục vụ thư mục ``web/`` an toàn: không thoát khỏi thư mục gốc, không liệt kê thư mục."""

from __future__ import annotations

import urllib.parse
from pathlib import Path

from webapp.routing import Response

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}


def resolve_static(web_root, url_path):
    """Trả về Path của file hợp lệ nằm trong ``web_root``, hoặc None."""
    rel = urllib.parse.unquote(url_path)
    if "\x00" in rel or "\\" in rel:
        return None
    rel = rel.lstrip("/")
    if rel == "":
        rel = "index.html"
    parts = rel.split("/")
    for part in parts:
        if part in ("", ".", "..") or part.startswith(".") or ":" in part:
            return None

    root = Path(web_root).resolve()
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            return None
    try:
        resolved = current.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):
        return None
    if resolved.suffix.lower() not in CONTENT_TYPES or not resolved.is_file():
        return None
    return resolved


def _not_found() -> Response:
    return Response(
        status=404,
        body="Không tìm thấy".encode("utf-8"),
        content_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )


def serve_static(web_root, url_path) -> Response:
    path = resolve_static(web_root, url_path)
    if path is None:
        return _not_found()
    try:
        body = path.read_bytes()
    except OSError:
        return _not_found()
    return Response(
        status=200,
        body=body,
        content_type=CONTENT_TYPES[path.suffix.lower()],
        headers={"Cache-Control": "no-cache"},
    )
```

- [ ] **Step 4: Chạy test để thấy đạt**

Run: `py -3.10 -m unittest test_webapp_static -v 2>&1 | tail -6`
Expected: `OK` (5 test; `test_symlinks_are_refused` có thể hiện `skipped` nếu Windows không cho tạo symlink, vẫn tính là đạt).

- [ ] **Step 5: Commit**

```bash
git add webapp/static.py test_webapp_static.py
git commit -F - <<'EOF'
Add safe static file serving for web/

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 7: Listener cục bộ và harness kiểm thử HTTP

**Files:**
- Tạo: `webapp/listener.py`, `webapp_testkit.py`
- Test: `test_webapp_listener.py`

**Interfaces:**
- Consumes: Task 2 (`http_limits.*`), Task 4 (`Router`, `Request`, `Response`, `error_response`, `SCOPE_LOCAL`), Task 5 (`LocalSession`, `SECURITY_HEADERS`, `host_allowed`, `origin_allowed`), Task 6 (`serve_static`).
- Produces (dùng ở Task 8, 9, 12): `listener.LocalListener(router, session, web_root, host="127.0.0.1")` (ném `ValueError` nếu `host` không phải `127.0.0.1`) với `.port: int`, `.session`, `.boot_url() -> str`, `.start()`, `.stop()` (idempotent). `webapp_testkit.Harness(test_case, router, web_root)` với `.port`, `.session`, `.cookie`, `.login() -> str`, `.request(method, path, *, headers=None, body=None, cookie=None) -> (status, headers_lowercase_dict, body_bytes)`, `.json(...) -> (status, headers, parsed_json)`; `cookie=None` nghĩa là dùng cookie đã đăng nhập, `cookie=""` nghĩa là không gửi cookie.

Luồng xử lý mỗi request: kiểm `Host` → kiểm framing body → `/boot/<token>` → xác thực cookie (API: 401 JSON; trang: 401 rỗng) → kiểm `Origin` với method không phải GET/HEAD → router (`/api/*`) hoặc file tĩnh (GET).

- [ ] **Step 1: Tạo harness và viết test thất bại**

Tạo `webapp_testkit.py` (không bắt đầu bằng `test`, nên `unittest discover` không nạp nó như test):

```python
# -*- coding: utf-8 -*-
"""Harness HTTP dùng chung cho test của backend web."""

import http.client
import json

from webapp.auth import LocalSession
from webapp.listener import LocalListener


class Harness:
    def __init__(self, test_case, router, web_root):
        self.session = LocalSession()
        self.listener = LocalListener(router, self.session, web_root)
        self.listener.start()
        test_case.addCleanup(self.listener.stop)
        self.cookie = None

    @property
    def port(self):
        return self.listener.port

    def request(self, method, path, *, headers=None, body=None, cookie=None):
        merged = dict(headers or {})
        cookie_value = cookie if cookie is not None else self.cookie
        if cookie_value:
            merged["Cookie"] = cookie_value
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.request(method, path, body=body, headers=merged)
            response = conn.getresponse()
            data = response.read()
            return response.status, {k.lower(): v for k, v in response.getheaders()}, data
        finally:
            conn.close()

    def json(self, method, path, **kwargs):
        status, headers, data = self.request(method, path, **kwargs)
        return status, headers, json.loads(data.decode("utf-8"))

    def login(self):
        status, headers, _ = self.request("GET", f"/boot/{self.session.boot_token}", cookie="")
        assert status == 302, status
        self.cookie = headers["set-cookie"].split(";", 1)[0]
        return self.cookie
```

Tạo `test_webapp_listener.py`:

```python
# -*- coding: utf-8 -*-
import tempfile
import unittest
from pathlib import Path

from http_limits import MAX_REQUEST_BODY_BYTES
from webapp.auth import LocalSession
from webapp.listener import LocalListener
from webapp.routing import SCOPE_LAN, Router, json_response
from webapp.security import SECURITY_HEADERS
from webapp_testkit import Harness


class ListenerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.web = Path(self.tmp.name)
        (self.web / "js").mkdir()
        (self.web / "index.html").write_text("<!doctype html><p>trang chủ</p>", encoding="utf-8")
        (self.web / "js" / "a.js").write_text("export const a = 1;", encoding="utf-8")
        router = Router()
        router.add("GET", "/api/ping", lambda request: json_response({"success": True, "scope": request.scope}))
        router.add("GET", "/api/lan-only", lambda request: json_response({"success": True}), scopes=(SCOPE_LAN,))
        self.harness = Harness(self, router, self.web)

    @property
    def origin(self):
        return {"Origin": f"http://127.0.0.1:{self.harness.port}"}


class AuthenticationTests(ListenerCase):
    def test_api_without_cookie_is_401_json(self):
        status, _, payload = self.harness.json("GET", "/api/ping")
        self.assertEqual(status, 401)
        self.assertEqual(payload, {"success": False, "message": "Chưa xác thực", "auth_required": True})

    def test_page_without_cookie_is_401_and_empty(self):
        status, _, body = self.harness.request("GET", "/")
        self.assertEqual(status, 401)
        self.assertEqual(body, b"")

    def test_boot_sets_an_httponly_cookie_and_redirects_home(self):
        status, headers, _ = self.harness.request("GET", f"/boot/{self.harness.session.boot_token}")
        self.assertEqual(status, 302)
        self.assertEqual(headers["location"], "/")
        cookie = headers["set-cookie"]
        for attribute in ("HttpOnly", "SameSite=Strict", "Path=/"):
            self.assertIn(attribute, cookie)

    def test_cookie_unlocks_pages_and_api_repeatedly(self):
        self.harness.login()
        for _ in range(2):
            status, _, body = self.harness.request("GET", "/")
            self.assertEqual(status, 200)
            self.assertIn("trang chủ".encode("utf-8"), body)
        status, _, payload = self.harness.json("GET", "/api/ping")
        self.assertEqual((status, payload["scope"]), (200, "local"))

    def test_boot_token_is_single_use_but_the_cookie_keeps_working(self):
        cookie = self.harness.login()
        status, _, _ = self.harness.request("GET", f"/boot/{self.harness.session.boot_token}", cookie="")
        self.assertEqual(status, 401)
        self.assertEqual(self.harness.request("GET", "/", cookie=cookie)[0], 200)

    def test_wrong_boot_token_is_rejected_and_the_real_one_still_works(self):
        status, _, _ = self.harness.request("GET", "/boot/not-the-token", cookie="")
        self.assertEqual(status, 401)
        self.harness.login()

    def test_a_forged_cookie_is_rejected(self):
        self.harness.login()
        status, _, _ = self.harness.request("GET", "/api/ping", cookie="qlk_session=forged")
        self.assertEqual(status, 401)


class HostAndOriginTests(ListenerCase):
    def test_foreign_or_wrong_port_host_is_403_even_with_a_valid_cookie(self):
        self.harness.login()
        for host in ("evil.example", f"127.0.0.1:{self.harness.port + 1}", "127.0.0.1"):
            with self.subTest(host=host):
                status, _, _ = self.harness.request("GET", "/api/ping", headers={"Host": host})
                self.assertEqual(status, 403)

    def test_wrong_host_does_not_consume_the_boot_token(self):
        status, _, _ = self.harness.request(
            "GET", f"/boot/{self.harness.session.boot_token}", headers={"Host": "evil.example"}, cookie=""
        )
        self.assertEqual(status, 403)
        self.harness.login()

    def test_localhost_alias_host_is_accepted(self):
        self.harness.login()
        status, _, _ = self.harness.request(
            "GET", "/api/ping", headers={"Host": f"localhost:{self.harness.port}"}
        )
        self.assertEqual(status, 200)

    def test_unsafe_methods_need_a_same_origin_marker(self):
        self.harness.login()
        status, _, _ = self.harness.request("POST", "/api/ping", body=b"{}")
        self.assertEqual(status, 403)
        status, _, _ = self.harness.request("POST", "/api/ping", body=b"{}", headers={"Origin": "http://evil.example"})
        self.assertEqual(status, 403)
        # Origin hợp lệ đi qua được lớp kiểm tra, tới router và nhận 405 (route chỉ có GET).
        status, _, _ = self.harness.request("POST", "/api/ping", body=b"{}", headers=self.origin)
        self.assertEqual(status, 405)
        status, _, _ = self.harness.request(
            "POST", "/api/ping", body=b"{}", headers={"Sec-Fetch-Site": "same-origin"}
        )
        self.assertEqual(status, 405)


class RoutingAndStaticTests(ListenerCase):
    def test_lan_only_route_is_403_on_the_local_listener(self):
        self.harness.login()
        self.assertEqual(self.harness.request("GET", "/api/lan-only")[0], 403)

    def test_unknown_api_path_is_404_json_and_unknown_page_is_404(self):
        self.harness.login()
        self.assertEqual(self.harness.json("GET", "/api/none")[0], 404)
        self.assertEqual(self.harness.request("GET", "/nope.html")[0], 404)

    def test_responses_carry_security_and_cache_headers(self):
        self.harness.login()
        _, page_headers, _ = self.harness.request("GET", "/")
        _, api_headers, _ = self.harness.request("GET", "/api/ping")
        _, denied_headers, _ = self.harness.request("GET", "/api/ping", cookie="")
        for headers in (page_headers, api_headers, denied_headers):
            for name, value in SECURITY_HEADERS.items():
                self.assertEqual(headers[name.lower()], value)
        self.assertEqual(page_headers["cache-control"], "no-cache")
        self.assertEqual(api_headers["cache-control"], "no-store")
        self.assertNotIn("python", page_headers.get("server", "").lower())

    def test_javascript_is_served_as_a_module_capable_type(self):
        self.harness.login()
        status, headers, body = self.harness.request("GET", "/js/a.js")
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "text/javascript; charset=utf-8")
        self.assertEqual(body, b"export const a = 1;")


class FramingTests(ListenerCase):
    def test_oversized_and_malformed_bodies_are_rejected_before_reading(self):
        self.harness.login()
        cases = (
            ({"Content-Length": str(MAX_REQUEST_BODY_BYTES + 1)}, 413),
            ({"Content-Length": "abc"}, 400),
            ({"Content-Length": "-5"}, 400),
            ({"Transfer-Encoding": "chunked"}, 400),
        )
        for extra, expected in cases:
            with self.subTest(extra=extra):
                headers = dict(self.origin)
                headers.update(extra)
                status, _, _ = self.harness.request("POST", "/api/ping", headers=headers)
                self.assertEqual(status, expected)


class ConstructionTests(unittest.TestCase):
    def test_only_loopback_binding_is_allowed(self):
        for host in ("0.0.0.0", "192.168.1.10", "", "localhost"):
            with self.subTest(host=host):
                with self.assertRaises(ValueError):
                    LocalListener(Router(), LocalSession(), Path("."), host=host)

    def test_port_is_assigned_by_the_system_and_boot_url_uses_it(self):
        session = LocalSession()
        listener = LocalListener(Router(), session, Path("."))
        try:
            self.assertGreater(listener.port, 0)
            self.assertEqual(listener.boot_url(), f"http://127.0.0.1:{listener.port}/boot/{session.boot_token}")
        finally:
            listener.stop()

    def test_stop_is_idempotent_and_safe_without_start(self):
        listener = LocalListener(Router(), LocalSession(), Path("."))
        listener.stop()
        listener.stop()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_webapp_listener -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'webapp.listener'`.

- [ ] **Step 3: Tạo `webapp/listener.py`**

```python
# -*- coding: utf-8 -*-
"""Listener loopback: boot token -> cookie phiên, kiểm Host/Origin, router và file tĩnh."""

from __future__ import annotations

import http.server
import threading
import urllib.parse
from pathlib import Path

from http_limits import (
    REQUEST_QUEUE_SIZE,
    REQUEST_SOCKET_TIMEOUT_SECONDS,
    RequestBodyPolicyError,
    validate_request_body_headers,
)
from webapp.auth import LocalSession
from webapp.routing import SCOPE_LOCAL, Request, Response, Router, error_response
from webapp.security import SECURITY_HEADERS, host_allowed, origin_allowed
from webapp.static import serve_static

LOOPBACK_HOSTS = ("127.0.0.1",)
BODY_METHODS = ("POST", "PUT", "PATCH")


def _make_handler(router: Router, session: LocalSession, web_root: Path, scope: str):
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "QuanLyKhoWeb"
        sys_version = ""
        timeout = REQUEST_SOCKET_TIMEOUT_SECONDS

        def log_message(self, format, *args):  # noqa: A002 - tên tham số do thư viện chuẩn quy định
            pass

        def _send(self, response: Response, close: bool = False):
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            for name, value in SECURITY_HEADERS.items():
                self.send_header(name, value)
            for name, value in response.headers.items():
                self.send_header(name, value)
            if close:
                self.send_header("Connection", "close")
                self.close_connection = True
            self.end_headers()
            try:
                self.wfile.write(response.body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _boot(self, token: str) -> Response:
            if not session.redeem_boot_token(token):
                return error_response(401, "Token khởi động không hợp lệ hoặc đã dùng")
            return Response(
                status=302,
                body=b"",
                content_type="text/plain; charset=utf-8",
                headers={
                    "Location": "/",
                    "Set-Cookie": session.session_cookie_header(),
                    "Cache-Control": "no-store",
                },
            )

        def _handle(self):
            port = self.server.server_address[1]
            if not host_allowed(self.headers.get("Host"), port):
                self._send(error_response(403, "Host không hợp lệ"), close=True)
                return
            try:
                length = validate_request_body_headers(self.headers)
            except RequestBodyPolicyError as exc:
                self._send(error_response(exc.status_code, exc.message), close=True)
                return
            body = self.rfile.read(length) if length and self.command in BODY_METHODS else b""

            parsed = urllib.parse.urlsplit(self.path)
            path = parsed.path
            if self.command == "GET" and path.startswith("/boot/"):
                self._send(self._boot(urllib.parse.unquote(path[len("/boot/"):])))
                return

            if not session.is_authenticated(self.headers.get("Cookie", "")):
                if path.startswith("/api/"):
                    self._send(error_response(401, "Chưa xác thực", auth_required=True))
                else:
                    self._send(Response(
                        status=401, body=b"", content_type="text/html; charset=utf-8",
                        headers={"Cache-Control": "no-store"},
                    ))
                return

            if self.command not in ("GET", "HEAD") and not origin_allowed(self.headers, port):
                self._send(error_response(403, "Origin không hợp lệ"))
                return

            if path.startswith("/api/"):
                query = {
                    key: values[0]
                    for key, values in urllib.parse.parse_qs(parsed.query, keep_blank_values=True).items()
                }
                request = Request(
                    method=self.command, path=path, query=query,
                    headers=self.headers, body=body, scope=scope,
                )
                self._send(router.dispatch(request))
            elif self.command == "GET":
                self._send(serve_static(web_root, path))
            else:
                self._send(error_response(405, "Phương thức không được hỗ trợ", headers={"Allow": "GET"}))

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _handle

    return Handler


class _Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False
    request_queue_size = REQUEST_QUEUE_SIZE


class LocalListener:
    """HTTP server loopback cho cửa sổ desktop (scope ``local``)."""

    def __init__(self, router: Router, session: LocalSession, web_root, host: str = "127.0.0.1"):
        if host not in LOOPBACK_HOSTS:
            raise ValueError("Listener cục bộ chỉ được bind vào địa chỉ loopback 127.0.0.1")
        self.session = session
        self._httpd = _Server((host, 0), _make_handler(router, session, Path(web_root), SCOPE_LOCAL))
        self._thread = None

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    def boot_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/boot/{self.session.boot_token}"

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            kwargs={"poll_interval": 0.1},
            name="qlk-local-listener",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        thread, self._thread = self._thread, None
        if thread is not None:
            self._httpd.shutdown()
            thread.join(timeout=5)
        self._httpd.server_close()
```

- [ ] **Step 4: Chạy test để thấy đạt**

Run: `py -3.10 -m unittest test_webapp_listener -v 2>&1 | tail -8`
Expected: `OK` (19 test). Nếu một test về `Content-Length` quá lớn treo quá 10 giây, kiểm tra lại thứ tự trong `_handle`: kiểm `Host` rồi `validate_request_body_headers` phải chạy **trước** khi đọc body.

- [ ] **Step 5: Commit**

```bash
git add webapp/listener.py webapp_testkit.py test_webapp_listener.py
git commit -F - <<'EOF'
Add loopback listener with boot-token auth

ThreadingHTTPServer bound to 127.0.0.1 on a system-assigned port: Host
allowlist, bounded body framing, single-use boot token to HttpOnly cookie,
same-origin check for unsafe methods, scope-aware router and static files.
Includes a shared HTTP test harness.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 8: Endpoint `/api/dashboard` và `build_router`

**Files:**
- Tạo: `webapp/api/__init__.py`, `webapp/api/dashboard.py`, `webapp/app.py`
- Sửa: `test_webapp_dashboard.py` (thêm lớp `DashboardApiTests` và các import ở đầu file)

**Interfaces:**
- Consumes: Task 3 (`build_dashboard_payload`, `validate_dashboard_params`, `DEFAULT_LIMIT`), Task 4 (`Router`, `HttpError`, `json_response`, `SCOPE_LOCAL`), Task 7 (`Harness`).
- Produces (dùng ở Task 9): `webapp.app.build_router(db_factory) -> Router` trong đó `db_factory` là hàm không tham số trả về đối tượng `DB` (handler tự đóng `db.conn` sau mỗi request); route `GET /api/dashboard` scope `local` trả `{"success": true, ...payload}`; tham số sai trả 400; lỗi khác trả 500 "Lỗi hệ thống".

- [ ] **Step 1: Thêm test thất bại**

Sửa phần import ở đầu `test_webapp_dashboard.py` thành:

```python
import datetime as dt
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import DB
from webapp.app import build_router
from webapp.services import dashboard as service
from webapp_testkit import Harness
```

Rồi thêm lớp sau **trước** dòng `if __name__ == "__main__":` ở cuối file:

```python
class DashboardApiTests(SeededDatabaseCase):
    def setUp(self):
        super().setUp()
        self.web_root = Path(self.tmp.name) / "web"
        self.web_root.mkdir()
        self.harness = Harness(self, build_router(lambda: DB(self.db_path)), self.web_root)
        self.harness.login()

    def get(self, query=""):
        return self.harness.json("GET", "/api/dashboard" + query)

    def test_requires_authentication(self):
        status, _, payload = self.harness.json("GET", "/api/dashboard", cookie="")
        self.assertEqual(status, 401)
        self.assertTrue(payload["auth_required"])

    def test_returns_the_documented_contract(self):
        status, headers, payload = self.get()
        self.assertEqual(status, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(
            set(payload),
            {"success", "warningDays", "lowStockThreshold", "cards", "warnings", "activities", "runtime"},
        )
        self.assertEqual(set(payload["warnings"]), {"counts", "rows"})
        self.assertEqual(payload["warnings"]["counts"], {"all": 3, "expired": 1, "near": 1, "low": 1})
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertIn("default-src 'self'", headers["content-security-policy"])

    def test_filter_and_limit_query_parameters(self):
        _, _, payload = self.get("?filter=near&limit=5")
        self.assertEqual([r["severity"] for r in payload["warnings"]["rows"]], [2])
        _, _, payload = self.get("?filter=low&limit=1")
        self.assertEqual([r["productName"] for r in payload["warnings"]["rows"]], ["Vật tư tồn thấp"])
        _, _, payload = self.get("?limit=500")
        self.assertEqual(len(payload["warnings"]["rows"]), 3)

    def test_invalid_query_parameters_are_400(self):
        for query in (
            "?filter=bogus", "?filter=", "?limit=0", "?limit=501", "?limit=abc",
            "?limit=", "?limit=2.5", "?limit=-3",
        ):
            with self.subTest(query=query):
                status, _, payload = self.get(query)
                self.assertEqual(status, 400)
                self.assertFalse(payload["success"])
                self.assertTrue(payload["message"])

    def test_database_error_is_reported_without_internal_details(self):
        def broken_factory():
            raise sqlite3.OperationalError(r"database is locked: C:\Users\secret\pharm.db")

        harness = Harness(self, build_router(broken_factory), self.web_root)
        harness.login()
        with self.assertLogs("webapp.routing", level="ERROR"):
            status, _, payload = harness.json("GET", "/api/dashboard")
        self.assertEqual(status, 500)
        self.assertEqual(payload, {"success": False, "message": "Lỗi hệ thống"})

    def test_hostile_text_survives_the_json_round_trip(self):
        self.add_product(5, HOSTILE_NAME, "L-<b>", -5, 7)
        _, _, payload = self.get("?filter=expired&limit=500")
        names = [row["productName"] for row in payload["warnings"]["rows"]]
        self.assertIn(HOSTILE_NAME, names)

    def test_database_connection_is_closed_after_each_request(self):
        opened = []

        def tracking_factory():
            db = DB(self.db_path)
            opened.append(db)
            return db

        harness = Harness(self, build_router(tracking_factory), self.web_root)
        harness.login()
        self.assertEqual(harness.json("GET", "/api/dashboard")[0], 200)
        self.assertEqual(len(opened), 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            opened[0].conn.execute("SELECT 1")
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_webapp_dashboard.DashboardApiTests -v 2>&1 | tail -6`
Expected: `ModuleNotFoundError: No module named 'webapp.app'`.

- [ ] **Step 3: Cài đặt**

Tạo `webapp/api/__init__.py`:

```python
# -*- coding: utf-8 -*-
"""Các endpoint HTTP của backend web."""
```

Tạo `webapp/api/dashboard.py`:

```python
# -*- coding: utf-8 -*-
"""GET /api/dashboard: dữ liệu màn hình Tổng quan (chỉ đọc, scope local)."""

from __future__ import annotations

from webapp.routing import SCOPE_LOCAL, HttpError, Request, Response, Router, json_response
from webapp.services.dashboard import DEFAULT_LIMIT, build_dashboard_payload, validate_dashboard_params


def make_handler(db_factory):
    def handler(request: Request) -> Response:
        flt = request.query.get("filter", "all")
        limit = DEFAULT_LIMIT
        raw_limit = request.query.get("limit")
        if raw_limit is not None:
            try:
                limit = int(raw_limit)
            except ValueError:
                raise HttpError(400, "Tham số limit phải là số nguyên")
        try:
            validate_dashboard_params(flt, limit)
        except ValueError as exc:
            raise HttpError(400, str(exc))

        db = db_factory()
        try:
            payload = build_dashboard_payload(db, flt=flt, limit=limit)
        finally:
            db.conn.close()
        payload["success"] = True
        return json_response(payload)

    return handler


def register(router: Router, db_factory) -> None:
    router.add("GET", "/api/dashboard", make_handler(db_factory), scopes=(SCOPE_LOCAL,))
```

Tạo `webapp/app.py`:

```python
# -*- coding: utf-8 -*-
"""Ghép các endpoint thành một Router."""

from __future__ import annotations

from webapp.api import dashboard as dashboard_api
from webapp.routing import Router


def build_router(db_factory) -> Router:
    """``db_factory``: hàm không tham số trả về một ``DB`` mới (mỗi request một kết nối)."""
    router = Router()
    dashboard_api.register(router, db_factory)
    return router
```

- [ ] **Step 4: Chạy test để thấy đạt**

Run: `py -3.10 -m unittest test_webapp_dashboard -v 2>&1 | tail -6`
Expected: `OK` (cả lớp service và lớp API).

- [ ] **Step 5: Chạy toàn bộ test backend đã có để chắc không lệch**

Run: `py -3.10 -m unittest test_http_limits test_webapp_routing test_webapp_local_auth test_webapp_static test_webapp_listener test_webapp_dashboard test_ui_dashboard test_mobile_http_hardening 2>&1 | tail -5`
Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add webapp/api/__init__.py webapp/api/dashboard.py webapp/app.py test_webapp_dashboard.py
git commit -F - <<'EOF'
Add /api/dashboard endpoint (read-only, local scope)

Validates filter/limit before touching the database, opens and closes one
SQLite connection per request, and reports failures as a generic 500 that
never leaks internal paths or messages.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 9: Điểm vào `quanly_web.py`, kiểm tra WebView2 và trang tạm

**Files:**
- Tạo: `webapp/runtime.py`, `quanly_web.py`, `run_web.bat`, `web/index.html` (trang tạm, Task 11 thay thế)
- Sửa: `requirements.txt` (thêm `pywebview`), `.gitignore` (thêm `build_web/`)
- Test: `test_webapp_runtime.py`, `test_quanly_web.py`

**Interfaces:**
- Consumes: Task 1 (phiên bản pywebview đã kiểm chứng, đọc trong `docs/superpowers/plans/2026-10-01-web-ui-p1-spike-result.md`), Task 7 (`LocalListener`), Task 8 (`build_router`), `config.DB_PATH`, `database.DB`.
- Produces (dùng ở Task 12, 13): `webapp.runtime.app_root() -> Path` (thư mục chứa `web/`: gốc repo khi chạy mã nguồn, `sys._MEIPASS` khi đã đóng gói); `webapp.runtime.webview2_runtime_version(winreg_module=None) -> str | None`; `quanly_web.create_listener(db_path=None) -> LocalListener`; `quanly_web.run_serve_only(listener) -> int`; `quanly_web.run_window(listener, on_ready=None) -> int` (`on_ready(window) -> int | None` chạy trong luồng của pywebview sau khi cửa sổ sẵn sàng; mã trả về là mã thoát; cửa sổ được đóng sau khi `on_ready` kết thúc); `quanly_web.build_parser()`; `quanly_web.main(argv=None) -> int`; hằng `quanly_web.WEBVIEW2_HELP`.

- [ ] **Step 1: Viết test thất bại cho `runtime`**

Tạo `test_webapp_runtime.py`:

```python
# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from webapp.runtime import app_root, webview2_runtime_version

GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WOW64 = r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\\" + GUID
NATIVE = r"SOFTWARE\Microsoft\EdgeUpdate\Clients\\" + GUID


class _Key:
    def __init__(self, ident):
        self.ident = ident

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeWinreg:
    HKEY_LOCAL_MACHINE = "HKLM"
    HKEY_CURRENT_USER = "HKCU"

    def __init__(self, values):
        self.values = values

    def OpenKey(self, hive, path):
        if (hive, path) not in self.values:
            raise FileNotFoundError(path)
        return _Key((hive, path))

    def QueryValueEx(self, key, name):
        assert name == "pv"
        return self.values[key.ident], 1


class RuntimeTests(unittest.TestCase):
    def test_app_root_in_source_mode_contains_the_web_directory(self):
        self.assertTrue((app_root() / "web").is_dir())

    def test_app_root_when_frozen_uses_the_pyinstaller_bundle_dir(self):
        bundle = tempfile.gettempdir()
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "_MEIPASS", bundle, create=True):
            self.assertEqual(app_root(), Path(bundle))

    def test_webview2_version_is_found_in_the_first_matching_location(self):
        fake = FakeWinreg({("HKLM", WOW64): "154.0.4258.37"})
        self.assertEqual(webview2_runtime_version(fake), "154.0.4258.37")

    def test_webview2_version_falls_back_to_other_locations(self):
        self.assertEqual(webview2_runtime_version(FakeWinreg({("HKLM", NATIVE): "120.0.1"})), "120.0.1")
        self.assertEqual(webview2_runtime_version(FakeWinreg({("HKCU", NATIVE): "119.0.2"})), "119.0.2")

    def test_missing_or_placeholder_version_means_not_installed(self):
        self.assertIsNone(webview2_runtime_version(FakeWinreg({})))
        self.assertIsNone(webview2_runtime_version(FakeWinreg({("HKLM", WOW64): "0.0.0.0"})))
        self.assertIsNone(webview2_runtime_version(FakeWinreg({("HKLM", WOW64): ""})))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_webapp_runtime -v 2>&1 | tail -4`
Expected: `ModuleNotFoundError: No module named 'webapp.runtime'`.

- [ ] **Step 3: Tạo `webapp/runtime.py` và trang tạm `web/index.html`**

Tạo `webapp/runtime.py`:

```python
# -*- coding: utf-8 -*-
"""Tiện ích môi trường chạy: thư mục gốc ứng dụng và phát hiện WebView2 Runtime."""

from __future__ import annotations

import sys
from pathlib import Path

WEBVIEW2_CLIENT_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
_REGISTRY_LOCATIONS = (
    ("HKEY_LOCAL_MACHINE", r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID),
    ("HKEY_LOCAL_MACHINE", r"SOFTWARE\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID),
    ("HKEY_CURRENT_USER", r"SOFTWARE\Microsoft\EdgeUpdate\Clients\\" + WEBVIEW2_CLIENT_GUID),
)


def app_root() -> Path:
    """Thư mục chứa ``web/``: gốc repo khi chạy mã nguồn, bundle PyInstaller khi đã đóng gói."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def webview2_runtime_version(winreg_module=None):
    """Trả về chuỗi phiên bản WebView2 Runtime đã cài, hoặc None nếu chưa có."""
    if winreg_module is None:
        try:
            import winreg as winreg_module
        except ImportError:  # không phải Windows
            return None
    for hive_name, path in _REGISTRY_LOCATIONS:
        hive = getattr(winreg_module, hive_name)
        try:
            with winreg_module.OpenKey(hive, path) as key:
                value, _ = winreg_module.QueryValueEx(key, "pv")
        except OSError:
            continue
        if value and value != "0.0.0.0":
            return str(value)
    return None
```

Tạo `web/index.html` (trang tạm để cổng cục bộ có gì đó phục vụ; Task 11 thay bằng giao diện thật):

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>Quản lý kho 2026</title>
</head>
<body>
  <p>Giao diện web đang được xây dựng.</p>
</body>
</html>
```

- [ ] **Step 4: Chạy test `runtime` để thấy đạt**

Run: `py -3.10 -m unittest test_webapp_runtime -v 2>&1 | tail -5`
Expected: `OK` (5 test).

- [ ] **Step 5: Viết test thất bại cho `quanly_web`**

Tạo `test_quanly_web.py`:

```python
# -*- coding: utf-8 -*-
import contextlib
import http.client
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import quanly_web


class CreateListenerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.listener = quanly_web.create_listener(os.path.join(self.tmp.name, "web.db"))
        self.listener.start()
        self.addCleanup(self.listener.stop)

    def get(self, path, cookie=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.listener.port, timeout=10)
        try:
            conn.request("GET", path, headers={"Cookie": cookie} if cookie else {})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_boot_url_logs_in_and_the_dashboard_api_answers_from_the_given_database(self):
        boot_path = self.listener.boot_url().split(str(self.listener.port), 1)[1]
        status, headers, _ = self.get(boot_path)
        self.assertEqual(status, 302)
        cookie = headers["Set-Cookie"].split(";", 1)[0]

        status, _, body = self.get("/api/dashboard", cookie=cookie)
        payload = json.loads(body.decode("utf-8"))
        self.assertEqual(status, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["cards"]["productCount"], 0)

        status, _, body = self.get("/", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertIn(b"<!doctype html", body.lower())


class WindowTests(unittest.TestCase):
    def test_missing_webview2_prints_help_and_returns_1(self):
        listener = mock.Mock()
        stderr = io.StringIO()
        with mock.patch.object(quanly_web, "webview2_runtime_version", return_value=None), \
                contextlib.redirect_stderr(stderr):
            code = quanly_web.run_window(listener)
        self.assertEqual(code, 1)
        self.assertIn("WebView2", stderr.getvalue())
        self.assertIn("go.microsoft.com/fwlink/p/?LinkId=2124703", stderr.getvalue())
        listener.start.assert_not_called()


class ParserTests(unittest.TestCase):
    def test_serve_flag(self):
        self.assertFalse(quanly_web.build_parser().parse_args([]).serve)
        self.assertTrue(quanly_web.build_parser().parse_args(["--serve"]).serve)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_quanly_web -v 2>&1 | tail -4`
Expected: `ModuleNotFoundError: No module named 'quanly_web'`.

- [ ] **Step 7: Tạo `quanly_web.py`**

```python
# -*- coding: utf-8 -*-
"""Điểm vào giao diện web: cổng cục bộ + cửa sổ pywebview (Edge WebView2).

Bản Tkinter vẫn là ``quanly_xnt.py``; hai bản dùng chung ``pharm.db``.
"""

from __future__ import annotations

import argparse
import sys
import time

from webapp.runtime import app_root, webview2_runtime_version

WINDOW_TITLE = "Quản lý kho 2026"
WEBVIEW2_HELP = (
    "Không tìm thấy Microsoft Edge WebView2 Runtime, cần có để hiển thị giao diện.\n"
    "Hãy cài bản 'Evergreen Bootstrapper' tại https://go.microsoft.com/fwlink/p/?LinkId=2124703 "
    "rồi chạy lại ứng dụng."
)


def create_listener(db_path=None):
    """Dựng router + phiên + listener; mỗi request mở một kết nối SQLite riêng."""
    from config import DB_PATH
    from database import DB
    from webapp.app import build_router
    from webapp.auth import LocalSession
    from webapp.listener import LocalListener

    path = db_path or DB_PATH
    router = build_router(lambda: DB(path))
    return LocalListener(router, LocalSession(), app_root() / "web")


def run_serve_only(listener) -> int:
    """Chế độ phát triển: chỉ mở cổng cục bộ, in địa chỉ boot dùng một lần."""
    listener.start()
    print("Giao diện web đang chạy ở chế độ phát triển (không mở cửa sổ).", flush=True)
    print("Mở địa chỉ sau trong trình duyệt (chỉ dùng được một lần):", flush=True)
    print(listener.boot_url(), flush=True)
    print("Nhấn Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
    return 0


def run_window(listener, on_ready=None) -> int:
    """Mở cửa sổ pywebview. ``on_ready(window)`` (tùy chọn) chạy sau khi cửa sổ sẵn sàng;
    giá trị trả về là mã thoát và cửa sổ được đóng ngay sau đó."""
    if webview2_runtime_version() is None:
        print(WEBVIEW2_HELP, file=sys.stderr)
        return 1
    try:
        import webview
    except ImportError:
        print("Thiếu thư viện pywebview. Hãy chạy: pip install -r requirements.txt", file=sys.stderr)
        return 1

    listener.start()
    # text_select=True: với False (mặc định) pywebview chèn một <style> nội tuyến để tắt bôi chọn chữ,
    # bị CSP chặt của giao diện chặn; cho bôi chọn cũng tiện sao chép số lô, tên thuốc từ bảng.
    window = webview.create_window(
        WINDOW_TITLE, listener.boot_url(), width=1366, height=800, min_size=(1024, 640),
        text_select=True,
    )
    outcome = {"code": 0}
    callback = None
    if on_ready is not None:
        def callback(win):
            try:
                outcome["code"] = int(on_ready(win) or 0)
            finally:
                win.destroy()
    try:
        webview.start(callback, window if callback else None, gui="edgechromium", private_mode=True, debug=False)
    except Exception as exc:
        print(f"Không mở được cửa sổ giao diện: {exc}\n{WEBVIEW2_HELP}", file=sys.stderr)
        return 1
    return outcome["code"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quản lý kho 2026 (giao diện web)")
    parser.add_argument(
        "--serve", action="store_true",
        help="chỉ mở cổng cục bộ và in địa chỉ boot một lần (phát triển/kiểm thử), không mở cửa sổ",
    )
    return parser


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    listener = create_listener()
    try:
        if args.serve:
            return run_serve_only(listener)
        return run_window(listener)
    finally:
        listener.stop()


if __name__ == "__main__":
    sys.exit(main())
```

**Ghi chú thực thi (phát hiện ở Task 12):** smoke thật trong WebView2 cho thấy pywebview 6.2.1 chèn một `<style>` nội tuyến khi `text_select=False` (mặc định), bị CSP chặt chặn. Vì vậy `create_window` truyền `text_select=True` (đã khóa bằng test `test_window_allows_text_selection_so_pywebview_injects_no_inline_style` trong `test_quanly_web.py`).

- [ ] **Step 8: Chạy test để thấy đạt**

Run: `py -3.10 -m unittest test_webapp_runtime test_quanly_web -v 2>&1 | tail -6`
Expected: `OK`.

- [ ] **Step 9: Thêm `run_web.bat`, ghim `pywebview`, cập nhật `.gitignore`**

Tạo `run_web.bat` (bản sao của `run.bat`, chỉ đổi điểm vào):

```bat
@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call setup.bat
    if errorlevel 1 (
        exit /b 1
    )
)

if not exist ".venv\requirements.installed" (
    call setup.bat
    if errorlevel 1 exit /b 1
) else (
    fc /b "requirements.txt" ".venv\requirements.installed" >nul
    if errorlevel 1 (
        call setup.bat
        if errorlevel 1 exit /b 1
    )
)

echo Starting Quan Ly Kho (web UI)...
".venv\Scripts\python.exe" quanly_web.py

endlocal
```

Ghim `pywebview`: lấy số phiên bản đã kiểm chứng trong `docs/superpowers/plans/2026-10-01-web-ui-p1-spike-result.md` (dòng "Phiên bản pywebview") và thêm vào **cuối** `requirements.txt` một dòng `pywebview==<phiên bản đó>`. Ví dụ nếu bản kiểm chứng là `5.3.2` thì dòng là `pywebview==5.3.2`.

Thêm vào cuối `.gitignore`:

```
# Build giao diện web
build_web/
```

- [ ] **Step 10: Kiểm tra thủ công bằng `--serve` (không cần cửa sổ)**

Dựng venv theo đúng pin để có `pywebview`, rồi chạy chế độ phát triển với DB tạm:

```bash
py -3.10 -m venv "$TEMP/qlk_venv"
"$TEMP/qlk_venv/Scripts/python.exe" -m pip install -r requirements.txt
export QLK_PY="$TEMP/qlk_venv/Scripts/python.exe"
$QLK_PY quanly_web.py --serve
```

(chạy lệnh cuối ở nền). Đọc địa chỉ `http://127.0.0.1:<port>/boot/<token>` từ đầu ra, rồi:

```bash
URL="<dán địa chỉ boot vừa in>"
BASE="${URL%%/boot/*}"
curl -s -i -c "$TEMP/qlk_jar.txt" "$URL" | head -12          # Expected: HTTP/1.0 302 ... Set-Cookie: qlk_session=...; HttpOnly; SameSite=Strict
curl -s -b "$TEMP/qlk_jar.txt" "$BASE/api/dashboard" | head -c 300    # Expected: {"warningDays": 90, ... "success": true}
curl -s -o /dev/null -w "%{http_code}\n" "$BASE/api/dashboard"        # Expected: 401 (không cookie)
curl -s -i -c "$TEMP/qlk_jar2.txt" "$URL" | head -1                   # Expected: HTTP/1.0 401 (token đã dùng)
```

Dừng tiến trình nền khi xong. Sau đó mở cửa sổ thật một lần để xác nhận pywebview chạy: `$QLK_PY quanly_web.py`. Expected: cửa sổ "Quản lý kho 2026" hiện dòng "Giao diện web đang được xây dựng."; đóng cửa sổ thì tiến trình thoát (mã 0).

- [ ] **Step 11: Commit**

```bash
git add webapp/runtime.py quanly_web.py run_web.bat web/index.html requirements.txt .gitignore test_webapp_runtime.py test_quanly_web.py
git commit -F - <<'EOF'
Add quanly_web entry point (pywebview window, --serve mode)

Opens the loopback listener and an Edge WebView2 window via pywebview.
Missing WebView2 prints Vietnamese install instructions and exits 1.
Adds pywebview to requirements and a placeholder index page.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 10: Token thiết kế, CSS nền, thư viện đặt sẵn, tiện ích JS và test chính sách

**Files:**
- Tạo: `web/css/tokens.css`, `web/css/base.css`, `web/css/components.css`, `web/js/vendor/htm-preact.js`, `web/js/vendor/LICENSE-htm.txt`, `web/js/vendor/LICENSE-preact.txt`, `web/js/vendor/VENDOR.md`, `web/js/format.js`, `web/js/api.js`, `web/js/nav.js`
- Test: `test_web_assets_policy.py`

**Interfaces:**
- Consumes: `ui_design.COLORS`, `ui_design.NAV_ITEMS` (đối chiếu parity).
- Produces (dùng ở Task 11): `format.js` xuất `formatDate(value)` (`2026-10-01` → `01-10-2026`), `formatDateTime(value)` (`2026-10-01 09:30:00` → `01-10-2026 09:30:00`, khớp `date_utils.format_datetime_display`), `formatCount(value)` (định dạng `vi-VN`), `formatQty(value)` (số bỏ phần thập phân thừa); `api.js` xuất `ApiError` (thuộc tính `status`, `authRequired`) và `getJson(path, params = {})` (gọi `fetch` cùng origin, ném `ApiError` khi `!response.ok` hoặc `success === false`); `nav.js` xuất `NAV_ITEMS` (11 mục `{id, label, tab, hotkey, live}`, chỉ `dashboard` có `live: true`); `vendor/htm-preact.js` xuất `html`, `render`, `Component`; CSS định nghĩa token và class BEM dùng ở Task 11 (`.shell`, `.nav`, `.btn`, `.panel`, `.table`, `.badge`, `.chip`, `.stat-list`, `.dot`, `.state`, `.toast`, `.info-list`, `.page-head`, `.dashboard__grid`).

- [ ] **Step 1: Viết test chính sách (thất bại)**

Tạo `test_web_assets_policy.py`:

```python
# -*- coding: utf-8 -*-
"""Kiểm tra tĩnh cho web/: không có API nguy hiểm, mọi tham chiếu đều tồn tại,
token màu đạt WCAG AA và khớp bảng màu Tkinter, điều hướng khớp ui_design."""

import hashlib
import re
import unittest
from pathlib import Path

from ui_design import COLORS, NAV_ITEMS

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
VENDOR_DIR = WEB / "js" / "vendor"
TOKENS = WEB / "css" / "tokens.css"


def own_files(*suffixes):
    """File do dự án viết (không gồm thư viện đặt sẵn trong js/vendor)."""
    return [
        path for path in sorted(WEB.rglob("*"))
        if path.is_file() and path.suffix in suffixes and VENDOR_DIR not in path.parents
    ]


def read(path):
    return path.read_text(encoding="utf-8")


BANNED = {
    "innerHTML": r"innerHTML",
    "outerHTML": r"outerHTML",
    "insertAdjacentHTML": r"insertAdjacentHTML",
    "document.write": r"document\.write",
    "dangerouslySetInnerHTML": r"dangerouslySetInnerHTML",
    "eval(": r"\beval\s*\(",
    "new Function": r"new\s+Function\b",
    "Function(": r"(?<![\w.])Function\s*\(",
    "thuộc tính sự kiện nội tuyến (on*=)": r"\son[a-z]+\s*=\s*[\"']",
    "thuộc tính style nội tuyến": r"\sstyle\s*=\s*[\"']",
    "javascript: URL": r"javascript:",
}


def exported_names(source):
    names = set()
    for match in re.finditer(r"export\s+(?:async\s+)?function\s+(\w+)", source):
        names.add(match.group(1))
    for match in re.finditer(r"export\s+(?:class|const|let|var)\s+(\w+)", source):
        names.add(match.group(1))
    for match in re.finditer(r"export\s*\{([^}]*)\}", source):
        for item in match.group(1).split(","):
            item = item.strip()
            if item:
                names.add(item.split(" as ")[-1].strip())
    return names


def parse_tokens():
    raw = dict(re.findall(r"--([a-z0-9-]+)\s*:\s*([^;]+);", read(TOKENS)))

    def resolve(name):
        value = raw[name].strip()
        alias = re.fullmatch(r"var\(--([a-z0-9-]+)\)", value)
        return resolve(alias.group(1)) if alias else value.upper()

    return {name: resolve(name) for name in raw}


def luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class ForbiddenApiTests(unittest.TestCase):
    def test_no_dangerous_apis_or_inline_handlers_in_own_files(self):
        problems = []
        for path in own_files(".js", ".html", ".css"):
            text = read(path)
            for label, pattern in BANNED.items():
                if re.search(pattern, text):
                    problems.append(f"{path.relative_to(WEB)}: {label}")
        self.assertEqual(problems, [])

    def test_html_has_no_inline_script_or_style_blocks(self):
        problems = []
        for path in own_files(".html"):
            text = read(path)
            if re.search(r"<script(?![^>]*\ssrc=)[^>]*>", text):
                problems.append(f"{path.relative_to(WEB)}: <script> nội tuyến")
            if re.search(r"<style\b", text):
                problems.append(f"{path.relative_to(WEB)}: <style> nội tuyến")
        self.assertEqual(problems, [])


class ReferenceTests(unittest.TestCase):
    def test_every_relative_import_and_asset_reference_resolves(self):
        missing = []
        for path in own_files(".js"):
            text = read(path)
            for spec in re.findall(r"\bfrom\s+[\"']([^\"']+)[\"']", text) + re.findall(
                r"\bimport\s+[\"']([^\"']+)[\"']", text
            ):
                if spec.startswith("."):
                    target = (path.parent / spec).resolve()
                    if not target.is_file():
                        missing.append(f"{path.relative_to(WEB)} -> {spec}")
        for path in own_files(".html"):
            for ref in re.findall(r"(?:src|href)=\"([^\"]+)\"", read(path)):
                if ref.startswith(("http:", "https:", "#", "data:")):
                    missing.append(f"{path.relative_to(WEB)} -> {ref} (tham chiếu ngoài)")
                    continue
                target = (WEB / ref.lstrip("/")).resolve() if ref.startswith("/") else (path.parent / ref).resolve()
                if not target.is_file():
                    missing.append(f"{path.relative_to(WEB)} -> {ref}")
        self.assertEqual(missing, [])

    def test_named_imports_exist_in_the_target_module(self):
        problems = []
        for path in own_files(".js"):
            for names, spec in re.findall(
                r"import\s*\{([^}]*)\}\s*from\s*[\"']([^\"']+)[\"']", read(path)
            ):
                if not spec.startswith("."):
                    continue
                target = (path.parent / spec).resolve()
                if VENDOR_DIR in target.parents or not target.is_file():
                    continue
                available = exported_names(read(target))
                for item in names.split(","):
                    name = item.strip().split(" as ")[0].strip()
                    if name and name not in available:
                        problems.append(f"{path.relative_to(WEB)}: '{name}' không được xuất bởi {spec}")
        self.assertEqual(problems, [])

    def test_css_only_uses_defined_tokens(self):
        defined = set(parse_tokens())
        problems = []
        for path in own_files(".css"):
            for name in re.findall(r"var\(--([a-z0-9-]+)\)", read(path)):
                if name not in defined:
                    problems.append(f"{path.relative_to(WEB)}: var(--{name}) chưa định nghĩa")
        self.assertEqual(problems, [])


class VendorTests(unittest.TestCase):
    def test_vendored_library_matches_its_recorded_hash_and_exports_what_the_app_uses(self):
        record = read(VENDOR_DIR / "VENDOR.md")
        match = re.search(r"^htm-preact\.js\s+sha256:\s*([0-9a-f]{64})\s*$", record, re.M)
        self.assertIsNotNone(match, "VENDOR.md phải có dòng 'htm-preact.js sha256: <64 hex>'")
        data = (VENDOR_DIR / "htm-preact.js").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(data).hexdigest(), match.group(1))
        available = exported_names(data.decode("utf-8"))
        for name in ("html", "render", "Component"):
            self.assertIn(name, available)

    def test_licenses_are_shipped_with_the_vendored_library(self):
        for name in ("LICENSE-htm.txt", "LICENSE-preact.txt"):
            self.assertGreater((VENDOR_DIR / name).stat().st_size, 200, name)


class DesignTokenTests(unittest.TestCase):
    def test_palette_matches_tkinter_tokens_except_the_documented_muted_text(self):
        tokens = parse_tokens()
        for key, value in COLORS.items():
            name = key.replace("_", "-")
            expected = "#5F6F85" if key == "text_muted" else value.upper()
            with self.subTest(token=name):
                self.assertEqual(tokens[name], expected)

    def test_text_and_background_pairs_meet_wcag_aa(self):
        tokens = parse_tokens()
        pairs = [
            ("text", "surface"), ("text", "canvas"), ("text", "selected"), ("text", "row-near-bg"),
            ("text-muted", "surface"), ("text-muted", "canvas"), ("text-muted", "surface-subdued"),
            ("text-subtle", "surface"), ("text-subtle", "canvas"), ("text-subtle", "surface-subdued"),
            ("on-primary", "primary"), ("on-primary", "primary-hover"),
            ("primary", "nav-active-bg"), ("primary", "canvas"), ("primary", "surface"),
            ("success", "success-bg"), ("success", "surface"),
            ("warning", "warning-bg"), ("warning", "surface"), ("warning", "row-near-bg"),
            ("danger", "danger-bg"), ("danger", "surface"),
            ("info", "info-bg"), ("info", "surface"),
        ]
        failures = []
        for fg, bg in pairs:
            ratio = contrast(tokens[fg], tokens[bg])
            if ratio < 4.5:
                failures.append(f"--{fg} trên --{bg}: {ratio:.2f}:1")
        self.assertEqual(failures, [])


class NavigationTests(unittest.TestCase):
    def test_nav_js_matches_tkinter_nav_items_and_only_the_dashboard_is_live(self):
        text = read(WEB / "js" / "nav.js")
        items = re.findall(
            r"\{\s*id:\s*\"([^\"]+)\",\s*label:\s*\"([^\"]+)\",\s*tab:\s*\"([^\"]+)\",\s*"
            r"hotkey:\s*\"([^\"]+)\",\s*live:\s*(true|false)\s*\}",
            text,
        )
        self.assertEqual([item[:4] for item in items], list(NAV_ITEMS))
        self.assertEqual([item[0] for item in items if item[4] == "true"], ["dashboard"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_web_assets_policy -v 2>&1 | tail -20`
Expected: lỗi `FileNotFoundError` trên `web/css/tokens.css` / `web/js/vendor/VENDOR.md` / `web/js/nav.js` (các file chưa tồn tại). Các test không đọc file đó (quét cấm API trên các file hiện có) có thể đã đạt.

- [ ] **Step 3: Đặt thư viện Preact + htm vào repo**

```bash
mkdir -p web/js/vendor
curl -fsSL -o web/js/vendor/htm-preact.js https://cdn.jsdelivr.net/npm/htm@3.1.1/preact/standalone.module.js
curl -fsSL -o web/js/vendor/LICENSE-htm.txt https://cdn.jsdelivr.net/npm/htm@3.1.1/LICENSE
curl -fsSL -o web/js/vendor/LICENSE-preact.txt https://cdn.jsdelivr.net/npm/preact@10/LICENSE
wc -c web/js/vendor/*
grep -o "export *{[^}]*}" web/js/vendor/htm-preact.js | head -2
```

Expected: ba file có kích thước > 0 (thư viện vài chục KB, giấy phép vài KB); dòng `export{...}` cuối liệt kê tên có chứa `html`, `render` và `Component` (có thể dạng `n as html`). **Nếu thiếu một trong ba tên, dừng lại và báo cáo**, không tự đổi thư viện.

Tính hash đã chuẩn hóa xuống dòng và ghi vào `web/js/vendor/VENDOR.md`:

```bash
HASH=$(py -3.10 -c "import hashlib; print(hashlib.sha256(open('web/js/vendor/htm-preact.js','rb').read().replace(b'\r\n', b'\n')).hexdigest())")
cat > web/js/vendor/VENDOR.md <<EOF
# Thư viện đặt sẵn

Không chỉnh sửa tay các file trong thư mục này. Nâng cấp = tải bản mới, cập nhật hash, chạy lại test.

htm-preact.js sha256: $HASH

Nguồn: https://cdn.jsdelivr.net/npm/htm@3.1.1/preact/standalone.module.js (htm 3.1.1, đóng gói kèm Preact 10.x).
Giấy phép: LICENSE-htm.txt (htm), LICENSE-preact.txt (Preact, MIT).
Hash tính trên nội dung đã chuẩn hóa xuống dòng về LF (để không phụ thuộc cấu hình CRLF của Git).
EOF
cat web/js/vendor/VENDOR.md
```

- [ ] **Step 4: Tạo token và CSS**

Tạo `web/css/tokens.css`:

```css
/* Token thiết kế (P1).
   Lớp 1: giá trị nguyên thủy. Lớp 2: ngữ nghĩa. Component chỉ dùng lớp 2.
   Giá trị chuyển 1:1 từ ui_design.py; ngoại lệ duy nhất: --text-muted là #5F6F85
   (thay cho #64748B) để đạt WCAG AA 4,5:1 trên nền canvas và surface-subdued. */
:root {
  /* Lớp 1: nguyên thủy */
  --white: #FFFFFF;
  --gray-50: #F8FAFC;
  --gray-100: #F3F6F9;
  --gray-150: #EDF2F7;
  --gray-200: #E2E8F0;
  --gray-300: #D1D9E2;
  --slate-550: #5F6F85;
  --slate-600: #475569;
  --slate-950: #0B1C30;
  --navy-700: #0D3B66;
  --navy-600: #1B4D7E;
  --teal-800: #164E63;
  --green-800: #166534;
  --green-100: #DCFCE7;
  --green-200: #BBF7D0;
  --amber-700: #B45309;
  --amber-100: #FEF3C7;
  --amber-200: #FDE68A;
  --amber-50: #FFF9E8;
  --red-700: #B91C1C;
  --red-100: #FEE2E2;
  --red-200: #FECACA;
  --blue-700: #1D4ED8;
  --blue-100: #DBEAFE;
  --blue-200: #BFDBFE;
  --sky-100: #E0F2FE;
  --periwinkle-100: #DCE9FF;
  --periwinkle-150: #D3E4FE;

  /* Lớp 2: ngữ nghĩa */
  --canvas: var(--gray-100);
  --surface: var(--white);
  --surface-subdued: var(--gray-150);
  --surface-hover: var(--gray-50);
  --border: var(--gray-300);
  --border-soft: var(--gray-200);
  --text: var(--slate-950);
  --text-muted: var(--slate-550);
  --text-subtle: var(--slate-600);
  --primary: var(--navy-700);
  --primary-hover: var(--navy-600);
  --on-primary: var(--white);
  --secondary: var(--teal-800);
  --success: var(--green-800);
  --success-bg: var(--green-100);
  --success-border: var(--green-200);
  --warning: var(--amber-700);
  --warning-bg: var(--amber-100);
  --warning-border: var(--amber-200);
  --danger: var(--red-700);
  --danger-bg: var(--red-100);
  --danger-border: var(--red-200);
  --info: var(--blue-700);
  --info-bg: var(--blue-100);
  --info-border: var(--blue-200);
  --selected: var(--sky-100);
  --nav-active-bg: var(--periwinkle-100);
  --nav-active-hover: var(--periwinkle-150);
  --row-near-bg: var(--amber-50);

  /* Khoảng cách, chữ, hình khối */
  --space-xs: 0.25rem;
  --space-sm: 0.375rem;
  --space-md: 0.5rem;
  --space-lg: 0.75rem;
  --space-xl: 1rem;
  --space-2xl: 1.25rem;
  --table-row: 2.125rem;
  --input-height: 2rem;
  --touch-target: 2.75rem;
  --radius: 0.375rem;
  --font-ui: "Segoe UI", system-ui, sans-serif;
  --font-mono: Consolas, "Courier New", monospace;
  --fs-display: 1.5rem;
  --fs-headline: 1.125rem;
  --fs-title: 0.9375rem;
  --fs-body: 0.8125rem;
  --fs-compact: 0.75rem;
  --fs-badge: 0.6875rem;
}
```

Tạo `web/css/base.css`:

```css
*, *::before, *::after { box-sizing: border-box; }

html, body { height: 100%; }

body {
  margin: 0;
  background: var(--canvas);
  color: var(--text);
  font-family: var(--font-ui);
  font-size: var(--fs-body);
  line-height: 1.4;
}

h1, h2, p, ul { margin: 0; padding: 0; }
ul { list-style: none; }
button { font: inherit; color: inherit; }
a { color: inherit; }

:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }

kbd { font-family: var(--font-ui); font-size: var(--fs-badge); color: var(--text-muted); }

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

Tạo `web/css/components.css`:

```css
/* Khung ứng dụng */
.shell { display: grid; grid-template-columns: 11rem minmax(0, 1fr); min-height: 100vh; }
.shell__side { background: var(--canvas); border-right: 1px solid var(--border-soft); padding: var(--space-lg) var(--space-md); }
.shell__brand { color: var(--primary); font-size: var(--fs-title); font-weight: 700; padding: var(--space-xs) var(--space-md) var(--space-lg); }
.shell__nav { display: flex; flex-direction: column; gap: 0.125rem; }
.shell__main { min-width: 0; padding: var(--space-lg) var(--space-xl); }

.nav { display: flex; align-items: center; justify-content: space-between; gap: var(--space-md); padding: 0.4rem var(--space-lg); border-radius: var(--radius); color: var(--text-subtle); text-decoration: none; white-space: nowrap; }
.nav:hover { background: var(--surface-subdued); color: var(--text); }
.nav--active, .nav--active:hover { background: var(--nav-active-bg); color: var(--primary); font-weight: 700; }
.nav--active kbd { color: var(--primary); }
.nav--off, .nav--off:hover { background: transparent; color: var(--text-muted); cursor: default; }
.nav small { background: var(--surface-subdued); border-radius: 999px; color: var(--text-muted); font-size: var(--fs-badge); padding: 0.0625rem 0.4rem; }

/* Đầu trang và nút */
.page-head { align-items: flex-start; display: flex; flex-wrap: wrap; gap: var(--space-lg); justify-content: space-between; margin-bottom: var(--space-lg); }
.page-head__title { font-size: var(--fs-headline); font-weight: 700; }
.page-head__sub { color: var(--text-muted); font-size: var(--fs-compact); margin-top: 0.125rem; }
.page-head__actions { display: flex; flex-wrap: wrap; gap: var(--space-sm); }

.btn { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text); cursor: pointer; font-size: var(--fs-compact); font-weight: 600; min-height: var(--input-height); padding: 0.3rem 0.75rem; }
.btn:hover:not(:disabled) { background: var(--surface-subdued); }
.btn--primary { background: var(--primary); border-color: var(--primary); color: var(--on-primary); }
.btn--primary:hover:not(:disabled) { background: var(--primary-hover); }
.btn:disabled { cursor: not-allowed; opacity: 0.55; }

/* Panel */
.panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.panel__head { align-items: center; border-bottom: 1px solid var(--border-soft); display: flex; flex-wrap: wrap; gap: var(--space-md); justify-content: space-between; padding: var(--space-md) var(--space-lg); }
.panel__title { font-size: var(--fs-compact); font-weight: 700; letter-spacing: 0.02em; }
.panel__foot { border-top: 1px solid var(--border-soft); color: var(--text-muted); font-size: var(--fs-compact); padding: var(--space-md) var(--space-lg); }

/* Bảng */
.table-wrap { max-height: 32rem; overflow: auto; }
.table { border-collapse: collapse; width: 100%; }
.table__th { background: var(--surface-subdued); color: var(--text-subtle); font-size: var(--fs-badge); font-weight: 700; letter-spacing: 0.02em; padding: var(--space-sm) var(--space-md); position: sticky; text-align: left; text-transform: uppercase; top: 0; }
.table__td { border-top: 1px solid var(--border-soft); font-size: var(--fs-compact); height: var(--table-row); padding: 0 var(--space-md); }
.table__th--center, .table__td--center { text-align: center; }
.table__th--right, .table__td--right { text-align: right; }
.row--expired .table__td { background: var(--danger-bg); color: var(--danger); }
.row--near .table__td { background: var(--row-near-bg); }
.row--low .table__td { background: var(--surface); }

/* Huy hiệu, chip, danh sách số liệu */
.badge { border-radius: 999px; display: inline-block; font-size: var(--fs-badge); font-weight: 700; padding: 0.0625rem 0.5rem; white-space: nowrap; }
.badge--danger { background: var(--danger-bg); color: var(--danger); }
.badge--warning { background: var(--warning-bg); color: var(--warning); }
.badge--info { background: var(--info-bg); color: var(--info); }
.badge--success { background: var(--success-bg); color: var(--success); }

.chips { display: flex; flex-wrap: wrap; gap: var(--space-sm); }
.chip { background: var(--surface); border: 1px solid var(--border); border-radius: 999px; color: var(--text-subtle); cursor: pointer; font-size: var(--fs-compact); padding: 0.125rem 0.6rem; }
.chip:hover { background: var(--surface-subdued); }
.chip--on, .chip--on:hover { background: var(--primary); border-color: var(--primary); color: var(--on-primary); }

.stat-list__row { align-items: center; border-top: 1px solid var(--border-soft); display: flex; gap: var(--space-md); padding: var(--space-md) var(--space-lg); }
.stat-list__row:first-child { border-top: 0; }
.stat-list__value { font-size: var(--fs-title); margin-left: auto; }
.dot { border-radius: 50%; flex: none; height: 0.5rem; width: 0.5rem; }
.dot--neutral { background: var(--primary); }
.dot--success { background: var(--success); }
.dot--warning { background: var(--warning); }
.dot--danger { background: var(--danger); }

.info-list__row { border-top: 1px solid var(--border-soft); color: var(--text-subtle); padding: var(--space-md) var(--space-lg); }
.info-list__row:first-child { border-top: 0; }
.is-ok { color: var(--success); }
.is-warn { color: var(--warning); }

/* Trạng thái rỗng, lỗi, thông báo */
.state { color: var(--text-subtle); padding: var(--space-2xl) var(--space-xl); text-align: center; }
.state__title { color: var(--text); font-weight: 700; }
.state__hint { color: var(--text-muted); margin-top: var(--space-sm); }
.state--error .state__title { color: var(--danger); }
.state__retry { margin-top: var(--space-lg); }

.toasts { bottom: var(--space-xl); display: grid; gap: var(--space-md); position: fixed; right: var(--space-xl); z-index: 10; }
.toast { background: var(--surface); border: 1px solid var(--border); border-left-width: 4px; border-radius: var(--radius); box-shadow: 0 2px 8px rgba(11, 28, 48, 0.15); max-width: 24rem; padding: var(--space-md) var(--space-lg); }
.toast--danger { border-left-color: var(--danger); }
.toast--info { border-left-color: var(--info); }
.toast--success { border-left-color: var(--success); }

/* Màn hình Tổng quan */
.dashboard__grid { align-items: start; display: grid; gap: var(--space-lg); grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); }
.dashboard__side { display: grid; gap: var(--space-lg); }
.dashboard__note { color: var(--text-muted); font-size: var(--fs-compact); margin-top: var(--space-lg); }
.dashboard__error { background: var(--danger-bg); border-radius: var(--radius); color: var(--danger); margin-bottom: var(--space-lg); padding: var(--space-md) var(--space-lg); }

/* Màn hình hẹp: thanh bên thành thanh ngang cuộn được, cột phải xuống dưới bảng */
@media (max-width: 1023px) {
  .shell { grid-template-columns: minmax(0, 1fr); }
  .shell__side { border-bottom: 1px solid var(--border-soft); border-right: 0; padding: var(--space-md); }
  .shell__nav { flex-direction: row; overflow-x: auto; }
  .dashboard__grid { grid-template-columns: minmax(0, 1fr); }
}

/* Màn hình cảm ứng nhỏ: vùng chạm tối thiểu 44px */
@media (max-width: 640px) {
  .btn, .chip, .nav { min-height: var(--touch-target); }
}
```

- [ ] **Step 5: Tạo tiện ích JS**

Tạo `web/js/format.js`:

```js
// Định dạng hiển thị khớp date_utils.py (DD-MM-YYYY) và bản Tkinter.

export function formatDate(value) {
  const text = String(value || "");
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(text);
  return match ? `${match[3]}-${match[2]}-${match[1]}` : text;
}

export function formatDateTime(value) {
  const text = String(value || "").trim();
  const match = /^(\d{4})-(\d{2})-(\d{2})[ T](.+)$/.exec(text);
  return match ? `${match[3]}-${match[2]}-${match[1]} ${match[4]}` : formatDate(text);
}

export function formatCount(value) {
  return new Intl.NumberFormat("vi-VN").format(Number(value) || 0);
}

export function formatQty(value) {
  const number = Number(value);
  return Number.isFinite(number) ? String(Math.round(number * 10000) / 10000) : "";
}
```

Tạo `web/js/api.js`:

```js
// Gọi API cùng origin. Cookie phiên HttpOnly tự được trình duyệt gửi kèm.

export class ApiError extends Error {
  constructor(status, message, authRequired) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.authRequired = Boolean(authRequired);
  }
}

export async function getJson(path, params = {}) {
  const url = new URL(path, window.location.origin);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, String(value));
  }

  let response;
  try {
    response = await fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } });
  } catch (error) {
    throw new ApiError(0, "Không kết nối được tới ứng dụng", false);
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch (error) {
    payload = null;
  }

  if (!response.ok || !payload || payload.success === false) {
    const message = (payload && payload.message) || `Lỗi ${response.status}`;
    throw new ApiError(response.status, message, response.status === 401 || Boolean(payload && payload.auth_required));
  }
  return payload;
}
```

Tạo `web/js/nav.js` (nhãn và phím tắt chép nguyên từ `ui_design.NAV_ITEMS`; test đối chiếu sẽ phát hiện lệch):

```js
// 11 mục điều hướng, khớp ui_design.NAV_ITEMS. Chỉ "Tổng quan" có bản web trong P1.

export const NAV_ITEMS = [
  { id: "dashboard", label: "▦  Tổng quan", tab: "tab_operations", hotkey: "F4", live: true },
  { id: "products", label: "▤  Danh mục hàng hóa", tab: "tab_products", hotkey: "F1", live: false },
  { id: "purchase", label: "↧  Nhập kho", tab: "tab_purchase", hotkey: "F2", live: false },
  { id: "dispatch", label: "↥  Xuất kho", tab: "tab_dispatch", hotkey: "F3", live: false },
  { id: "stock", label: "⌛  Tồn kho (FEFO)", tab: "tab_stock", hotkey: "F5", live: false },
  { id: "alerts", label: "⚠  Cảnh báo HSD", tab: "tab_alerts", hotkey: "F6", live: false },
  { id: "report", label: "▧  Báo cáo XNT", tab: "tab_report", hotkey: "F7", live: false },
  { id: "temp", label: "♨  Nhiệt độ & độ ẩm", tab: "tab_temp_log", hotkey: "F11", live: false },
  { id: "data", label: "⌘  Công cụ dữ liệu", tab: "tab_backup", hotkey: "F8", live: false },
  { id: "advanced", label: "▥  Báo cáo nâng cao", tab: "tab_advanced_reports", hotkey: "F12", live: false },
  { id: "admin", label: "⚙  Quản trị hệ thống", tab: "tab_mobile", hotkey: "F10", live: false },
];
```

- [ ] **Step 6: Chạy test chính sách để thấy đạt**

Run: `py -3.10 -m unittest test_web_assets_policy -v 2>&1 | tail -20`
Expected: `OK` (10 test). Nếu `test_text_and_background_pairs_meet_wcag_aa` báo cặp nào dưới 4,5:1, **không hạ ngưỡng**: chỉnh giá trị token tương ứng (và ghi vào chú thích đầu `tokens.css`), vì đây là yêu cầu của spec.

- [ ] **Step 7: Commit**

```bash
git add web/css web/js/format.js web/js/api.js web/js/nav.js web/js/vendor test_web_assets_policy.py
git commit -F - <<'EOF'
Add web design tokens, vendored Preact+htm and asset policy tests

Two-layer CSS tokens ported from ui_design.py (muted text darkened to meet
WCAG AA), base/component CSS, format/api/nav modules, and static policy
tests: no unsafe DOM APIs or inline handlers, every import resolves,
vendored library hash and exports, palette parity, contrast, nav parity.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 11: Component, màn hình Tổng quan (bố cục B) và khởi động ứng dụng

**Files:**
- Tạo: `web/js/components/{button,badge,panel,stat-list,filter-chips,data-table,states,toast,app-shell}.js`, `web/js/views/dashboard.js`, `web/js/app.js`
- Sửa: `web/index.html` (thay trang tạm), `webapp_testkit.py` (thêm `seed_demo_database`)

**Interfaces:**
- Consumes: Task 10 (`format.js`, `api.js`, `nav.js`, `vendor/htm-preact.js`, CSS), API `/api/dashboard` (Task 8).
- Produces (dùng ở Task 12): trên trang có `window.__qlk = {cspViolations: [], errors: []}`; các `data-testid`: `dashboard-ready` / `dashboard-loading` (gốc màn hình, `ready` khi đã tải xong dù thành công hay lỗi), `dashboard-error`, `warning-table`, `warning-empty`, `warning-foot`, `chip-all|expired|near|low` (nút có `aria-pressed`), `reload`, `nav-<id>`; mỗi `<tr>` của bảng cảnh báo có `data-severity`. `webapp_testkit.seed_demo_database(db_path) -> dict` trả `{"counts": {"all": 3, "expired": 1, "near": 1, "low": 1}, "literal": "<b>x</b>"}`.

JS không có bộ chạy test tự động trong dự án (không Node), nên chất lượng được bảo đảm bằng: test chính sách ở Task 10 (cấm API nguy hiểm, mọi import tồn tại, tên import khớp tên xuất), kiểm tra thủ công trong trình duyệt ở bước cuối task này, và smoke test trong cửa sổ thật ở Task 12. Các component đều là hàm thuần trả về `html\`...\``; chỉ màn hình có state dùng lớp `Component` (chỉ cần `html`, `render`, `Component` từ thư viện).

- [ ] **Step 1: Tạo các component**

Tạo `web/js/components/button.js`:

```js
import { html } from "../vendor/htm-preact.js";

export function Button({ tone = "secondary", disabled = false, title = null, onClick = null, testid = null, children }) {
  return html`<button type="button" class=${"btn btn--" + tone} disabled=${disabled} title=${title}
    onClick=${onClick} data-testid=${testid}>${children}</button>`;
}
```

Tạo `web/js/components/badge.js`:

```js
import { html } from "../vendor/htm-preact.js";

export function Badge({ tone = "info", children }) {
  return html`<span class=${"badge badge--" + tone}>${children}</span>`;
}
```

Tạo `web/js/components/panel.js`:

```js
import { html } from "../vendor/htm-preact.js";

export function Panel({ title, actions = null, testid = null, children }) {
  return html`<section class="panel" data-testid=${testid}>
    <header class="panel__head"><h2 class="panel__title">${title}</h2>${actions}</header>
    <div class="panel__body">${children}</div>
  </section>`;
}
```

Tạo `web/js/components/stat-list.js`:

```js
import { html } from "../vendor/htm-preact.js";

export function StatList({ items }) {
  return html`<ul class="stat-list">
    ${items.map((item) => html`<li class="stat-list__row" key=${item.key}>
      <span class=${"dot dot--" + item.tone} aria-hidden="true"></span>
      <span class="stat-list__label">${item.label}</span>
      <strong class="stat-list__value">${item.value}</strong>
    </li>`)}
  </ul>`;
}
```

Tạo `web/js/components/filter-chips.js`:

```js
import { html } from "../vendor/htm-preact.js";

export function FilterChips({ options, value, onChange }) {
  return html`<div class="chips" role="group" aria-label="Lọc cảnh báo">
    ${options.map((option) => html`<button type="button" key=${option.value}
      class=${"chip" + (option.value === value ? " chip--on" : "")}
      aria-pressed=${option.value === value ? "true" : "false"}
      data-testid=${"chip-" + option.value}
      onClick=${() => onChange(option.value)}>${option.label} ${option.count}</button>`)}
  </div>`;
}
```

Tạo `web/js/components/data-table.js`:

```js
import { html } from "../vendor/htm-preact.js";

// columns: [{ key, label, align?, render?(row) }]; rowProps(row) trả về thuộc tính thêm cho <tr>.
export function DataTable({ columns, rows, rowKey, rowProps = null, testid = null, empty = null }) {
  if (!rows.length) {
    return empty;
  }
  return html`<div class="table-wrap">
    <table class="table" data-testid=${testid}>
      <thead><tr>
        ${columns.map((column) => html`<th key=${column.key} class=${"table__th table__th--" + (column.align || "left")}>${column.label}</th>`)}
      </tr></thead>
      <tbody>
        ${rows.map((row) => html`<tr key=${rowKey(row)} ...${rowProps ? rowProps(row) : {}}>
          ${columns.map((column) => html`<td key=${column.key} class=${"table__td table__td--" + (column.align || "left")}>${column.render ? column.render(row) : row[column.key]}</td>`)}
        </tr>`)}
      </tbody>
    </table>
  </div>`;
}
```

Tạo `web/js/components/states.js`:

```js
import { html } from "../vendor/htm-preact.js";
import { Button } from "./button.js";

export function EmptyState({ title, hint = null, testid = null }) {
  return html`<div class="state" data-testid=${testid}>
    <p class="state__title">${title}</p>
    ${hint ? html`<p class="state__hint">${hint}</p>` : null}
  </div>`;
}

export function ErrorState({ title, message, onRetry = null, testid = "dashboard-error" }) {
  return html`<div class="state state--error" role="alert" data-testid=${testid}>
    <p class="state__title">${title}</p>
    <p class="state__hint">${message}</p>
    ${onRetry ? html`<div class="state__retry"><${Button} tone="secondary" onClick=${onRetry} testid="retry">Thử lại<//></div>` : null}
  </div>`;
}
```

Tạo `web/js/components/toast.js`:

```js
import { html, Component } from "../vendor/htm-preact.js";

const listeners = new Set();
let nextId = 1;

export function showToast(message, tone = "info") {
  const toast = { id: nextId++, message: String(message), tone };
  listeners.forEach((listener) => listener(toast));
}

export class ToastHost extends Component {
  constructor(props) {
    super(props);
    this.state = { toasts: [] };
    this.onToast = (toast) => {
      this.setState((state) => ({ toasts: [...state.toasts, toast] }));
      window.setTimeout(() => this.dismiss(toast.id), 5000);
    };
  }

  dismiss(id) {
    this.setState((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
  }

  componentDidMount() {
    listeners.add(this.onToast);
  }

  componentWillUnmount() {
    listeners.delete(this.onToast);
  }

  render() {
    return html`<div class="toasts" role="status" aria-live="polite">
      ${this.state.toasts.map((toast) => html`<div key=${toast.id} class=${"toast toast--" + toast.tone}>${toast.message}</div>`)}
    </div>`;
  }
}
```

Tạo `web/js/components/app-shell.js`:

```js
import { html } from "../vendor/htm-preact.js";

export function AppShell({ items, activeId, children }) {
  return html`<div class="shell">
    <aside class="shell__side" aria-label="Điều hướng chính">
      <div class="shell__brand">QUẢN LÝ KHO 2026</div>
      <nav class="shell__nav">
        ${items.map((item) => item.live
          ? html`<a key=${item.id} class=${"nav" + (item.id === activeId ? " nav--active" : "")}
              href=${"#/" + item.id} aria-current=${item.id === activeId ? "page" : null}
              data-testid=${"nav-" + item.id}><span>${item.label}</span><kbd>${item.hotkey}</kbd></a>`
          : html`<span key=${item.id} class="nav nav--off" aria-disabled="true"
              title="Chưa có trong giao diện mới" data-testid=${"nav-" + item.id}><span>${item.label}</span><small>sắp có</small></span>`)}
      </nav>
    </aside>
    <main class="shell__main">${children}</main>
  </div>`;
}
```

- [ ] **Step 2: Tạo màn hình Tổng quan**

Tạo `web/js/views/dashboard.js`:

```js
import { html, Component } from "../vendor/htm-preact.js";
import { getJson } from "../api.js";
import { formatCount, formatDate, formatDateTime, formatQty } from "../format.js";
import { Button } from "../components/button.js";
import { Badge } from "../components/badge.js";
import { Panel } from "../components/panel.js";
import { StatList } from "../components/stat-list.js";
import { FilterChips } from "../components/filter-chips.js";
import { DataTable } from "../components/data-table.js";
import { EmptyState, ErrorState } from "../components/states.js";
import { showToast } from "../components/toast.js";

const CHIPS = [["all", "Tất cả"], ["expired", "Hết hạn"], ["near", "Cận hạn"], ["low", "Tồn thấp"]];
const TONE = { expired: "danger", near: "warning", low: "info" };
const NOT_AVAILABLE = "Chưa có trong giao diện mới";
const QUICK_ACTIONS = [
  { label: "+ Nhập kho", tone: "primary" },
  { label: "− Xuất kho", tone: "primary" },
  { label: "Tra cứu tồn", tone: "secondary" },
  { label: "Báo cáo XNT", tone: "secondary" },
];

function categoryOf(severity) {
  if (severity <= 1) return "expired";
  if (severity === 2) return "near";
  return "low";
}

const COLUMNS = [
  { key: "product", label: "Thuốc - vật tư", render: (row) => `#${row.productId}  ${row.productName}` },
  { key: "lot", label: "Lô", align: "center", render: (row) => row.lotNo },
  { key: "expiry", label: "Hạn dùng", align: "center", render: (row) => formatDate(row.expiryDate) },
  { key: "stock", label: "Tồn", align: "right", render: (row) => formatQty(row.stockBase) },
  { key: "fund", label: "Nguồn", render: (row) => row.fundSource || "(không rõ)" },
  {
    key: "status",
    label: "Trạng thái",
    align: "center",
    render: (row) => html`<${Badge} tone=${TONE[categoryOf(row.severity)]}>${row.status}<//>`,
  },
];

export class DashboardView extends Component {
  constructor(props) {
    super(props);
    this.requestId = 0;
    this.state = { filter: "all", data: null, error: null, loading: true };
    this.reload = () => this.load(this.state.filter);
    this.pickFilter = (value) => this.load(value);
  }

  componentDidMount() {
    this.load("all");
  }

  componentWillUnmount() {
    this.requestId += 1; // bỏ qua phản hồi đến muộn sau khi rời màn hình
  }

  async load(filter) {
    const requestId = ++this.requestId;
    this.setState({ filter, loading: true });
    try {
      const data = await getJson("/api/dashboard", { filter });
      if (requestId !== this.requestId) return; // đã có yêu cầu mới hơn: bỏ phản hồi cũ
      this.setState({ data, error: null, loading: false });
    } catch (error) {
      if (requestId !== this.requestId) return;
      this.setState({ error, loading: false });
      showToast(error.message, "danger");
    }
  }

  renderHeader() {
    return html`<header class="page-head">
      <div>
        <h1 class="page-head__title">Tổng quan vận hành kho</h1>
        <p class="page-head__sub">FEFO theo lô và HSD</p>
      </div>
      <div class="page-head__actions">
        ${QUICK_ACTIONS.map((action) => html`<${Button} key=${action.label} tone=${action.tone}
          disabled=${true} title=${NOT_AVAILABLE}>${action.label}<//>`)}
        <${Button} tone="secondary" title="Tải lại" testid="reload" onClick=${this.reload}>↻<//>
      </div>
    </header>`;
  }

  renderWarnings(data) {
    const { filter, loading } = this.state;
    const counts = data.warnings.counts;
    const rows = data.warnings.rows;
    const options = CHIPS.map(([value, label]) => ({ value, label, count: counts[value] }));
    const chips = html`<${FilterChips} options=${options} value=${filter} onChange=${this.pickFilter} />`;
    const empty = html`<${EmptyState} testid="warning-empty"
      title=${counts.all === 0 ? "Không có cảnh báo nào cần xử lý" : "Không có dòng nào thuộc nhóm này"} />`;
    return html`<${Panel} title="⚠ CẦN XỬ LÝ HÔM NAY" actions=${chips} testid="warnings-panel">
      <${DataTable} testid="warning-table" columns=${COLUMNS} rows=${rows} empty=${empty}
        rowKey=${(row) => `${row.productId}-${row.batchId}-${row.fundSource}`}
        rowProps=${(row) => ({ class: "row--" + categoryOf(row.severity), "data-severity": row.severity })} />
      <div class="panel__foot" data-testid="warning-foot">
        ${loading ? "Đang tải…" : `Hiển thị ${rows.length} / ${counts[filter]} dòng`}
      </div>
    <//>`;
  }

  renderActivities(activities) {
    if (!activities.length) {
      return html`<${EmptyState} title="Chưa có hoạt động được ghi nhận" />`;
    }
    return html`<ul class="info-list">
      ${activities.map((item, index) => html`<li key=${index} class="info-list__row">
        ${formatDateTime(item.timestamp)} • ${item.action} • ${item.details}
      </li>`)}
    </ul>`;
  }

  renderSide(data) {
    const cards = data.cards;
    const stats = [
      { key: "products", label: "Tổng mặt hàng", value: formatCount(cards.productCount), tone: "neutral" },
      { key: "active", label: "Lô đang tồn", value: formatCount(cards.activeLotCount), tone: "success" },
      { key: "near", label: `Cận hạn ≤${data.warningDays} ngày`, value: formatCount(cards.nearExpiryCount), tone: "warning" },
      { key: "expired", label: "Đã hết hạn", value: formatCount(cards.expiredCount), tone: "danger" },
      { key: "low", label: `Tồn thấp ≤${data.lowStockThreshold}`, value: formatCount(cards.lowStockCount), tone: "warning" },
    ];
    const runtime = data.runtime;
    const backupOk = Boolean(runtime.lastBackup);
    const backupText = backupOk
      ? `✓ Sao lưu gần nhất: ${formatDateTime(runtime.lastBackup.created)}`
      : "! Chưa có bản sao lưu";
    const temp = runtime.latestTemperature;
    const humidity = temp && temp.humidity !== null ? ` • ${formatQty(temp.humidity)}%` : "";
    const negative = runtime.negativeStockRows;
    return html`<div class="dashboard__side">
      <${Panel} title="SỐ LIỆU KHO (theo lô)" testid="stats-panel"><${StatList} items=${stats} /><//>
      <${Panel} title="↶ HOẠT ĐỘNG GẦN ĐÂY" testid="activity-panel">${this.renderActivities(data.activities)}<//>
      <${Panel} title="✓ TRẠNG THÁI" testid="status-panel">
        <ul class="info-list">
          <li class=${"info-list__row " + (backupOk ? "is-ok" : "is-warn")}>${backupText}</li>
          <li class="info-list__row">${temp
            ? html`Nhiệt độ gần nhất: ${formatQty(temp.temperature)}°C${humidity}<br />${temp.locationName} • ${formatDate(temp.logDate)} • ${temp.session}`
            : "Nhiệt độ & độ ẩm: chưa có bản ghi"}</li>
          <li class=${"info-list__row " + (negative === 0 ? "is-ok" : "is-warn")}>${negative === 0
            ? "✓ Không có dòng tồn âm"
            : `! Phát hiện ${negative} dòng tồn âm`}</li>
        </ul>
      <//>
    </div>`;
  }

  renderBody() {
    const { data, error } = this.state;
    if (data) {
      return html`${error ? html`<p class="dashboard__error" role="alert">${error.message}</p>` : null}
        <div class="dashboard__grid">${this.renderWarnings(data)}${this.renderSide(data)}</div>
        <p class="dashboard__note">Ngưỡng tồn thấp hiện là ≤${data.lowStockThreshold} đơn vị cơ sở, không phải định mức cấu hình.</p>`;
    }
    if (error) {
      const expired = error.authRequired === true;
      return html`<${ErrorState}
        title=${expired ? "Phiên làm việc đã hết hạn" : "Không tải được Tổng quan"}
        message=${expired ? "Hãy đóng cửa sổ và mở lại ứng dụng." : error.message}
        onRetry=${expired ? null : this.reload} />`;
    }
    return html`<${EmptyState} title="Đang tải dữ liệu…" />`;
  }

  render() {
    const { data, error, loading } = this.state;
    const ready = !loading && Boolean(data || error);
    return html`<section class="dashboard" data-testid=${ready ? "dashboard-ready" : "dashboard-loading"}>
      ${this.renderHeader()}${this.renderBody()}
    </section>`;
  }
}
```

- [ ] **Step 3: Tạo `app.js` và thay trang tạm**

Tạo `web/js/app.js`:

```js
import { html, render, Component } from "./vendor/htm-preact.js";
import { NAV_ITEMS } from "./nav.js";
import { AppShell } from "./components/app-shell.js";
import { ToastHost, showToast } from "./components/toast.js";
import { DashboardView } from "./views/dashboard.js";

// Chẩn đoán cho smoke test đóng gói (quanly_web.py --smoke đọc window.__qlk).
window.__qlk = { cspViolations: [], errors: [] };
document.addEventListener("securitypolicyviolation", (event) => {
  window.__qlk.cspViolations.push(`${event.violatedDirective} ${event.blockedURI}`);
});
window.addEventListener("error", (event) => {
  window.__qlk.errors.push(String(event.message));
});
window.addEventListener("unhandledrejection", (event) => {
  window.__qlk.errors.push(String(event.reason));
});

const VIEWS = { dashboard: DashboardView };

function routeFromHash() {
  const id = String(window.location.hash || "").replace(/^#\//, "");
  const item = NAV_ITEMS.find((entry) => entry.id === id);
  return item && item.live ? item.id : "dashboard"; // mục chưa có bản web vẫn giữ Tổng quan
}

class App extends Component {
  constructor(props) {
    super(props);
    this.state = { route: routeFromHash() };
    this.onHashChange = () => this.setState({ route: routeFromHash() });
    this.onKeyDown = (event) => {
      const item = NAV_ITEMS.find((entry) => entry.hotkey === event.key);
      if (!item) return;
      event.preventDefault(); // chặn F5 (tải lại) và F12 (devtools) mặc định
      if (item.live) {
        window.location.hash = `#/${item.id}`;
      } else {
        showToast("Màn hình này chưa có trong giao diện mới. Hãy mở bằng bản Tkinter.", "info");
      }
    };
  }

  componentDidMount() {
    window.addEventListener("hashchange", this.onHashChange);
    window.addEventListener("keydown", this.onKeyDown);
  }

  componentWillUnmount() {
    window.removeEventListener("hashchange", this.onHashChange);
    window.removeEventListener("keydown", this.onKeyDown);
  }

  render() {
    const View = VIEWS[this.state.route];
    return html`<${AppShell} items=${NAV_ITEMS} activeId=${this.state.route}>
        <${View} key=${this.state.route} />
      <//>
      <${ToastHost} />`;
  }
}

render(html`<${App} />`, document.getElementById("app"));
```

Thay toàn bộ `web/index.html` (trang tạm ở Task 9):

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Quản lý kho 2026</title>
  <link rel="stylesheet" href="/css/tokens.css">
  <link rel="stylesheet" href="/css/base.css">
  <link rel="stylesheet" href="/css/components.css">
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/js/app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Thêm DB mẫu vào harness**

Thêm vào cuối `webapp_testkit.py`:

```python


def seed_demo_database(db_path):
    """DB mẫu cho smoke test và kiểm tra thủ công: 1 hết hạn, 1 cận hạn, 1 tồn thấp, 1 bình thường.

    Tên sản phẩm đầu tiên chứa thẻ HTML và dấu nháy để kiểm tra hiển thị an toàn.
    """
    import datetime as dt
    import os

    from database import DB

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    today = dt.date.today()
    products = [
        (1, '<b>x</b> Thuốc hết hạn & "q"', "L-EXP", -10, 20),
        (2, "Thuốc cận hạn", "L-NEAR", 30, 50),
        (3, "Vật tư tồn thấp", "L-LOW", 800, 5),
        (4, "Thuốc bình thường", "L-OK", 900, 100),
    ]
    db = DB(db_path)
    try:
        for product_id, name, lot, offset_days, qty in products:
            db.conn.execute(
                "INSERT INTO products(id, name, defaultUnit) VALUES(?, ?, 'Viên')", (product_id, name)
            )
            db.conn.execute(
                "INSERT INTO product_units(productId, unitCode, toBaseQty, price) VALUES(?, 'Viên', 1, 0)",
                (product_id,),
            )
            db.conn.commit()
            db.record_purchase(
                [{
                    "productId": product_id, "productName": name, "qty": qty, "unitCode": "Viên",
                    "lotNo": lot, "expiryDate": (today + dt.timedelta(days=offset_days)).isoformat(),
                    "cost": 1000, "fundSource": "BHYT",
                }],
                "NCC", "Nhập kho", "",
            )
    finally:
        db.conn.close()
    return {"counts": {"all": 3, "expired": 1, "near": 1, "low": 1}, "literal": "<b>x</b>"}
```

- [ ] **Step 5: Chạy test chính sách và toàn bộ test web đã có**

Run: `py -3.10 -m unittest test_web_assets_policy test_quanly_web test_webapp_listener test_webapp_dashboard 2>&1 | tail -6`
Expected: `OK`. Test chính sách phải bắt được nếu có chỗ import sai tên (ví dụ `Badge` nhập từ file không xuất nó).

- [ ] **Step 6: Kiểm tra thủ công trong trình duyệt (bắt buộc: đây là lần đầu giao diện được chạy thật)**

```bash
export QLK_APPDATA="$TEMP/qlk_ui_check"
rm -rf "$QLK_APPDATA" && mkdir -p "$QLK_APPDATA"
export LOCALAPPDATA="$(cygpath -w "$QLK_APPDATA")"
py -3.10 -c "import webapp_testkit, config; print(webapp_testkit.seed_demo_database(config.DB_PATH))"
py -3.10 quanly_web.py --serve
```

(lệnh cuối chạy ở nền; in địa chỉ boot). Mở địa chỉ boot đó trong trình duyệt (ví dụ trình duyệt tích hợp của Claude: `mcp__Claude_Browser__navigate`), rồi kiểm tra bằng mắt và `read_page`/`get_page_text`:

1. Tiêu đề "Tổng quan vận hành kho", 4 nút tác nghiệp nhanh bị vô hiệu hóa (di chuột thấy gợi ý "Chưa có trong giao diện mới"), nút ↻.
2. Bảng cảnh báo có 3 dòng: dòng "Đã hết hạn" nền đỏ nhạt, dòng "Cận hạn 30 ngày" nền vàng nhạt, dòng "Tồn thấp ≤10". Dòng đầu **hiện nguyên văn `<b>x</b> Thuốc hết hạn & "q"`** (không có chữ in đậm, không có thẻ `<b>` trong DOM của bảng).
3. Chip: "Tất cả 3", "Hết hạn 1", "Cận hạn 1", "Tồn thấp 1"; bấm từng chip thì bảng chỉ còn đúng nhóm đó và chân bảng ghi "Hiển thị 1 / 1 dòng".
4. Cột phải: "SỐ LIỆU KHO (theo lô)" gồm 4 / 4 / 1 / 1 / 1 theo thứ tự Tổng mặt hàng, Lô đang tồn, Cận hạn ≤90 ngày, Đã hết hạn, Tồn thấp ≤10 (ghi lại số thấy thực tế; phải khớp `cards` của API), "HOẠT ĐỘNG GẦN ĐÂY" có 4 dòng NHAP_KHO, "TRẠNG THÁI" có "! Chưa có bản sao lưu" và "Nhiệt độ & độ ẩm: chưa có bản ghi" và "✓ Không có dòng tồn âm".
5. Nhấn F1 (mục chưa có bản web): hiện toast "Màn hình này chưa có trong giao diện mới…"; địa chỉ `#/products` gõ tay thì vẫn hiển thị Tổng quan.
6. Console không có lỗi hay vi phạm CSP: trong trình duyệt chạy `JSON.stringify(window.__qlk)`, expected `{"cspViolations":[],"errors":[]}`.

Dừng tiến trình nền khi xong. Nếu bước nào sai, sửa file JS/CSS tương ứng rồi tải lại; **không** chuyển sang task sau khi còn lỗi hiển thị.

- [ ] **Step 7: Commit**

```bash
git add web/index.html web/js/app.js web/js/components web/js/views webapp_testkit.py
git commit -F - <<'EOF'
Add dashboard view (layout B), components and app bootstrap

Preact+htm components (shell, panel, stat list, filter chips, data table,
badge, toast, states) and the read-only Dashboard with filter chips,
quick-action buttons (disabled until their screens exist), activity and
status panels. A request counter drops stale responses when chips are
clicked quickly. Includes a demo database seeder for manual and smoke
checks.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 12: Smoke test trong cửa sổ thật (`--smoke`) và trình chạy smoke

**Files:**
- Tạo: `webapp/smoke.py`, `release_web_smoke_check.py`
- Sửa: `quanly_web.py` (thêm cờ `--smoke`), `test_quanly_web.py` (thêm test cho cờ)
- Test: `test_webapp_smoke.py` (mới)

**Interfaces:**
- Consumes: Task 9 (`run_window(listener, on_ready)`), Task 11 (các `data-testid` và `window.__qlk`), `webapp_testkit.seed_demo_database`.
- Produces (dùng ở Task 13, 14): `webapp.smoke.run_smoke(window) -> int` (in `WEB_SMOKE_OK` và trả 0, hoặc in `WEB_SMOKE_FAIL: <lý do>` và trả 1); biến môi trường `QLK_SMOKE_EXPECT` = JSON `{"counts": {"all","expired","near","low"}, "literal": str|null}` bật phần kiểm tra chip lọc và hiển thị an toàn; `quanly_web.py --smoke`; `release_web_smoke_check.py [--source]` chạy hai kịch bản (`empty` = cài mới, `seeded` = DB mẫu), mã thoát 0 khi cả hai đạt.

Các kiểm tra của smoke: màn hình sẵn sàng và không ở trạng thái lỗi; tiêu đề đúng; không có vi phạm CSP hay lỗi JavaScript (`window.__qlk`); nhãn chip khớp số đếm kỳ vọng; tên thuốc chứa `<b>` hiện nguyên văn và không có thẻ `<b>` trong bảng; bấm từng chip cho đúng nhóm dòng; **bấm 3 chip trong một nhịp** thì kết quả cuối khớp chip cuối cùng và vẫn giữ nguyên sau 1 giây (phản hồi cũ không ghi đè); mở `#/products` vẫn giữ Tổng quan.

- [ ] **Step 1: Viết test thất bại**

Tạo `test_webapp_smoke.py`:

```python
# -*- coding: utf-8 -*-
import contextlib
import io
import json
import os
import tempfile
import time
import unittest
from unittest import mock

from database import DB
from webapp import smoke
from webapp.services import dashboard as service
from webapp_testkit import seed_demo_database

REAL_SLEEP = time.sleep  # lấy trước khi vá, để bản vá không gọi lại chính nó
COUNTS = {"all": 3, "expired": 1, "near": 1, "low": 1}
EXPECT = json.dumps({"counts": COUNTS, "literal": "<b>x</b>"})


class FakeDashboardWindow:
    """Mô phỏng vừa đủ DOM của Tổng quan để chạy kịch bản smoke."""

    def __init__(self, counts, literal="<b>x</b>", ready=True, bold=0, csp=None, stale_rows=False):
        self.counts = counts
        self.literal = literal
        self.ready = ready
        self.bold = bold
        self.csp = csp or []
        self.stale_rows = stale_rows
        self.pressed = "all"
        self.rows_from = "all"
        self.hash = ""

    def _severities(self, source):
        c = self.counts
        return {
            "all": ["0"] * c["expired"] + ["2"] * c["near"] + ["3"] * c["low"],
            "expired": ["0"] * c["expired"],
            "near": ["2"] * c["near"],
            "low": ["3"] * c["low"],
        }[source]

    def evaluate_js(self, script):
        if script == smoke.STATE:
            c = self.counts
            return json.dumps({
                "ready": self.ready,
                "error": False,
                "title": "Tổng quan vận hành kho",
                "activeNav": "▦  Tổng quan F4",
                "chipLabels": [f"Tất cả {c['all']}", f"Hết hạn {c['expired']}", f"Cận hạn {c['near']}", f"Tồn thấp {c['low']}"],
                "pressed": [self.pressed],
                "severities": self._severities(self.rows_from),
                "tableText": self.literal or "",
                "boldCount": self.bold,
                "diagnostics": {"cspViolations": self.csp, "errors": []},
            })
        for name in ("expired", "near", "low", "all"):
            if script == smoke.click_script(name):
                self.pressed = self.rows_from = name
                return True
        if script == smoke.RAPID_CLICKS:
            self.pressed = "low"
            # Lỗi mô phỏng: phản hồi của chip đầu tiên đến muộn và ghi đè bảng.
            self.rows_from = "expired" if self.stale_rows else "low"
            return True
        if script == smoke.OPEN_UNAVAILABLE_ROUTE:
            self.hash = "#/products"
            return True
        raise AssertionError(f"Script lạ: {script[:80]}")


def run(window, expect=EXPECT):
    out = io.StringIO()
    env = {"QLK_SMOKE_EXPECT": expect} if expect is not None else {}
    with mock.patch.dict(os.environ, env, clear=False), contextlib.redirect_stdout(out):
        if expect is None:
            os.environ.pop("QLK_SMOKE_EXPECT", None)
        code = smoke.run_smoke(window)
    return code, out.getvalue()


class SmokeScenarioTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.multiple(smoke, TIMEOUT_SECONDS=0.5, POLL_SECONDS=0.02)
        patcher.start()
        self.addCleanup(patcher.stop)
        sleeper = mock.patch.object(smoke.time, "sleep", lambda seconds: REAL_SLEEP(min(seconds, 0.02)))
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def test_healthy_dashboard_passes(self):
        window = FakeDashboardWindow(COUNTS)
        code, output = run(window)
        self.assertEqual((code, output.strip()), (0, "WEB_SMOKE_OK"))
        self.assertEqual(window.hash, "#/products")

    def test_basic_checks_without_an_expectation(self):
        code, output = run(FakeDashboardWindow({"all": 0, "expired": 0, "near": 0, "low": 0}), expect=None)
        self.assertEqual((code, output.strip()), (0, "WEB_SMOKE_OK"))

    def test_empty_database_scenario_passes(self):
        zero = {"all": 0, "expired": 0, "near": 0, "low": 0}
        code, output = run(FakeDashboardWindow(zero, literal=None), json.dumps({"counts": zero, "literal": None}))
        self.assertEqual((code, output.strip()), (0, "WEB_SMOKE_OK"))

    def test_text_rendered_as_html_fails(self):
        code, output = run(FakeDashboardWindow(COUNTS, bold=1))
        self.assertEqual(code, 1)
        self.assertIn("<b>", output)

    def test_csp_violation_fails(self):
        code, output = run(FakeDashboardWindow(COUNTS, csp=["script-src-elem https://evil.example"]))
        self.assertEqual(code, 1)
        self.assertIn("CSP", output)

    def test_stale_response_overwriting_the_last_chip_fails(self):
        code, output = run(FakeDashboardWindow(COUNTS, stale_rows=True))
        self.assertEqual(code, 1)
        self.assertIn("WEB_SMOKE_FAIL", output)

    def test_wrong_chip_counts_fail(self):
        wrong = dict(COUNTS, all=4)
        code, output = run(FakeDashboardWindow(wrong))
        self.assertEqual(code, 1)
        self.assertIn("chip", output.lower())

    def test_page_that_never_becomes_ready_times_out(self):
        code, output = run(FakeDashboardWindow(COUNTS, ready=False))
        self.assertEqual(code, 1)
        self.assertIn("Quá thời gian chờ", output)


class DemoSeedTests(unittest.TestCase):
    def test_seed_matches_the_expectation_used_by_the_smoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "QuanLyXNT", "pharm.db")
            expectation = seed_demo_database(path)
            db = DB(path)
            try:
                warnings = service.build_dashboard_payload(db)["warnings"]
            finally:
                db.conn.close()
        self.assertEqual(warnings["counts"], expectation["counts"])
        names = [row["productName"] for row in warnings["rows"]]
        self.assertTrue(any(expectation["literal"] in name for name in names))


if __name__ == "__main__":
    unittest.main()
```

Thêm vào lớp `ParserTests` trong `test_quanly_web.py` (sau `test_serve_flag`), và thêm `import contextlib` đã có sẵn ở đầu file:

```python
    def test_smoke_flag_and_mutual_exclusion(self):
        self.assertTrue(quanly_web.build_parser().parse_args(["--smoke"]).smoke)
        self.assertFalse(quanly_web.build_parser().parse_args([]).smoke)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            quanly_web.build_parser().parse_args(["--serve", "--smoke"])
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_webapp_smoke test_quanly_web -v 2>&1 | tail -8`
Expected: `ImportError: cannot import name 'smoke' from 'webapp'` (hoặc `ModuleNotFoundError`), và `test_smoke_flag_and_mutual_exclusion` thất bại do chưa có `--smoke`.

- [ ] **Step 3: Tạo `webapp/smoke.py`**

```python
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
```

Sửa `quanly_web.py`: thay hai hàm `build_parser` và `main` bằng bản có `--smoke`:

```bash
py -3.10 - <<'EOF'
import io
path = "quanly_web.py"
s = io.open(path, encoding="utf-8").read()
start = s.index("def build_parser()")
end = s.index('if __name__ == "__main__":')
new = '''def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quản lý kho 2026 (giao diện web)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--serve", action="store_true",
        help="chỉ mở cổng cục bộ và in địa chỉ boot một lần (phát triển/kiểm thử), không mở cửa sổ",
    )
    mode.add_argument(
        "--smoke", action="store_true",
        help="mở cửa sổ, chạy smoke test rồi thoát (mã 0 khi đạt); dùng qua release_web_smoke_check.py",
    )
    return parser


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    listener = create_listener()
    try:
        if args.serve:
            return run_serve_only(listener)
        if args.smoke:
            from webapp.smoke import run_smoke

            return run_window(listener, on_ready=run_smoke)
        return run_window(listener)
    finally:
        listener.stop()


'''
s = s[:start] + new + s[end:]
io.open(path, "w", encoding="utf-8", newline="\n").write(s)
print("quanly_web.py updated")
EOF
```

- [ ] **Step 4: Chạy test để thấy đạt**

Run: `py -3.10 -m unittest test_webapp_smoke test_quanly_web -v 2>&1 | tail -8`
Expected: `OK` (8 test smoke + 1 test seed + các test `quanly_web`).

- [ ] **Step 5: Tạo `release_web_smoke_check.py`**

```python
# -*- coding: utf-8 -*-
"""Smoke test giao diện web trong cửa sổ pywebview thật.

Mặc định chạy bản đóng gói ``dist/QuanLyKhoWeb``; ``--source`` chạy ``quanly_web.py`` từ mã nguồn.
Mỗi kịch bản dùng ``LOCALAPPDATA`` tạm nên không bao giờ chạm DB thật:
  * empty : cài mới, DB trống (Tổng quan hiện số 0, không báo lỗi)
  * seeded: DB mẫu (chip lọc, hiển thị an toàn, bấm nhanh, địa chỉ chưa có bản web)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
APP_DIST = ROOT / "dist" / "QuanLyKhoWeb"
EXE = APP_DIST / "QuanLyKhoWeb.exe"
SCENARIO_TIMEOUT_SECONDS = 180
EMPTY_EXPECTATION = {"counts": {"all": 0, "expired": 0, "near": 0, "low": 0}, "literal": None}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_package() -> None:
    if not EXE.is_file():
        raise RuntimeError(f"Thiếu packaged executable: {EXE}")
    if EXE.stat().st_size < 1024 * 1024:
        raise RuntimeError(f"{EXE} nhỏ bất thường")
    manifest = APP_DIST / "SHA256SUMS.txt"
    if not manifest.is_file():
        raise RuntimeError("Thiếu SHA256SUMS.txt")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        path = APP_DIST / Path(rel)
        if not path.is_file():
            raise RuntimeError(f"Manifest trỏ tới file bị thiếu: {rel}")
        if _sha256(path).lower() != expected.lower():
            raise RuntimeError(f"SHA-256 mismatch: {rel}")


def _env(local_appdata: Path, expectation=None) -> dict:
    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(local_appdata)
    env["PYTHONUTF8"] = "1"
    env.pop("QLK_SMOKE_EXPECT", None)
    if expectation is not None:
        env["QLK_SMOKE_EXPECT"] = json.dumps(expectation)
    return env


def seed_database(local_appdata: Path) -> dict:
    """Tạo DB mẫu ở LOCALAPPDATA tạm (trong tiến trình con để config.py đọc đúng thư mục)."""
    code = (
        "import json, config, webapp_testkit; "
        "print('SEED:' + json.dumps(webapp_testkit.seed_demo_database(config.DB_PATH)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=_env(local_appdata),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    for line in result.stdout.splitlines():
        if line.startswith("SEED:"):
            return json.loads(line[5:])
    raise RuntimeError("Không tạo được DB mẫu:\n" + (result.stdout + result.stderr)[-2000:])


def run_scenario(name: str, command: list, cwd: Path, local_appdata: Path, expectation: dict) -> bool:
    result = subprocess.run(
        command, cwd=cwd, env=_env(local_appdata, expectation),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=SCENARIO_TIMEOUT_SECONDS,
    )
    output = (result.stdout or "") + (result.stderr or "")
    ok = result.returncode == 0 and "WEB_SMOKE_OK" in output
    print(f"[{name}] {'OK' if ok else 'FAIL'} (exit={result.returncode})")
    if not ok:
        print(output[-4000:])
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="store_true", help="chạy quanly_web.py từ mã nguồn thay vì bản đóng gói")
    args = parser.parse_args()

    if os.name != "nt":
        print("Smoke test giao diện web chỉ hỗ trợ Windows")
        return 0

    if args.source:
        command, cwd = [sys.executable, "quanly_web.py", "--smoke"], ROOT
    else:
        verify_package()
        command, cwd = [str(EXE), "--smoke"], APP_DIST

    results = []
    with tempfile.TemporaryDirectory(prefix="quanlykho-web-empty-") as empty_dir:
        results.append(run_scenario("empty", command, cwd, Path(empty_dir), EMPTY_EXPECTATION))
    with tempfile.TemporaryDirectory(prefix="quanlykho-web-seeded-") as seeded_dir:
        expectation = seed_database(Path(seeded_dir))
        results.append(run_scenario("seeded", command, cwd, Path(seeded_dir), expectation))
    return 0 if all(results) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"WEB RELEASE SMOKE FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 6: Chạy smoke thật từ mã nguồn (cần pywebview và WebView2)**

Run: `$QLK_PY release_web_smoke_check.py --source`
Expected: hai dòng `[empty] OK (exit=0)` và `[seeded] OK (exit=0)`. Một cửa sổ sẽ hiện và tự đóng ở mỗi kịch bản (mỗi kịch bản vài giây đến khoảng nửa phút). Nếu `FAIL`, đọc phần đầu ra in kèm: dòng `WEB_SMOKE_FAIL: ...` nêu đúng kiểm tra nào không đạt; sửa nguyên nhân gốc (không nới lỏng smoke test).

- [ ] **Step 7: Commit**

```bash
git add webapp/smoke.py quanly_web.py release_web_smoke_check.py test_webapp_smoke.py test_quanly_web.py
git commit -F - <<'EOF'
Add in-window smoke test for the web UI (--smoke)

Checks readiness, CSP/JS diagnostics, filter chip counts, literal rendering
of hostile text, rapid chip clicks (last chip wins, stale responses are
dropped) and that an unavailable route keeps the dashboard. The runner
covers an empty (fresh install) and a seeded database, from source or from
the packaged build, always on a temporary LOCALAPPDATA.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 13: Đóng gói `dist/QuanLyKhoWeb/`

**Files:**
- Tạo: `build_web_release.py`
- Test: `test_build_web_release.py`

**Interfaces:**
- Consumes: Task 12 (`release_web_smoke_check.py` kiểm tra bản đóng gói), `web/` (Task 10, 11), `quanly_web.py` (Task 9).
- Produces (dùng ở Task 14): `build_web_release.build_command(python=None) -> list[str]`, `build_web_release._validate_distribution()` (ném `RuntimeError` khi thiếu file), `python build_web_release.py [--ci]` tạo `dist/QuanLyKhoWeb/` (onedir, có `QuanLyKhoWeb.exe`, `_internal/web/**`, `SHA256SUMS.txt`).

- [ ] **Step 1: Viết test thất bại**

Tạo `test_build_web_release.py`:

```python
# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build_web_release


class BuildCommandTests(unittest.TestCase):
    def test_command_bundles_web_and_excludes_desktop_only_libraries(self):
        command = build_web_release.build_command("python")
        self.assertEqual(command[:3], ["python", "-m", "PyInstaller"])
        for flag in ("--onedir", "--console", "--noconfirm", "--clean", "--name=QuanLyKhoWeb"):
            self.assertIn(flag, command)
        web = build_web_release.ROOT / "web"
        self.assertIn(f"--add-data={web}{os.pathsep}web", command)
        for module in ("cv2", "pyzbar", "matplotlib", "pandas", "tkinter"):
            self.assertIn(f"--exclude-module={module}", command)
        self.assertEqual(command[-1], str(build_web_release.ROOT / "quanly_web.py"))


class ValidateDistributionTests(unittest.TestCase):
    def make_dist(self, root: Path):
        (root / "QuanLyKhoWeb.exe").write_bytes(b"0" * (1024 * 1024 + 1))
        for rel in build_web_release.REQUIRED_WEB_FILES:
            target = root / "_internal" / "web" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x", encoding="utf-8")

    def test_complete_distribution_passes_and_missing_asset_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_dist(root)
            with mock.patch.object(build_web_release, "APP_DIST", root):
                build_web_release._validate_distribution()
                (root / "_internal" / "web" / "js" / "app.js").unlink()
                with self.assertRaises(RuntimeError) as ctx:
                    build_web_release._validate_distribution()
                self.assertIn("js/app.js", str(ctx.exception))

    def test_tiny_executable_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_dist(root)
            (root / "QuanLyKhoWeb.exe").write_bytes(b"0" * 10)
            with mock.patch.object(build_web_release, "APP_DIST", root):
                with self.assertRaises(RuntimeError):
                    build_web_release._validate_distribution()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy để thấy thất bại**

Run: `py -3.10 -m unittest test_build_web_release -v 2>&1 | tail -4`
Expected: `ModuleNotFoundError: No module named 'build_web_release'`.

- [ ] **Step 3: Tạo `build_web_release.py`**

```python
# -*- coding: utf-8 -*-
"""Build bản phát hành giao diện web: dist/QuanLyKhoWeb/ (PyInstaller onedir).

Tách khỏi build_release.py (bản Tkinter) để hai bản độc lập, dùng chung DB.
Thư viện chỉ dùng cho bản Tkinter (OpenCV, pandas, matplotlib, ...) bị loại khỏi bản web:
``config.py`` đã bọc việc import chúng trong try/except nên thiếu chúng vẫn chạy được.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DIST_ROOT = ROOT / "dist"
APP_DIST = DIST_ROOT / "QuanLyKhoWeb"
WORK_ROOT = ROOT / "build_web"
EXCLUDED_MODULES = (
    "cv2", "pyzbar", "matplotlib", "pandas", "numpy", "PIL", "reportlab",
    "openpyxl", "qrcode", "schedule", "ttkbootstrap", "tkinter",
)
REQUIRED_WEB_FILES = (
    "index.html",
    "css/tokens.css",
    "css/base.css",
    "css/components.css",
    "js/app.js",
    "js/vendor/htm-preact.js",
)


def _require(path: Path, label: str) -> Path:
    if not path.exists():
        raise RuntimeError(f"Thiếu {label}: {path}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_command(python=None) -> list:
    command = [
        python or sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onedir", "--console", "--noupx",
        "--name=QuanLyKhoWeb",
        f"--add-data={ROOT / 'web'}{os.pathsep}web",
    ]
    command += [f"--exclude-module={module}" for module in EXCLUDED_MODULES]
    command += [
        f"--distpath={DIST_ROOT}",
        f"--workpath={WORK_ROOT}",
        f"--specpath={WORK_ROOT}",
        str(ROOT / "quanly_web.py"),
    ]
    return command


def _validate_distribution() -> None:
    exe = _require(APP_DIST / "QuanLyKhoWeb.exe", "executable")
    if exe.stat().st_size < 1024 * 1024:
        raise RuntimeError(f"{exe} nhỏ bất thường")
    web_dir = APP_DIST / "_internal" / "web"
    for rel in REQUIRED_WEB_FILES:
        _require(web_dir / rel, f"web asset {rel}")


def _write_hash_manifest() -> None:
    manifest = APP_DIST / "SHA256SUMS.txt"
    lines = []
    for path in sorted(APP_DIST.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not path.is_file() or path == manifest:
            continue
        lines.append(f"{_sha256(path)}  {path.relative_to(APP_DIST).as_posix()}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_release() -> Path:
    if os.name != "nt":
        raise RuntimeError("Release QuanLyKhoWeb hiện chỉ hỗ trợ build trên Windows")
    _require(ROOT / "quanly_web.py", "entrypoint")
    _require(ROOT / "web" / "index.html", "web UI")
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("PyInstaller chưa được cài đặt trong môi trường build") from exc
    try:
        import webview  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("pywebview chưa được cài đặt: chạy pip install -r requirements.txt") from exc

    shutil.rmtree(APP_DIST, ignore_errors=True)
    shutil.rmtree(WORK_ROOT, ignore_errors=True)
    print("Building web release candidate with:", sys.executable)
    subprocess.run(build_command(), cwd=ROOT, check=True)
    _validate_distribution()
    _write_hash_manifest()
    print(f"Web release candidate ready: {APP_DIST}")
    return APP_DIST


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true", help="CI marker; behavior remains deterministic")
    parser.parse_args()
    try:
        build_release()
        return 0
    except Exception as exc:
        print(f"WEB RELEASE BUILD FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Chạy test để thấy đạt**

Run: `py -3.10 -m unittest test_build_web_release -v 2>&1 | tail -6`
Expected: `OK` (3 test).

- [ ] **Step 5: Build thật và chạy smoke đóng gói**

```bash
$QLK_PY build_web_release.py
ls dist/QuanLyKhoWeb | head
$QLK_PY release_web_smoke_check.py
```

Expected: `Web release candidate ready: ...`; thư mục có `QuanLyKhoWeb.exe`, `_internal`, `SHA256SUMS.txt`; smoke in `[empty] OK (exit=0)` và `[seeded] OK (exit=0)`.

Nếu bản đóng gói báo `ModuleNotFoundError` cho một module vừa bị loại (ví dụ `numpy`, `PIL`), bỏ **đúng module đó** khỏi `EXCLUDED_MODULES`, build lại và ghi chú lý do ngay trong tuple (chú thích một dòng). Nếu thiếu module của pywebview/pythonnet, dùng các cờ đã ghi trong kết quả spike (`2026-10-01-web-ui-p1-spike-result.md`) và thêm chúng vào `build_command`. Không bỏ qua hay nới lỏng smoke test.

- [ ] **Step 6: Commit**

```bash
git add build_web_release.py test_build_web_release.py
git commit -F - <<'EOF'
Add packaging for the web UI (dist/QuanLyKhoWeb)

PyInstaller onedir build separate from the Tkinter release, bundling web/
and excluding desktop-only libraries, with asset validation and a SHA-256
manifest checked by the packaged smoke test.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 14: CI, tài liệu và kiểm tra cuối

**Files:**
- Sửa: `.github/workflows/tests.yml`, `README.md`

**Interfaces:**
- Consumes: mọi task trước.
- Produces: pipeline CI chạy bộ test mới, build `dist/QuanLyKhoWeb`, smoke đóng gói và tải artifact; mục README cho giao diện web; kết quả kiểm tra cuối (số test, `pip-audit`, smoke, đối chiếu trên bản sao DB thật).

- [ ] **Step 1: Sửa CI**

```bash
py -3.10 - <<'EOF'
import io
path = ".github/workflows/tests.yml"
s = io.open(path, encoding="utf-8").read()

old = "test_ui_support_final.py test_xnt_excel_export.py test_input_validation.py test_mobile_template_escaping.py"
assert s.count(old) == 1
new_files = (
    " http_limits.py quanly_web.py webapp_testkit.py build_web_release.py release_web_smoke_check.py"
    " test_http_limits.py test_webapp_dashboard.py test_webapp_routing.py test_webapp_local_auth.py"
    " test_webapp_static.py test_webapp_listener.py test_webapp_runtime.py test_quanly_web.py"
    " test_webapp_smoke.py test_build_web_release.py test_web_assets_policy.py webapp"
)
s = s.replace(old, old + new_files)

steps = r'''
      - name: Ensure WebView2 runtime
        shell: pwsh
        run: |
          $key = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
          if (Test-Path $key) { "WebView2 runtime present: $((Get-ItemProperty $key).pv)"; exit 0 }
          Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile "$env:RUNNER_TEMP\MicrosoftEdgeWebview2Setup.exe"
          Start-Process -FilePath "$env:RUNNER_TEMP\MicrosoftEdgeWebview2Setup.exe" -ArgumentList '/silent','/install' -Wait
          if (-not (Test-Path $key)) { throw 'WebView2 runtime installation failed' }

      - name: Build web release candidate
        run: python build_web_release.py --ci

      - name: Packaged web smoke
        run: python release_web_smoke_check.py

      - name: Upload web release candidate
        if: github.event_name == 'pull_request' || github.ref == 'refs/heads/main'
        uses: actions/upload-artifact@v4
        with:
          name: QuanLyKhoWeb-windows-rc
          path: dist/QuanLyKhoWeb
          if-no-files-found: error
          retention-days: 7
'''
s = s.rstrip("\n") + "\n" + steps
io.open(path, "w", encoding="utf-8", newline="\n").write(s)
print("tests.yml updated")
EOF
tail -32 .github/workflows/tests.yml
py -3.10 -c "import yaml" 2>/dev/null && py -3.10 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/tests.yml', encoding='utf-8')); print('YAML hợp lệ')" || echo "(PyYAML không có: đọc lại bằng mắt, các bước thụt lề 6 khoảng trắng như các bước cũ)"
```

Expected: ba bước mới nằm sau bước "Upload Windows release candidate", cùng mức thụt lề với các bước cũ; danh sách `compileall` chứa các file mới.

- [ ] **Step 2: Thêm mục README**

```bash
py -3.10 - <<'EOF'
import io
path = "README.md"
s = io.open(path, encoding="utf-8").read()
anchor = "## 📦 Hướng dẫn đóng gói File chạy (.exe) độc lập"
assert s.count(anchor) == 1
section = '''## 🌐 Giao diện web (thử nghiệm)

Bản giao diện web chạy song song với bản Tkinter và dùng chung dữ liệu (`pharm.db`). Hiện mới có màn hình **Tổng quan**; các màn hình còn lại vẫn dùng bản Tkinter (`run.bat`).

*   Yêu cầu: Windows có Microsoft Edge WebView2 Runtime (sẵn trên Windows 11; Windows 10 cần cài nếu chưa có, ứng dụng sẽ hiện hướng dẫn).
*   Chạy: `run_web.bat` hoặc `python quanly_web.py`.
*   Chế độ phát triển (không mở cửa sổ, mở bằng trình duyệt): `python quanly_web.py --serve`, rồi mở địa chỉ được in ra (chỉ dùng được một lần).
*   Đóng gói: `python build_web_release.py` tạo `dist/QuanLyKhoWeb/`; kiểm tra bản đóng gói bằng `python release_web_smoke_check.py`.
*   Thiết kế: `docs/superpowers/specs/2026-10-01-web-ui-foundation-design.md`.

---

'''
s = s.replace(anchor, section + anchor)
io.open(path, "w", encoding="utf-8", newline="\n").write(s)
print("README.md updated")
EOF
grep -n "Giao diện web (thử nghiệm)" README.md
```

- [ ] **Step 3: Chạy toàn bộ test trên môi trường theo pin**

```bash
$QLK_PY -m unittest discover 2>&1 | tail -6
```

Expected: `OK`. Khi áp dụng đúng kế hoạch trên nền `main` hiện tại (106 test sẵn có), tổng là 199 test (93 test mới); 1 test symlink có thể báo `skipped` trên Windows. Ghi lại con số thật. Bất kỳ test nào thất bại, kể cả test không do thay đổi này gây ra, đều phải được liệt kê tên trong báo cáo cuối.

- [ ] **Step 4: Quét lỗ hổng phụ thuộc và smoke giao diện Tkinter**

```bash
$QLK_PY -m pip install pip-audit==2.10.1
$QLK_PY -m pip_audit -r requirements.txt --progress-spinner off
$QLK_PY ui_smoke_check.py
```

Expected: `No known vulnerabilities found` và `DESKTOP_UI_SMOKE_OK`. Nếu `pip-audit` báo lỗ hổng ở `pywebview` hoặc phụ thuộc trực tiếp của nó, báo cáo cho chủ dự án trước khi đi tiếp.

- [ ] **Step 5: Đối chiếu trên bản sao DB thật (chỉ đọc DB gốc)**

Sao lưu nhất quán bằng API của SQLite (an toàn với file WAL, không sửa DB gốc), rồi tính số liệu theo cả hai đường:

```bash
export QLK_REAL="$(cygpath -w "$(cygpath -u "$USERPROFILE")/AppData/Local/QuanLyXNT/pharm.db")"   # pharm.db thật của người dùng (chỉ đọc)
test -f "$QLK_REAL" && echo "Tìm thấy DB thật: $QLK_REAL" || echo "KHÔNG thấy DB thật: bỏ qua bước đối chiếu và ghi rõ trong báo cáo cuối"
export QLK_COPY_ROOT="$(cygpath -w "$TEMP/qlk_real_copy")"
rm -rf "$QLK_COPY_ROOT" && mkdir -p "$QLK_COPY_ROOT/QuanLyXNT"
py -3.10 - <<'EOF'
import os, pathlib, sqlite3
src = os.environ["QLK_REAL"]
dst = os.path.join(os.environ["QLK_COPY_ROOT"], "QuanLyXNT", "pharm.db")
source = sqlite3.connect(pathlib.Path(src).as_uri() + "?mode=ro", uri=True)
target = sqlite3.connect(dst)
source.backup(target)
target.close(); source.close()
print("copied ->", dst)
EOF
export LOCALAPPDATA="$QLK_COPY_ROOT"
py -3.10 - <<'EOF'
import json
import config
from database import DB
from webapp.services import dashboard as service

db = DB(config.DB_PATH)
try:
    summary = db.dashboard_summary(service.WARNING_DAYS)
    snapshot = service.build_dashboard_snapshot(db.get_inventory(), warning_days=service.WARNING_DAYS)
    payload = service.build_dashboard_payload(db)
finally:
    db.conn.close()
tk = {"productCount": int(summary["product_count"]), "activeLotCount": snapshot["active_lot_count"],
      "nearExpiryCount": snapshot["near_expiry_count"], "expiredCount": snapshot["expired_count"],
      "lowStockCount": snapshot["low_stock_count"]}
print("Tkinter logic:", json.dumps(tk))
print("Web payload  :", json.dumps(payload["cards"]))
print("warnings.counts:", payload["warnings"]["counts"], "| rows:", len(payload["warnings"]["rows"]))
assert tk == payload["cards"], "Số liệu thẻ KHÁC NHAU"
print("CARDS MATCH")
EOF
```

Expected: hai dòng số liệu giống hệt và `CARDS MATCH`. Sau đó đối chiếu bằng mắt hai giao diện cùng bản sao (đây là tiêu chí hoàn thành số 3 của spec): chạy `$QLK_PY quanly_xnt.py` rồi `$QLK_PY quanly_web.py` (cùng `LOCALAPPDATA` trỏ vào bản sao ở trên) và xác nhận các con số sau trùng nhau: Tổng mặt hàng, Lô đang tồn, Cận hạn ≤90 ngày, Đã hết hạn, Tồn thấp ≤10, và các dòng đầu của bảng cảnh báo (cùng sản phẩm, lô, hạn, tồn, nguồn, trạng thái). Ghi kết quả vào báo cáo cuối. Xóa `$QLK_COPY_ROOT` khi xong.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/tests.yml README.md
git commit -F - <<'EOF'
Run web UI tests, build and packaged smoke in CI; document the web UI

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
git status --short
git log --oneline -15
```

Expected: cây làm việc chỉ còn `?? opencode.json`; lịch sử có một commit cho mỗi task.

- [ ] **Step 7: Báo cáo và xin phép đưa lên GitHub**

Báo cáo cho chủ dự án: số test thật và kết quả `pip-audit`, smoke (cả hai kịch bản, từ mã nguồn và đóng gói), kết quả đối chiếu trên bản sao DB thật, và mọi test thất bại (nếu có). **Không push và không tạo PR** khi chưa được đồng ý. Khi được đồng ý: `git push -u origin web-ui/p1-foundation`, tạo PR vào `main` (mô tả nêu: spec, kế hoạch, kết quả kiểm tra, các điểm khác biệt có chủ ý như `--text-muted` và `negativeStockRows`), rồi đọc trạng thái CI qua công cụ của ứng dụng thay vì tự thăm dò; riêng nhánh spike tạm (nếu đã tạo ở Task 1) phải được xóa.
