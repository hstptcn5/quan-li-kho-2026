# Giao diện web: nền tảng (P1) — Thiết kế

Ngày: 2026-10-01 · Trạng thái: chờ duyệt · Dự án con 1/5 của chương trình "làm lại UI"

## 1. Bối cảnh và mục tiêu

**Người dùng đã nêu:** làm lại cả hai giao diện (desktop Tkinter và di động web) trên một hệ thiết kế chung; lý do chính là muốn **đổi công nghệ giao diện** để desktop và di động dùng chung một bộ mã giao diện.

**Đã chốt qua trao đổi:**

| Quyết định | Lựa chọn |
|---|---|
| Vỏ desktop | Cửa sổ nhúng bằng **pywebview** (Edge WebView2), backend vẫn là Python |
| Công nghệ web | HTML/CSS/ES modules + **Preact + htm** đặt sẵn trong repo, **không build**, không Node, chạy offline |
| Chiến lược chuyển đổi | **Song song, cuốn chiếu**: Tkinter vẫn là bản chính cho tới khi UI web đạt ngang tính năng và qua UAT |
| Kiến trúc | **Một backend, hai cổng**: cổng `127.0.0.1` đủ quyền cho cửa sổ desktop; cổng LAN chỉ lộ tập API di động |
| Thị giác P1 | Giữ nguyên bảng màu "Clinical Logistics Authority" đã duyệt 07/09 (chuyển 1:1 sang CSS) |

**Giả định (chưa xác nhận riêng):** chỉ đổi lớp giao diện, nghiệp vụ/DB/API di động giữ nguyên; tiếng Việt; Windows; vẫn đóng gói `.exe`.

**Mục tiêu P1:** dựng nền tảng web dùng lại được cho mọi dự án sau, và đưa **một màn hình thật (Tổng quan)** qua toàn bộ chuỗi: API → bảo mật → cửa sổ → đóng gói → CI, để lộ sớm rủi ro kỹ thuật.

## 2. Lộ trình chương trình (để đặt P1 vào ngữ cảnh)

| # | Dự án con | Nội dung |
|---|---|---|
| **P1** | **Nền tảng (tài liệu này)** | `web/`, `webapp/`, `quanly_web.py`, màn hình Tổng quan, đóng gói và CI |
| P2 | Desktop: 3 luồng hằng ngày | Danh mục hàng hóa, Nhập kho, Xuất kho (FEFO) |
| P3 | Desktop: phần còn lại | Tồn kho, Cảnh báo HSD, Báo cáo XNT, Nhiệt độ/độ ẩm, Công cụ dữ liệu, Quản trị, Báo cáo nâng cao |
| P4 | Di động | Chuyển `mobile_templates.py` sang bộ giao diện chung; hardening nhập thẳng vào server, bỏ cơ chế vá HTML bằng regex; nối cổng LAN |
| P5 | Gỡ Tkinter | Chỉ sau UAT trên bản sao DB thật và kiểm thử trên máy Windows sạch |

Mỗi dự án con có spec, kế hoạch và đợt kiểm thử riêng.

## 3. Phạm vi P1

**Trong phạm vi**
- Thư mục `web/`: token thiết kế, CSS nền, component cơ sở, router băm, thư viện đặt sẵn.
- Gói `webapp/`: router có `scope`, xác thực phiên cục bộ, phục vụ file tĩnh, API `/api/dashboard`, service tổng quan.
- `quanly_web.py` (điểm vào) và `run_web.bat`.
- Màn hình **Tổng quan** (chỉ đọc), khung điều hướng đủ 11 mục.
- Bản build `dist/QuanLyKhoWeb/` và smoke test đóng gói trong CI.

**Ngoài phạm vi:** mọi endpoint ghi dữ liệu; PIN admin trên web; cổng LAN và thay thế giao diện di động; chế độ tối; đổi nghiệp vụ hoặc lược đồ DB; tính năng mới; tài khoản nhiều người dùng. `server.py`, `mobile_templates.py` và toàn bộ `ui*.py` giữ nguyên hành vi.

P1 **chỉ đọc DB** nên không có rủi ro làm hỏng dữ liệu.

## 4. Kiến trúc và cấu trúc thư mục

