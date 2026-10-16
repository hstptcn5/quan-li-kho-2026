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
