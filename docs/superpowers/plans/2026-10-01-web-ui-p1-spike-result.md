# Kết quả spike pywebview (P1)

Ngày chạy: 2026-10-01

| Hạng mục | Kết quả |
|---|---|
| Phiên bản pywebview | 6.2.1 |
| Phiên bản pythonnet / clr_loader | 3.1.0 / 0.3.1 |
| PyInstaller dùng cho spike | 6.22.3 |
| pip-audit (`pywebview==6.2.1` và phụ thuộc) | No known vulnerabilities found (cảnh báo `setuptools 65.5.0` trong venv mới tạo không thuộc phụ thuộc của pywebview) |
| WebView2 Runtime trên máy chạy spike | 154.0.4258.37 |
| Chạy từ mã nguồn (Step 3) | SPIKE_OK (exit 0) |
| Chạy bản PyInstaller (Step 4) | SPIKE_OK (exit 0), không cần cờ `--collect-all`/`--hidden-import` bổ sung |
| Chạy trên runner CI (Step 5) | chưa kiểm chứng: cần push nhánh tạm lên GitHub (cần chủ dự án đồng ý); CI của PR thật (build + smoke đóng gói web) sẽ là bằng chứng |
| Runner có sẵn WebView2 | chưa rõ; workflow chính có bước "Ensure WebView2 runtime" tự cài khi thiếu |

Đã kiểm chứng: `webview.create_window(..., min_size=...)`, `webview.start(func, window, gui="edgechromium", private_mode=True, debug=False)`, `window.evaluate_js(...)`, `window.destroy()` hoạt động đúng như Task 9 và Task 12 dùng; trang module script dưới CSP `default-src 'self'; script-src 'self'` chạy được trong WebView2.

**Quyết định:** TIẾP TỤC với pywebview 6.2.1 (ghim `pywebview==6.2.1` ở Task 9).