```
web/                          # giao diện dùng chung, đóng gói vào .exe
  index.html
  css/tokens.css base.css components.css
  js/vendor/                  # preact + htm, ghim phiên bản, kèm LICENSE
  js/app.js                   # router băm (#/dashboard), store, phím tắt F1–F12
  js/api.js                   # bọc fetch, xử lý 401 và lỗi JSON
  js/nav.js                   # 11 mục điều hướng (nguồn dữ liệu duy nhất phía web)
  js/components/*.js          # AppShell, Button, Panel, MetricCard, Badge, DataTable, Toast, EmptyState, ErrorState
  js/views/dashboard.js
webapp/                       # backend mới, chỉ dùng thư viện chuẩn
  routing.py                  # Router nhỏ; mỗi route khai báo scope = "local" | "lan"
  auth.py                     # phiên cục bộ (boot token, cookie). PIN LAN chuyển vào ở P4
  static.py                   # phục vụ web/ an toàn, đặt header bảo mật
  listener.py                 # ThreadingHTTPServer bind 127.0.0.1:0 (tên khác server.py ở thư mục gốc để tránh nhầm)
  api/dashboard.py            # GET /api/dashboard
  services/dashboard.py       # build_dashboard_snapshot + dựng dữ liệu tổng quan (logic thuần)
quanly_web.py                 # điểm vào: mở cổng cục bộ + cửa sổ pywebview; cờ --smoke
```

**Ranh giới**
- `services/` là logic thuần: không import Tkinter, không biết HTTP. `ui_dashboard.py` import lại `build_dashboard_snapshot` từ `webapp/services/dashboard.py`, nên Tkinter vẫn chạy và `test_ui_dashboard.py` vẫn đúng.
- `webapp/` không import `ui*.py`. Lớp `DB` (`database.py`) được dùng nguyên trạng.
- Mỗi request tự mở và đóng kết nối SQLite riêng trong luồng xử lý (quy tắc H3.1). Dùng lại `validate_request_body_headers` và trần body 1 MiB từ `mobile_http_hardening.py`, không chép lại.
- **Route scope:** bộ phân phối từ chối mọi route `local` khi yêu cầu đến từ listener `lan`. Cơ chế nằm trong P1 vì là ranh giới bảo mật; listener LAN thật chỉ được nối ở P4.
- Hai app (Tkinter, web) có thể chạy cùng lúc nhờ SQLite WAL. Trong P1, server di động LAN chỉ bật được từ bản Tkinter.

## 5. Mô hình bảo mật cổng cục bộ

**Khởi động**
1. `quanly_web.py` bind `127.0.0.1` cổng 0 (hệ điều hành cấp cổng ngẫu nhiên) và sinh *boot token* (`secrets.token_urlsafe(32)`) dùng một lần.
2. Cửa sổ pywebview mở `http://127.0.0.1:<port>/boot/<token>`. Server so sánh bằng `hmac.compare_digest`, đặt cookie phiên `HttpOnly; SameSite=Strict; Path=/` (cookie phiên, hết hạn khi đóng app), trả `302 /`, rồi **hủy boot token**. Token chỉ nằm trong bộ nhớ tiến trình, không ở dòng lệnh. pywebview chạy `private_mode=True`.
3. Mọi request khác bắt buộc có cookie hợp lệ, nếu không trả 401 (API) hoặc trang trống (HTML).

**Phòng thủ bổ sung**
- `Host` chỉ chấp nhận `127.0.0.1:<port>` hoặc `localhost:<port>` (chống DNS rebinding).
- Request không phải GET/HEAD phải cùng origin (`Origin`, `Sec-Fetch-Site: same-origin`).
- File tĩnh chỉ lấy trong `web/`; từ chối `..`, đường dẫn tuyệt đối, liên kết tượng trưng; không liệt kê thư mục; chỉ phục vụ phần mở rộng trong danh sách cho phép (`.html .css .js .svg .png .ico .woff2`).
- Header: `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` cho API.
- Không `innerHTML`, không `eval`/`new Function`, không thuộc tính `on*=`, không script/style inline. Mọi chuỗi động đi qua Preact (tự escape).
- `style-src 'self'` chặn thuộc tính `style="..."` viết sẵn trong HTML, nên giao diện dùng class CSS. Gán style động qua CSSOM của Preact (`element.style`) vẫn được phép khi cần.

**Giới hạn đã chấp nhận:** tiến trình khác cùng quyền người dùng Windows có thể đọc bộ nhớ app. Nằm ngoài mô hình đe dọa, giống ghi chú trong `docs/SECURITY.md`.

## 6. Hợp đồng API

`GET /api/dashboard` (scope `local`). Trả `200` và JSON; ngày/giờ giữ dạng ISO, định dạng `DD-MM-YYYY` do frontend (khớp `date_utils.format_date_display`).

```json
{
  "success": true,
  "warningDays": 90,
  "cards": {
    "productCount": 0, "activeLotCount": 0, "nearExpiryCount": 0,
    "expiredCount": 0, "lowStockCount": 0
  },
  "warnings": {
    "total": 0,
    "rows": [{
      "productId": 1, "batchId": 1, "productName": "", "lotNo": "",
      "expiryDate": "2030-12-31", "fundSource": "", "stockBase": 12.5,
      "status": "Cận hạn 30 ngày", "severity": 2, "daysLeft": 30
    }]
  },
  "activities": [{ "timestamp": "2026-10-01 09:30:00", "action": "", "details": "" }],
  "runtime": {
    "lastBackup": { "file": "", "created": "2026-10-01 09:00:00" },
    "latestTemperature": {
      "logDate": "2026-10-01", "session": "", "locationName": "",
      "temperature": 24.0, "humidity": 55.0, "recordedBy": ""
    },
    "negativeStockRows": 0
  }
}
```

- `warnings.rows` tối đa 80 dòng, `warnings.total` là tổng; `activities` tối đa 10 dòng mới nhất từ `audit_logs`.
- `lastBackup` và `latestTemperature` là `null` khi chưa có.
- Số thẻ lấy từ `dashboard_summary(90)` (`product_count`) và `build_dashboard_snapshot(get_inventory(), warning_days=90)`, **giống bản Tkinter**.
- **Khác biệt có chủ ý:** `negativeStockRows` lấy từ `dashboard_summary()["negative_count"]` (đếm thật). Bản Tkinter đếm trên danh sách tồn dương nên luôn gần như 0 (chính code đã ghi chú). Test parity loại trường này.
- Lỗi: `{ "success": false, "message": "..." }` kèm mã HTTP đúng (401 chưa xác thực, 403 sai scope/Host/Origin, 404, 500 không rò thông tin nội bộ).

## 7. Hệ thiết kế và component

- `tokens.css` hai lớp: **nguyên thủy** (dải màu, thang khoảng cách) và **ngữ nghĩa** (`--surface`, `--text`, `--primary`, `--success-bg`…). Component chỉ dùng lớp ngữ nghĩa. Giá trị chuyển 1:1 từ `ui_design.py` (nền `#F3F6F9`, chủ đạo `#0D3B66`, hàng bảng 34px, chữ Segoe UI hệ thống, không tải font web).
- Đơn vị `rem`; ở màn hình dưới 640px, vùng chạm tối thiểu 44px (để P4 dùng lại).
- Component P1: `AppShell`, `Button` (primary/secondary), `Panel`, `MetricCard`, `Badge` (success/warning/danger/info), `DataTable` (tiêu đề dính, điều hướng bàn phím), `Toast`, `EmptyState`, `ErrorState`. `Modal` và `FormField` để P2.
- Điều hướng đủ 11 mục như `ui_design.NAV_ITEMS`; phím F1–F12 giữ nguyên, chặn mặc định F5 (tải lại) và F12 (devtools). Chỉ "Tổng quan" hoạt động; các mục khác hiện "Chưa có trong giao diện mới, mở bằng bản Tkinter".
- Truy cập: vòng focus rõ (`:focus-visible`), tương phản chữ/nền tối thiểu 4.5:1.

## 8. Khởi chạy, đóng gói và CI

- Chạy: `python quanly_web.py` hoặc `run_web.bat`. Cửa sổ 1366×800, tối thiểu 1024×640. Đóng cửa sổ thì dừng server. Thiếu WebView2: in hướng dẫn cài bằng tiếng Việt và thoát mã 1.
- Thêm `pywebview` (phiên bản ghim, chốt trong kế hoạch) vào `requirements.txt`; `pip-audit` trong CI vẫn là cổng chặn.
- Build: bản mới `dist/QuanLyKhoWeb/` (PyInstaller onedir, kèm `web/`, hidden-import `webview`), tách khỏi `dist/QuanLyKho/` của Tkinter, dùng chung DB. Tái dùng SHA256 manifest và bộ kiểm tra bản phát hành.
- Smoke test đóng gói: `QuanLyKhoWeb.exe --smoke` khởi cổng cục bộ, mở cửa sổ, chờ Tổng quan render, đọc DOM qua `evaluate_js`, xác nhận không có lỗi console hay vi phạm CSP, thoát mã 0.

## 9. Kiểm thử

Test Python (không cần Node), chạy trong `unittest discover`:

| File | Kiểm tra |
|---|---|
| `test_webapp_routing.py` | Route `local` bị từ chối từ listener `lan`; 404/405 |
| `test_webapp_local_auth.py` | Boot token dùng một lần; cookie; chặn Host/Origin sai; request thiếu cookie → 401 |
| `test_webapp_static.py` | Chặn `..`, đường dẫn tuyệt đối, liên kết tượng trưng, phần mở rộng lạ; header bảo mật |
| `test_webapp_dashboard.py` | Số liệu API khớp `build_dashboard_snapshot` trên DB tạm (trừ `negativeStockRows`); hợp đồng JSON; thông báo lỗi không rò nội bộ |
| `test_web_assets_policy.py` | Tương phản các cặp màu trong `tokens.css` đạt WCAG AA; cấm `innerHTML`/`eval`/`new Function`/`on*=`/script inline trong `web/`; `nav.js` khớp `ui_design.NAV_ITEMS` |

Cộng smoke test đóng gói ở mục 8. Test Tkinter hiện có (kể cả `test_ui_dashboard.py`) giữ nguyên và phải xanh.

## 10. Rủi ro và phương án dự phòng

| Rủi ro | Xử lý |
|---|---|
| pywebview trên Windows dựa vào `pythonnet` và WebView2; đóng gói PyInstaller hoặc chạy trên runner CI có thể lỗi | **Tác vụ đầu tiên của kế hoạch là spike bỏ đi**: gói cửa sổ "hello" bằng PyInstaller và chạy trong CI. Nếu thất bại, dùng chế độ `msedge --app=<URL>` (không cần thư viện) với hồ sơ tạm riêng, phát hiện đóng cửa sổ bằng chờ tiến trình |
| Máy người dùng chưa có WebView2 | Thông báo hướng dẫn cài; bộ cài có thể kèm runtime (quyết định ở kế hoạch phát hành) |
| Preact/htm đặt sẵn lệch phiên bản hoặc không còn bảo trì | Ghim phiên bản và giấy phép trong `web/js/vendor/`; thư viện nhỏ, thay thế được |
| Hai UI song song làm lệch dữ liệu hiển thị | Test parity ở mục 9; cùng dùng một hàm `build_dashboard_snapshot` |

## 11. Tiêu chí hoàn thành

1. Toàn bộ test (cũ và mới) pass trên venv theo pin; `ui_smoke_check.py` của Tkinter vẫn OK.
2. `dist/QuanLyKhoWeb/QuanLyKhoWeb.exe` build được; smoke test đóng gói pass trong CI.
3. Trên **bản sao** `pharm.db` thật, Tổng quan web hiện các thẻ và danh sách cảnh báo **trùng** bản Tkinter (đối chiếu thủ công).
4. `pip-audit` sạch; không còn lệnh cấm trong `web/` (mục 9).
5. Hành vi bản Tkinter và `server.py` không đổi.

## 12. Chi tiết để lại cho kế hoạch (không phải điểm mơ hồ về thiết kế)

Số phiên bản cụ thể của `pywebview`, `preact`, `htm`; tên cờ dòng lệnh của bản build; chi tiết kịch bản spike. Thiết kế ở trên đủ để lập kế hoạch mà không cần quyết định lại.
