MOBILE_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Kiểm Kho Di Động</title>
    <style>
        :root {
            --primary: #0479b8;
            --primary-hover: #036494;
            --bg-grad: linear-gradient(180deg, #eef8fc 0%, #dff1f8 100%);
            --glass-bg: rgba(255, 255, 255, 0.88);
            --glass-border: rgba(15, 23, 42, 0.08);
            --text-light: #0f172a;
            --text-muted: #475569;
            --success: #0d9488;
            --warning: #ea580c;
            --danger: #e11d48;
            --surface: #ffffff;
            --surface-soft: #f8fafc;
            --shadow-sm: 0 8px 24px rgba(15, 23, 42, 0.07);
            --shadow-focus: 0 10px 22px rgba(4, 121, 184, 0.18);
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
            -webkit-tap-highlight-color: transparent;
        }
        body {
            background: var(--bg-grad);
            color: var(--text-light);
            min-height: 100vh;
            padding: 14px 12px 18px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 500px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        header {
            text-align: left;
            padding: 4px 4px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        header h1 {
            font-size: 1.25rem;
            font-weight: 800;
            color: #075985;
            line-height: 1.15;
        }
        header p {
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        .app-mark {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            background: #075985;
            color: #fff;
            display: grid;
            place-items: center;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.3px;
            box-shadow: var(--shadow-focus);
            flex: 0 0 auto;
        }
        .nav-tabs {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            width: 100%;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--glass-border);
            border-radius: 14px;
            padding: 5px;
            box-shadow: var(--shadow-sm);
        }
        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 9px 5px;
            font-size: 0.76rem;
            font-weight: 700;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.18s;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3px;
            min-height: 48px;
        }
        .tab-btn span {
            display: inline;
        }
        .tab-icon {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: currentColor;
            opacity: 0.55;
        }
        @media (max-width: 480px) {
            .tab-btn {
                padding: 8px 3px;
                font-size: 0.68rem;
            }
        }
        .tab-btn.active {
            background: var(--primary);
            color: #fff;
            box-shadow: var(--shadow-focus);
        }
        .tab-content {
            display: none;
            flex-direction: column;
            gap: 12px;
        }
        .tab-content.active {
            display: flex;
        }
        .card {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 14px;
            padding: 15px;
            box-shadow: var(--shadow-sm);
        }
        .section-title {
            font-size: 0.98rem;
            font-weight: 800;
            color: var(--text-light);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            border-bottom: 1px solid var(--glass-border);
            padding-bottom: 10px;
            margin-bottom: 12px;
        }
        .dashboard-card {
            padding: 14px;
        }
        .dashboard-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }
        .dashboard-title {
            font-weight: 800;
            color: #075985;
            font-size: 0.94rem;
        }
        .refresh-link {
            border: 1px solid var(--glass-border);
            background: var(--surface-soft);
            color: var(--text-muted);
            border-radius: 8px;
            padding: 6px 8px;
            cursor: pointer;
            font-size: 0.75rem;
            font-weight: 700;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            text-align: left;
        }
        .stat-tile {
            background: var(--surface-soft);
            border: 1px solid var(--glass-border);
            padding: 10px;
            border-radius: 10px;
        }
        .stat-tile.clickable {
            cursor: pointer;
        }
        .stat-label {
            font-size: 0.7rem;
            color: var(--text-muted);
            font-weight: 700;
            line-height: 1.2;
        }
        .stat-value {
            font-size: 1.18rem;
            font-weight: 850;
            color: var(--text-light);
            margin-top: 6px;
            line-height: 1;
        }
        .stat-danger { color: var(--danger); }
        .stat-warning { color: #d97706; }
        .scanner-card {
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        #reader {
            width: 100% !important;
            border: none !important;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
        }
        #reader button {
            background: var(--primary) !important;
            color: #fff !important;
            border: none !important;
            padding: 8px 16px !important;
            border-radius: 8px !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            margin: 10px 0 !important;
            transition: background 0.2s !important;
        }
        #reader button:hover {
            background: var(--primary-hover) !important;
        }
        #reader select {
            background: rgba(255, 255, 255, 0.8) !important;
            color: var(--text-light) !important;
            border: 1px solid var(--glass-border) !important;
            padding: 8px !important;
            border-radius: 8px !important;
            margin: 5px 0 !important;
            width: 90% !important;
        }
        .search-box {
            display: flex;
            gap: 8px;
        }
        .search-box input {
            flex: 1;
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            padding: 10px 12px;
            color: var(--text-light);
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }
        .search-box input:focus {
            border-color: var(--primary);
        }
        .search-box button {
            background: var(--primary);
            border: none;
            border-radius: 8px;
            color: #fff;
            padding: 0 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .search-box button:hover {
            background: var(--primary-hover);
        }
        .result-title {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            color: var(--text-light);
            border-bottom: 1px solid var(--glass-border);
            padding-bottom: 8px;
        }
        .product-info {
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
            margin-bottom: 12px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
        }
        .info-label {
            color: var(--text-muted);
        }
        .info-value {
            font-weight: 600;
            color: var(--text-light);
        }
        .batch-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .batch-item {
            background: rgba(255, 255, 255, 0.45);
            border: 1px solid rgba(2, 132, 199, 0.08);
            border-radius: 10px;
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .batch-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .batch-lot {
            font-weight: 700;
            color: #0369a1;
            font-size: 0.95rem;
        }
        .batch-qty {
            font-size: 1.1rem;
            font-weight: 800;
            color: var(--success);
        }
        .batch-expiry {
            font-size: 0.8rem;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge-expired {
            background: rgba(225, 29, 72, 0.12);
            color: var(--danger);
            border: 1px solid rgba(225, 29, 72, 0.2);
        }
        .badge-warning {
            background: rgba(234, 88, 12, 0.12);
            color: var(--warning);
            border: 1px solid rgba(234, 88, 12, 0.2);
        }
        .badge-ok {
            background: rgba(13, 148, 136, 0.12);
            color: var(--success);
            border: 1px solid rgba(13, 148, 136, 0.2);
        }
        
        .action-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 15px;
            border-top: 1px solid var(--glass-border);
            padding-top: 15px;
        }
        .action-btn {
            padding: 10px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            color: #fff;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            font-size: 0.85rem;
            transition: opacity 0.2s, transform 0.1s;
        }
        .action-btn:active {
            transform: scale(0.97);
        }
        .btn-purchase { background: var(--success); }
        .btn-dispatch { background: var(--danger); }
        .btn-barcode { background: var(--warning); grid-column: span 2; }
        
        .form-container {
            margin-top: 15px;
            padding: 12px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.5);
            border: 1px dashed rgba(2, 132, 199, 0.2);
            display: none;
        }
        .form-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-light);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .form-group {
            margin-bottom: 10px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .form-group label {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 600;
        }
        .form-control {
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid var(--glass-border);
            border-radius: 6px;
            padding: 8px 10px;
            color: var(--text-light);
            font-size: 0.9rem;
            outline: none;
        }
        .form-control:focus {
            border-color: var(--primary);
        }
        .form-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }
        .form-actions button {
            flex: 1;
            padding: 8px;
            border-radius: 6px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.85rem;
        }
        .btn-submit { background: var(--primary); color: #fff; }
        .btn-cancel { background: rgba(0, 0, 0, 0.05); color: var(--text-light); }
        
        .product-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 50vh;
            overflow-y: auto;
            margin-top: 8px;
            padding-right: 2px;
        }
        .product-item {
            background: var(--surface);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 12px;
            cursor: pointer;
            transition: border-color 0.2s, box-shadow 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .product-item:hover {
            border-color: rgba(4, 121, 184, 0.22);
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
        }
        .product-item-details {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .product-item-name {
            font-weight: 600;
            color: var(--text-light);
            font-size: 0.9rem;
        }
        .product-item-sub {
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        .product-item-arrow {
            color: var(--text-muted);
            font-size: 1.1rem;
        }
        .activity-item {
            cursor: default;
            flex-direction: column;
            align-items: stretch;
            gap: 10px;
        }
        .activity-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }
        .status-pill {
            font-size: 0.7rem;
            line-height: 1;
            font-weight: 800;
            padding: 6px 8px;
            border-radius: 999px;
            letter-spacing: 0.2px;
        }
        .status-pill.purchase {
            background: rgba(13, 148, 136, 0.1);
            color: #0f766e;
            border: 1px solid rgba(13, 148, 136, 0.2);
        }
        .status-pill.dispatch {
            background: rgba(225, 29, 72, 0.1);
            color: #be123c;
            border: 1px solid rgba(225, 29, 72, 0.18);
        }
        .activity-time {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 700;
        }
        .activity-note {
            font-weight: 800;
            font-size: 0.94rem;
            color: var(--text-light);
        }
        .activity-partner {
            font-size: 0.8rem;
            color: var(--text-muted);
            line-height: 1.35;
        }
        .activity-action {
            width: 100%;
            padding: 9px 10px;
            background: var(--primary);
            border: none;
            border-radius: 9px;
            color: #fff;
            font-weight: 800;
            font-size: 0.8rem;
            cursor: pointer;
        }
        
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 23, 42, 0.45);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.25s ease-out;
        }
        .modal-content {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 24px;
            width: 90%;
            max-width: 380px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(2, 132, 199, 0.12);
            animation: scaleIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .modal-icon {
            font-size: 3rem;
            margin-bottom: 12px;
        }
        .modal-content h3 {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--text-light);
        }
        .modal-content p {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 20px;
            line-height: 1.4;
        }
        .modal-actions {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .btn-modal-print {
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 10px;
            font-weight: bold;
            font-size: 0.95rem;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn-modal-print:hover {
            background: var(--primary-hover);
        }
        .btn-modal-close {
            background: rgba(0, 0, 0, 0.05);
            color: var(--text-light);
            border: 1px solid var(--glass-border);
            padding: 12px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-modal-close:hover {
            background: rgba(0, 0, 0, 0.08);
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes scaleIn {
            from { transform: scale(0.9); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .cart-item-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: rgba(2, 132, 199, 0.04);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            margin-bottom: 8px;
        }
        .cart-item-details {
            flex: 1;
        }
        .cart-item-name {
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--text-light);
        }
        .cart-item-meta {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 2px;
        }
        .btn-cart-remove {
            background: none;
            border: none;
            color: #ef4444;
            font-size: 1.1rem;
            cursor: pointer;
            padding: 4px 8px;
            transition: opacity 0.2s;
        }
        .btn-cart-remove:hover {
            opacity: 0.7;
        }
        .preview-table th, .preview-table td {
            padding: 8px 10px;
            border-bottom: 1px solid var(--glass-border);
            color: var(--text-light);
        }
        .preview-table tbody tr:last-child td {
            border-bottom: none;
        }
        
        #toast-container {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 9999;
            width: 90%;
            max-width: 320px;
        }
        .toast {
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--glass-border);
            backdrop-filter: blur(10px);
            border-radius: 8px;
            padding: 10px 14px;
            color: #fff;
            font-size: 0.8rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            animation: slideUp 0.3s ease forwards;
        }
        .toast-success { border-left: 4px solid var(--success); }
        .toast-error { border-left: 4px solid var(--danger); }
        
        .no-result, .loading, .error-msg {
            text-align: center;
            padding: 20px;
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        .error-msg {
            color: var(--danger);
        }
        .loading-spinner {
            border: 3px solid rgba(255,255,255,0.1);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 26px;
            height: 26px;
            animation: spin 1s linear infinite;
            margin: 10px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .report-table-wrapper {
            overflow-x: auto;
            margin-top: 10px;
            border-radius: 8px;
            border: 1px solid var(--glass-border);
            background: #fff;
        }
        .report-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.78rem;
            text-align: left;
            table-layout: fixed;
        }
        .report-table th, .report-table td {
            padding: 7px 6px;
            border-bottom: 1px solid rgba(0,0,0,0.06);
            white-space: normal;
            overflow-wrap: anywhere;
            vertical-align: top;
        }
        .report-table th {
            background: rgba(2, 132, 199, 0.06);
            font-weight: 700;
            color: var(--primary);
        }
        .report-table tbody tr:last-child td {
            border-bottom: none;
        }
        .report-table tr:nth-child(even) {
            background: rgba(0,0,0,0.01);
        }
        .temp-status-alert {
            background: rgba(225, 29, 72, 0.08) !important;
            color: var(--danger) !important;
            border-left: 3px solid var(--danger) !important;
        }
    </style>
</head>
<body>
    <div id="toast-container"></div>

    <!-- Print Success Modal -->
    <div id="print-modal" class="modal-overlay" style="display: none;">
        <div class="modal-content">
            <div class="modal-icon">✅</div>
            <h3 id="print-modal-title">Thành công</h3>
            <p id="print-modal-message">Đã thực hiện thành công.</p>
            <div class="modal-actions">
                <button id="btn-modal-print-pc" class="btn-modal-print" style="background: #10b981;">
                    🖥️ In qua máy tính (PC)
                </button>
                <button id="btn-modal-print-phone" class="btn-modal-print">
                    📱 In/Tải về trên ĐT
                </button>
                <button class="btn-modal-close" onclick="closePrintModal()">Đóng</button>
            </div>
        </div>
    </div>

    <!-- Cart Review Modal -->
    <div id="cart-modal" class="modal-overlay" style="display: none;">
        <div class="modal-content" style="max-width: 440px; text-align: left;">
            <h3 id="cart-modal-title" style="text-align: center; margin-bottom: 12px; color: var(--primary);">🛒 Giỏ Hàng</h3>
            
            <div id="cart-items-container" style="max-height: 200px; overflow-y: auto; margin-bottom: 15px; border-bottom: 1px solid var(--glass-border); padding-bottom: 10px;">
            </div>
            
            <div id="cart-form-fields">
                <div class="form-group" style="margin-bottom: 10px;">
                    <label id="cart-partner-label" style="font-weight: 600; font-size: 0.85rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Đối tác *</label>
                    <select id="cart-partner-select" class="form-control" style="width: 100%;" onchange="toggleCartCustomPartner()"></select>
                    <input type="text" id="cart-partner-input" class="form-control" style="display: none; margin-top: 6px;" placeholder="Nhập tên đối tác..." />
                </div>
                <div class="form-group" style="margin-bottom: 10px;">
                    <label id="cart-reason-label" style="font-weight: 600; font-size: 0.85rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Lý do thực hiện *</label>
                    <input type="text" id="cart-reason-input" class="form-control" placeholder="Lý do..." />
                </div>
                <div class="form-group" style="margin-bottom: 15px;">
                    <label style="font-weight: 600; font-size: 0.85rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Ghi chú</label>
                    <input type="text" id="cart-note-input" class="form-control" placeholder="Ghi chú thêm..." />
                </div>
            </div>
            
            <div class="modal-actions" style="margin-top: 15px; gap: 8px;">
                <button id="btn-cart-submit-pc" class="btn-modal-print" style="background: #10b981;">
                    🖥️ Tạo phiếu & In PC
                </button>
                <button id="btn-cart-submit-phone" class="btn-modal-print">
                    📱 Tạo phiếu & In ĐT
                </button>
                <button class="btn-modal-close" onclick="closeCartModal()">Đóng</button>
            </div>
        </div>
    </div>

    <!-- Note Preview Modal -->
    <div id="preview-modal" class="modal-overlay" style="display: none;">
        <div class="modal-content" style="max-width: 460px; text-align: left;">
            <h3 id="preview-modal-title" style="text-align: center; margin-bottom: 12px; color: var(--primary);">📋 Xem Trước Phiếu</h3>
            
            <div id="preview-info-container" style="font-size: 0.85rem; line-height: 1.5; margin-bottom: 12px; background: rgba(0,0,0,0.02); padding: 10px; border-radius: 10px; border: 1px solid var(--glass-border);">
            </div>
            
            <div style="font-weight: 600; font-size: 0.85rem; color: var(--text-light); margin-bottom: 6px;">Danh sách sản phẩm:</div>
            <div id="preview-items-container" style="max-height: 180px; overflow-y: auto; margin-bottom: 15px; border: 1px solid var(--glass-border); border-radius: 8px; background: #fff;">
                <table class="preview-table" style="width: 100%; border-collapse: collapse; font-size: 0.8rem;">
                    <thead>
                        <tr style="background: rgba(2, 132, 199, 0.08); border-bottom: 1px solid var(--glass-border);">
                            <th style="padding: 6px 8px; text-align: left;">Tên sản phẩm</th>
                            <th style="padding: 6px 8px; text-align: center; width: 65px;">Lô</th>
                            <th style="padding: 6px 8px; text-align: right; width: 65px;">SL</th>
                        </tr>
                    </thead>
                    <tbody id="preview-table-body">
                    </tbody>
                </table>
            </div>
            
            <div class="modal-actions" style="margin-top: 15px; gap: 8px;">
                <button id="btn-preview-submit-pc" class="btn-modal-print" style="background: #10b981;">
                    🖥️ Xác nhận In PC
                </button>
                <button id="btn-preview-submit-phone" class="btn-modal-print">
                    📱 Tải về / Xem PDF ĐT
                </button>
                <button class="btn-modal-close" onclick="closePreviewModal()">Đóng</button>
            </div>
        </div>
    </div>

    <div class="container">
        <header>
            <div class="app-mark">XNT</div>
            <div>
                <h1>Quản lý kho di động</h1>
                <p>Kiểm kho, nhập xuất và liên kết mã vạch</p>
            </div>
        </header>

        <div class="card dashboard-card">
            <div class="dashboard-head">
                <div class="dashboard-title">Tổng quan kho hàng</div>
                <button id="dashboard-refresh" class="refresh-link" onclick="loadDashboardStats()">Cập nhật</button>
            </div>
            <div class="stat-grid">
                <div class="stat-tile">
                    <div class="stat-label">Tổng sản phẩm</div>
                    <div id="dash-total-products" class="stat-value">0</div>
                </div>
                <div class="stat-tile clickable" onclick="filterCatalog('outofstock')">
                    <div class="stat-label">Hết hàng</div>
                    <div id="dash-outofstock-products" class="stat-value stat-danger">0</div>
                </div>
                <div class="stat-tile clickable" onclick="filterCatalog('expiring')">
                    <div class="stat-label">Cận hạn</div>
                    <div id="dash-expiring-products" class="stat-value stat-warning">0</div>
                </div>
            </div>
        </div>

        <div class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('tab-checker')"><i class="tab-icon"></i><span>Kiểm kho</span></button>
            <button class="tab-btn" onclick="switchTab('tab-temp')"><i class="tab-icon"></i><span>Nhiệt độ</span></button>
            <button class="tab-btn" onclick="switchTab('tab-xnt')"><i class="tab-icon"></i><span>XNT</span></button>
            <button class="tab-btn" onclick="switchTab('tab-catalog')"><i class="tab-icon"></i><span>Danh sách</span></button>
            <button class="tab-btn" onclick="switchTab('tab-history')"><i class="tab-icon"></i><span>Lịch sử</span></button>
        </div>

        <div id="cart-status-bar" style="display: none; gap: 8px; width: 100%; margin-top: 5px; margin-bottom: 10px;">
            <div id="cart-purchase-btn" onclick="openCartModal('purchase')" style="flex: 1; background: #0d9488; color: #fff; padding: 10px; border-radius: 12px; font-weight: bold; text-align: center; font-size: 0.82rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.15);">
                📥 Giỏ Nhập: <span id="cart-purchase-count">0</span> món
            </div>
            <div id="cart-dispatch-btn" onclick="openCartModal('dispatch')" style="flex: 1; background: #e11d48; color: #fff; padding: 10px; border-radius: 12px; font-weight: bold; text-align: center; font-size: 0.82rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 4px 12px rgba(225, 29, 72, 0.15);">
                📤 Giỏ Xuất: <span id="cart-dispatch-count">0</span> món
            </div>
        </div>

        <div id="tab-checker" class="tab-content active">
            <div class="card scanner-card">
                <div id="reader"></div>
            </div>

            <div class="card">
                <div class="search-box">
                    <input type="text" id="barcode-input" placeholder="Nhập mã vạch hoặc tên..." />
                    <button id="search-btn">Tìm</button>
                </div>
            </div>

            <div class="card" id="result-card" style="display: none;">
                <div class="section-title">Kết quả truy vấn</div>
                <div id="result-content"></div>
                
                <div id="action-forms">
                    <div id="form-purchase" class="form-container">
                        <div class="form-title">📥 Nhập kho nhanh</div>
                        <div class="form-group">
                            <label>Nhà cung cấp</label>
                            <select id="pur-supplier" class="form-control" onchange="toggleCustomSupplier()"></select>
                            <input type="text" id="pur-supplier-custom" class="form-control" style="display: none; margin-top: 6px;" placeholder="Nhập nhà cung cấp mới..." />
                        </div>
                        <div class="form-group">
                            <label>Nguồn kinh phí</label>
                            <select id="pur-fund" class="form-control" onchange="toggleCustomFund()"></select>
                            <input type="text" id="pur-fund-custom" class="form-control" style="display: none; margin-top: 6px;" placeholder="Nhập nguồn kinh phí mới..." />
                        </div>
                        <div class="form-group">
                            <label>Số lượng nhập (Đơn vị tính gốc)</label>
                            <input type="number" id="pur-qty" class="form-control" placeholder="Ví dụ: 10" step="any" required />
                        </div>
                        <div class="form-group">
                            <label>Số lô (Lot No)</label>
                            <input type="text" id="pur-lot" class="form-control" placeholder="Ví dụ: LO1234" required />
                        </div>
                        <div class="form-group">
                            <label>Hạn sử dụng</label>
                            <input type="date" id="pur-expiry" class="form-control" required />
                        </div>
                        <div class="form-actions" style="display: flex; flex-direction: column; gap: 8px;">
                            <div style="display: flex; gap: 8px; width: 100%;">
                                <button class="btn-cancel" onclick="closeForms()" style="flex: 1; margin: 0; padding: 10px;">Hủy</button>
                                <button class="btn-submit" onclick="addToCart('purchase')" style="flex: 2; background: #0d9488; margin: 0; padding: 10px;">📥 Thêm vào giỏ</button>
                            </div>
                            <button class="btn-submit" onclick="submitPurchase()" style="width: 100%; margin: 0; padding: 10px;">Nhập & Tạo phiếu ngay</button>
                        </div>
                    </div>
                    
                    <div id="form-dispatch" class="form-container">
                        <div class="form-title">📤 Xuất kho nhanh</div>
                        <div class="form-group">
                            <label>Đơn vị nhận</label>
                            <select id="disp-unit" class="form-control" onchange="toggleCustomDispatchUnit()"></select>
                            <input type="text" id="disp-unit-custom" class="form-control" style="display: none; margin-top: 6px;" placeholder="Nhập đơn vị nhận mới..." />
                        </div>
                        <div class="form-group">
                            <label>Chọn lô xuất</label>
                            <select id="disp-batch-id" class="form-control" onchange="onDispatchBatchChange()"></select>
                        </div>
                        <div class="form-group">
                            <label>Nguồn xuất</label>
                            <select id="disp-fund" class="form-control"></select>
                        </div>
                        <div class="form-group">
                            <label>Số lượng xuất (Đơn vị tính gốc)</label>
                            <input type="number" id="disp-qty" class="form-control" placeholder="Ví dụ: 5" step="any" required />
                        </div>
                        <div class="form-group">
                            <label>Lý do xuất</label>
                            <input type="text" id="disp-reason" class="form-control" placeholder="Ví dụ: Hao hụt, Cấp phát di động,..." value="Xuất qua điện thoại" />
                        </div>
                        <div class="form-actions" style="display: flex; flex-direction: column; gap: 8px;">
                            <div style="display: flex; gap: 8px; width: 100%;">
                                <button class="btn-cancel" onclick="closeForms()" style="flex: 1; margin: 0; padding: 10px;">Hủy</button>
                                <button class="btn-submit" onclick="addToCart('dispatch')" style="flex: 2; background: #e11d48; margin: 0; padding: 10px;">📤 Thêm vào giỏ</button>
                            </div>
                            <button class="btn-submit" onclick="submitDispatch()" style="width: 100%; margin: 0; padding: 10px;">Xuất & Tạo phiếu ngay</button>
                        </div>
                    </div>

                    <div id="form-barcode" class="form-container">
                        <div class="form-title">🏷️ Khai báo mã vạch mới</div>
                        <div class="form-group">
                            <label>Mã vạch liên kết</label>
                            <input type="text" id="link-barcode" class="form-control" placeholder="Quét hoặc điền mã vạch..." required />
                        </div>
                        <div class="form-actions">
                            <button class="btn-cancel" onclick="closeForms()">Hủy</button>
                            <button class="btn-submit" onclick="submitLinkBarcode()">Lưu Liên Kết</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div id="tab-temp" class="tab-content">
            <div class="card">
                <div class="section-title">Nhật ký nhiệt độ và độ ẩm</div>
                <div class="form-group">
                    <label>Ngày ghi nhận</label>
                    <input type="date" id="temp-date" class="form-control" required />
                </div>
                <div class="form-group">
                    <label>Buổi ghi nhận</label>
                    <select id="temp-session" class="form-control">
                        <option value="Sáng">Sáng</option>
                        <option value="Chiều">Chiều</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Vị trí bảo quản</label>
                    <select id="temp-location-select" class="form-control" onchange="toggleCustomTempLocation()"></select>
                    <input type="text" id="temp-location-custom" class="form-control" style="display: none; margin-top: 6px;" placeholder="Nhập tên tủ/kho mới..." />
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div class="form-group">
                        <label>Nhiệt độ (°C) *</label>
                        <input type="number" id="temp-val" class="form-control" placeholder="Ví dụ: 5.2" step="any" required />
                    </div>
                    <div class="form-group">
                        <label>Độ ẩm (%)</label>
                        <input type="number" id="temp-humidity" class="form-control" placeholder="Ví dụ: 60" step="any" />
                    </div>
                </div>
                <div class="form-group">
                    <label>Người ghi nhận</label>
                    <input type="text" id="temp-recorded-by" class="form-control" placeholder="Tên người ghi..." />
                </div>
                <button class="btn-submit" style="width: 100%; margin-top: 10px; padding: 12px; border-radius: 8px;" onclick="submitTemperatureLog()">💾 Lưu chỉ số</button>
            </div>

            <div class="card">
                <div class="section-title">Nhật ký đo gần đây</div>
                <div style="display: flex; gap: 8px; margin-bottom: 10px;">
                    <input type="month" id="temp-filter-month" class="form-control" style="flex: 1;" onchange="loadTemperatureLogs()" />
                    <select id="temp-filter-location" class="form-control" style="flex: 1;" onchange="loadTemperatureLogs()"></select>
                </div>
                <div id="temp-logs-list" style="display: flex; flex-direction: column; gap: 8px; max-height: 250px; overflow-y: auto;">
                    <div style="text-align: center; color: var(--text-muted); padding: 15px;">Đang tải nhật ký...</div>
                </div>
            </div>
        </div>

        <div id="tab-xnt" class="tab-content">
            <div class="card">
                <div class="section-title">Tra cứu xuất nhập tồn</div>
                <div class="form-group">
                    <label>Chọn tháng tra cứu</label>
                    <input type="month" id="xnt-filter-month" class="form-control" required />
                </div>
                <div class="form-group">
                    <label>Nguồn kinh phí</label>
                    <select id="xnt-filter-fund" class="form-control"></select>
                </div>
                <button class="btn-submit" style="width: 100%; margin-top: 10px; padding: 12px; border-radius: 8px;" onclick="loadXNTReport()">📊 Xem báo cáo</button>
            </div>

            <div class="card" id="xnt-report-card" style="display: none;">
                <div class="section-title">Bảng số liệu XNT</div>
                <div class="report-table-wrapper">
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>Tên hàng / Vật tư</th>
                                <th>Số lô / Nguồn</th>
                                <th style="text-align: right;">Đầu kỳ</th>
                                <th style="text-align: right;">Nhập</th>
                                <th style="text-align: right;">Xuất</th>
                                <th style="text-align: right;">Cuối kỳ</th>
                            </tr>
                        </thead>
                        <tbody id="xnt-report-body">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="tab-catalog" class="tab-content">
            <div class="card">
                <button class="action-btn" style="margin-bottom: 12px; width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px; background: var(--primary); font-size: 0.9rem;" onclick="openCreateProductForm()">Thêm sản phẩm mới</button>
                
                <div id="form-create-product" class="form-container" style="margin-bottom: 15px; border-style: solid; border-color: var(--primary);">
                    <div class="form-title">➕ Thêm sản phẩm mới</div>
                    <div class="form-group">
                        <label>Tên sản phẩm *</label>
                        <input type="text" id="new-name" class="form-control" placeholder="Ví dụ: Paracetamol 500mg" required />
                    </div>
                    <div class="form-group">
                        <label>Đơn vị tính gốc *</label>
                        <input type="text" id="new-unit" class="form-control" placeholder="Ví dụ: Viên, Hộp, Chai" required />
                    </div>
                    <div class="form-group">
                        <label>Phân loại sản phẩm</label>
                        <select id="new-type" class="form-control">
                            <option value="thuoc">Thuốc / Dược phẩm</option>
                            <option value="vaccine">Vaccine</option>
                            <option value="vtyt">Vật tư y tế</option>
                            <option value="khac">Sản phẩm khác</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Mã vạch (Quét hoặc điền)</label>
                        <input type="text" id="new-barcode" class="form-control" placeholder="Để trống nếu chưa có" />
                    </div>
                    <div class="form-group">
                        <label>Số đăng ký (Không bắt buộc)</label>
                        <input type="text" id="new-regnumber" class="form-control" placeholder="Số đăng ký..." />
                    </div>
                    <div class="form-actions">
                        <button class="btn-cancel" onclick="closeCreateProductForm()">Hủy</button>
                        <button class="btn-submit" onclick="submitCreateProduct()">Tạo & Nhập Kho</button>
                    </div>
                </div>

                <div class="search-box">
                    <input type="text" id="catalog-search" placeholder="Nhập tên sản phẩm..." />
                    <button id="catalog-search-btn">Lọc</button>
                </div>
                <div class="filter-toggles" style="display: flex; gap: 6px; margin-bottom: 12px; font-size: 0.8rem; margin-top: -6px;">
                    <button id="filter-btn-all" onclick="filterCatalog('all')" style="flex: 1; padding: 8px 6px; border: 1px solid var(--primary); background: var(--primary); color: #fff; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 0.75rem; transition: all 0.2s;">Tất cả</button>
                    <button id="filter-btn-outofstock" onclick="filterCatalog('outofstock')" style="flex: 1; padding: 8px 6px; border: 1px solid var(--glass-border); background: #fff; color: #ef4444; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 0.75rem; transition: all 0.2s;">❌ Hết Hàng</button>
                    <button id="filter-btn-expiring" onclick="filterCatalog('expiring')" style="flex: 1; padding: 8px 6px; border: 1px solid var(--glass-border); background: #fff; color: #f59e0b; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 0.75rem; transition: all 0.2s;">⚠️ Cận Hạn</button>
                </div>
                <div id="catalog-list" class="product-list"></div>
            </div>
        </div>
        
        <div id="tab-history" class="tab-content">
            <div class="card">
                <div class="section-title">Lịch sử hoạt động gần đây</div>
                <div id="history-list" class="product-list">
                    <div style="text-align: center; color: var(--text-muted); padding: 20px;">Đang tải...</div>
                </div>
            </div>
        </div>
    <!-- Màn hình xác thực PIN (Lỗi 3) -->
    <div id="auth-modal" style="display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(12px); z-index: 9999; align-items: center; justify-content: center; padding: 20px;">
        <div class="card" style="width: 100%; max-width: 360px; text-align: center; border: 1px solid var(--glass-border); background: rgba(30, 41, 59, 0.7); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);">
            <div style="font-size: 3rem; margin-bottom: 10px;">🔐</div>
            <h2 style="font-size: 1.25rem; font-weight: bold; margin-bottom: 5px; color: #fff;">Xác thực thiết bị</h2>
            <p style="font-size: 0.875rem; color: var(--text-muted); margin-bottom: 20px;">Vui lòng nhập mã PIN hiển thị trên màn hình Desktop của thủ kho.</p>
            <div style="margin-bottom: 20px;">
                <input type="password" id="pin-input" inputmode="numeric" pattern="[0-9]*" maxlength="6" placeholder="Mã PIN 6 số" style="width: 100%; padding: 12px; font-size: 1.25rem; text-align: center; letter-spacing: 0.5em; border-radius: 8px; border: 1px solid var(--glass-border); background: rgba(15, 23, 42, 0.6); color: #fff; outline: none;">
            </div>
            <button id="auth-btn" onclick="submitPin()" style="width: 100%; padding: 12px; background: var(--primary); border: none; border-radius: 8px; color: white; font-weight: bold; font-size: 1rem; cursor: pointer; transition: all 0.2s;">Xác nhận</button>
            <div id="auth-error" style="color: #ef4444; font-size: 0.875rem; margin-top: 10px; font-weight: bold;"></div>
        </div>
    </div>

    <script src="/static/html5-qrcode.min.js"></script>
    <script>
        // Override fetch to include token and handle 401 (Lỗi 3)
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            const token = localStorage.getItem('inventory_token') || '';
            options.headers = options.headers || {};
            if (token) {
                options.headers['Authorization'] = `Bearer ${token}`;
            }
            if (typeof url === 'string') {
                // Tự động chuyển /api/pc-print từ GET sang POST
                if (url.startsWith('/api/pc-print')) {
                    try {
                        const parsed = new URL(url, window.location.origin);
                        const type = parsed.searchParams.get('type') || '';
                        const id = parsed.searchParams.get('id') || '';
                        url = '/api/pc-print';
                        options.method = 'POST';
                        options.headers['Content-Type'] = 'application/json';
                        options.body = JSON.stringify({ type: type, id: id });
                    } catch (e) {
                        console.error('Error rewriting print URL:', e);
                    }
                }
            }
            return originalFetch(url, options).then(response => {
                if (response.status === 401) {
                    localStorage.removeItem('inventory_token');
                    showAuthModal();
                    throw new Error('Unauthorized');
                }
                return response;
            });
        };

        function showAuthModal() {
            document.getElementById('pin-input').value = '';
            document.getElementById('auth-error').textContent = '';
            document.getElementById('auth-modal').style.setProperty('display', 'flex', 'important');
        }
        
        function hideAuthModal() {
            document.getElementById('auth-modal').style.setProperty('display', 'none', 'important');
        }

        function submitPin() {
            const pin = document.getElementById('pin-input').value.trim();
            const errorDiv = document.getElementById('auth-error');
            const authBtn = document.getElementById('auth-btn');
            errorDiv.textContent = '';
            
            if (pin.length === 0) {
                errorDiv.textContent = 'Vui lòng nhập mã PIN';
                return;
            }
            
            authBtn.disabled = true;
            authBtn.textContent = 'Đang xác thực...';
            
            originalFetch('/api/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin: pin })
            })
            .then(res => res.json())
            .then(data => {
                authBtn.disabled = false;
                authBtn.textContent = 'Xác nhận';
                if (data.success) {
                    localStorage.setItem('inventory_token', data.token);
                    hideAuthModal();
                    showToast('Xác thực PIN thành công', 'success');
                    updateCartStatus();
                    loadDashboardStats();
                    loadPartnersAndFunds();
                    switchTab('tab-scan');
                } else {
                    errorDiv.textContent = data.message || 'Mã PIN không đúng';
                }
            })
            .catch(err => {
                authBtn.disabled = false;
                authBtn.textContent = 'Xác nhận';
                errorDiv.textContent = 'Không thể kết nối đến máy chủ';
            });
        }

        document.addEventListener('DOMContentLoaded', () => {
            const token = localStorage.getItem('inventory_token');
            if (!token) {
                showAuthModal();
            } else {
                hideAuthModal();
            }
            
            // Lắng nghe sự kiện Enter cho mã PIN
            const pinIn = document.getElementById('pin-input');
            if (pinIn) {
                pinIn.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        submitPin();
                    }
                });
            }
        });

        const barcodeInput = document.getElementById('barcode-input');
        const searchBtn = document.getElementById('search-btn');
        const resultCard = document.getElementById('result-card');
        const resultContent = document.getElementById('result-content');
        
        let currentProduct = null;
        let currentProductBatches = [];

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            document.getElementById(tabId).classList.add('active');
            
            const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => btn.getAttribute('onclick').includes(tabId));
            if (activeBtn) {
                activeBtn.classList.add('active');
            }
            
            if (tabId === 'tab-catalog') {
                loadCatalog('');
            } else if (tabId === 'tab-history') {
                loadRecentActivities();
            } else if (tabId === 'tab-temp') {
                loadTemperatureLogs();
            } else if (tabId === 'tab-xnt') {
                loadXNTReport();
            }
        }

        function showToast(message, type = 'success') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            
            const iconSpan = document.createElement('span');
            iconSpan.textContent = type === 'success' ? '✅ ' : '❌ ';
            
            const msgSpan = document.createElement('span');
            msgSpan.textContent = message;
            
            toast.appendChild(iconSpan);
            toast.appendChild(msgSpan);
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'none';
                toast.offsetHeight;
                toast.style.animation = 'slideUp 0.3s ease reverse forwards';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        function showPrintModal(type, noteId, message) {
            document.getElementById('print-modal-message').textContent = message;
            
            const btnPc = document.getElementById('btn-modal-print-pc');
            const btnPhone = document.getElementById('btn-modal-print-phone');
            
            btnPc.onclick = function() {
                btnPc.disabled = true;
                btnPc.textContent = '⌛ Đang gửi...';
                
                fetch(`/api/pc-print?type=${type}&id=${noteId}`)
                    .then(res => res.json())
                    .then(data => {
                        btnPc.disabled = false;
                        btnPc.innerHTML = '🖥️ In qua máy tính (PC)';
                        if (data.success) {
                            showToast(data.message, "success");
                            closePrintModal();
                        } else {
                            showToast(data.message, "error");
                        }
                    })
                    .catch(err => {
                        btnPc.disabled = false;
                        btnPc.innerHTML = '🖥️ In qua máy tính (PC)';
                        showToast("Lỗi kết nối lệnh in PC", "error");
                    });
            };
            
            if (type === 'purchase') {
                document.getElementById('print-modal-title').textContent = 'Nhập Kho Thành Công';
                btnPhone.onclick = function() {
                    window.open(withAuthToken(`/api/print-purchase?id=${encodeURIComponent(noteId)}`), '_blank');
                    closePrintModal();
                };
            } else {
                document.getElementById('print-modal-title').textContent = 'Xuất Kho Thành Công';
                btnPhone.onclick = function() {
                    window.open(withAuthToken(`/api/print-dispatch?id=${encodeURIComponent(noteId)}`), '_blank');
                    closePrintModal();
                };
            }
            
            document.getElementById('print-modal').style.display = 'flex';
        }
        
        function closePrintModal() {
            document.getElementById('print-modal').style.display = 'none';
        }

        function withAuthToken(url) {
            const token = localStorage.getItem('inventory_token') || '';
            if (!token) return url;
            const sep = url.includes('?') ? '&' : '?';
            return `${url}${sep}token=${encodeURIComponent(token)}`;
        }

        function loadRecentActivities() {
            const historyList = document.getElementById('history-list');
            historyList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">Đang tải lịch sử...</div>`;
            
            fetch('/api/recent-activities')
                .then(res => res.json())
                .then(data => {
                    if (data.success && data.activities.length > 0) {
                        historyList.innerHTML = '';
                        data.activities.forEach(act => {
                            const dateStr = act.createdAt;
                            let formattedDate = dateStr;
                            try {
                                const parts = dateStr.split(' ');
                                const dateParts = parts[0].split('-');
                                formattedDate = `${dateParts[2]}/${dateParts[1]} ${parts[1].substring(0, 5)}`;
                            } catch(e) {}
                            
                            const item = document.createElement('div');
                            item.className = 'product-item activity-item';
                            
                            const isPurchase = act.type === 'nhap';
                            const typeClass = isPurchase ? 'purchase' : 'dispatch';
                            const typeLabel = isPurchase ? 'Nhập kho' : 'Xuất kho';
                            
                            item.innerHTML = `
                                <div class="activity-top">
                                    <span class="status-pill ${typeClass}">${typeLabel}</span>
                                    <span class="activity-time">${formattedDate}</span>
                                </div>
                                <div class="activity-note">Số phiếu: ${escapeHtml(act.noteNumber)}</div>
                                <div class="activity-partner">${isPurchase ? 'Nhà cung cấp' : 'Đơn vị nhận'}: ${escapeHtml(act.details)}</div>
                                <button class="activity-action" onclick="showNotePreview('${act.type}', ${act.id})">Xem trước và in phiếu</button>
                            `;
                            historyList.appendChild(item);
                        });
                    } else {
                        historyList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">Không có hoạt động gần đây</div>`;
                    }
                })
                .catch(err => {
                    historyList.innerHTML = `<div style="text-align: center; color: var(--danger); padding: 20px;">Lỗi tải dữ liệu</div>`;
                });
        }
        
        function printActivityPC(type, noteId, btn) {
            btn.disabled = true;
            const origText = btn.innerHTML;
            btn.textContent = '⌛...';
            
            fetch(`/api/pc-print?type=${type}&id=${noteId}`)
                .then(res => res.json())
                .then(data => {
                    btn.disabled = false;
                    btn.innerHTML = origText;
                    showToast(data.message, data.success ? "success" : "error");
                })
                .catch(err => {
                    btn.disabled = false;
                    btn.innerHTML = origText;
                    showToast("Lỗi gửi lệnh in PC", "error");
                });
        }
        
        function printActivityPhone(type, noteId) {
            const url = type === 'nhap'
                ? `/api/print-purchase?id=${encodeURIComponent(noteId)}`
                : `/api/print-dispatch?id=${encodeURIComponent(noteId)}`;
            window.open(withAuthToken(url), '_blank');
        }

        let purchaseCart = JSON.parse(localStorage.getItem('mob_purchase_cart')) || [];
        let dispatchCart = JSON.parse(localStorage.getItem('mob_dispatch_cart')) || [];

        function updateCartStatus() {
            const pCount = purchaseCart.length;
            const dCount = dispatchCart.length;
            
            document.getElementById('cart-purchase-count').textContent = pCount;
            document.getElementById('cart-dispatch-count').textContent = dCount;
            
            const statusBar = document.getElementById('cart-status-bar');
            const pBtn = document.getElementById('cart-purchase-btn');
            const dBtn = document.getElementById('cart-dispatch-btn');
            
            if (pCount > 0 || dCount > 0) {
                statusBar.style.display = 'flex';
                pBtn.style.display = pCount > 0 ? 'flex' : 'none';
                dBtn.style.display = dCount > 0 ? 'flex' : 'none';
            } else {
                statusBar.style.display = 'none';
            }
        }

        function addToCart(type) {
            if (!currentProduct) return;
            
            if (type === 'purchase') {
                const qty = parseFloat(document.getElementById('pur-qty').value);
                const lotNo = document.getElementById('pur-lot').value.trim();
                const expiry = document.getElementById('pur-expiry').value;
                
                const fundSelect = document.getElementById('pur-fund');
                let fundSource = fundSelect.value;
                if (fundSource === '__custom__') {
                    fundSource = document.getElementById('pur-fund-custom').value.trim();
                } else {
                    fundSource = fundSource.trim();
                }
                
                if (!qty || qty <= 0 || !lotNo || !expiry) {
                    showToast("Vui lòng điền đầy đủ thông tin nhập kho!", "error");
                    return;
                }
                
                const existingIdx = purchaseCart.findIndex(item => 
                    item.productId === currentProduct.id && 
                    item.lotNo === lotNo && 
                    (item.fundSource || '') === fundSource
                );
                if (existingIdx > -1) {
                    purchaseCart[existingIdx].qty += qty;
                } else {
                    purchaseCart.push({
                        productId: currentProduct.id,
                        productName: currentProduct.name,
                        unit: currentProduct.unit,
                        qty: qty,
                        lotNo: lotNo,
                        expiryDate: expiry,
                        fundSource: fundSource
                    });
                }
                localStorage.setItem('mob_purchase_cart', JSON.stringify(purchaseCart));
                showToast(`Đã thêm ${qty} ${currentProduct.unit} vào giỏ nhập`, "success");
                closeForms();
                updateCartStatus();
            } else if (type === 'dispatch') {
                const lotNo = document.getElementById('disp-batch-id').value;
                const qty = parseFloat(document.getElementById('disp-qty').value);
                const fundSource = document.getElementById('disp-fund').value;
                
                if (!lotNo || !qty || qty <= 0) {
                    showToast("Vui lòng điền đầy đủ thông tin xuất kho!", "error");
                    return;
                }
                
                const existingIdx = dispatchCart.findIndex(item => 
                    item.productId === currentProduct.id && 
                    item.lotNo === lotNo && 
                    (item.fundSource || '') === fundSource
                );
                if (existingIdx > -1) {
                    dispatchCart[existingIdx].qty += qty;
                } else {
                    dispatchCart.push({
                        productId: currentProduct.id,
                        productName: currentProduct.name,
                        unit: currentProduct.unit,
                        qty: qty,
                        lotNo: lotNo,
                        fundSource: fundSource
                    });
                }
                localStorage.setItem('mob_dispatch_cart', JSON.stringify(dispatchCart));
                showToast(`Đã thêm ${qty} ${currentProduct.unit} vào giỏ xuất`, "success");
                closeForms();
                updateCartStatus();
            }
        }

        let activeCartType = null;
        function openCartModal(type) {
            activeCartType = type;
            const container = document.getElementById('cart-items-container');
            container.innerHTML = '';
            
            const title = document.getElementById('cart-modal-title');
            const partnerLabel = document.getElementById('cart-partner-label');
            const partnerSelect = document.getElementById('cart-partner-select');
            const partnerInput = document.getElementById('cart-partner-input');
            const reasonInput = document.getElementById('cart-reason-input');
            const noteInput = document.getElementById('cart-note-input');
            
            const cart = type === 'purchase' ? purchaseCart : dispatchCart;
            
            let htmlPartner = `<option value="">-- Chọn đối tác --</option>`;
            const listPartners = type === 'purchase' ? partnersData.suppliers : partnersData.receivingUnits;
            listPartners.forEach(p => {
                htmlPartner += `<option value="${escapeHtml(p)}">${escapeHtml(p)}</option>`;
            });
            htmlPartner += `<option value="__custom__">Khác (Nhập tay)...</option>`;
            partnerSelect.innerHTML = htmlPartner;
            
            if (type === 'purchase') {
                title.textContent = '📥 Giỏ Hàng Nhập Kho';
                partnerLabel.textContent = 'Nhà cung cấp *';
                partnerInput.placeholder = 'Ví dụ: Công ty Dược CDC, ...';
                reasonInput.value = 'Nhập qua điện thoại';
            } else {
                title.textContent = '📤 Giỏ Hàng Xuất Kho';
                partnerLabel.textContent = 'Đơn vị nhận *';
                partnerInput.placeholder = 'Ví dụ: Khoa dược, CDC chi nhánh, ...';
                reasonInput.value = 'Xuất qua điện thoại';
            }
            noteInput.value = '';
            partnerInput.value = '';
            partnerSelect.value = '';
            toggleCartCustomPartner();
            
            if (cart.length === 0) {
                container.innerHTML = '<div class="no-result">Giỏ hàng trống.</div>';
            } else {
                cart.forEach((item, index) => {
                    const row = document.createElement('div');
                    row.className = 'cart-item-row';
                    let metaText = `SL: ${item.qty} ${item.unit}`;
                    if (item.lotNo) metaText += ` | Lô: ${item.lotNo}`;
                    if (item.expiryDate) metaText += ` | HSD: ${item.expiryDate}`;
                    if (item.fundSource) metaText += ` | Nguồn: ${item.fundSource}`;
                    row.innerHTML = `
                        <div class="cart-item-details">
                            <div class="cart-item-name">${escapeHtml(item.productName)}</div>
                            <div class="cart-item-meta">${escapeHtml(metaText)}</div>
                        </div>
                        <button class="btn-cart-remove" onclick="removeFromCart('${escapeHtml(type)}', ${index})">❌</button>
                    `;
                    container.appendChild(row);
                });
            }
            
            document.getElementById('btn-cart-submit-pc').onclick = () => submitCart(type, 'pc');
            document.getElementById('btn-cart-submit-phone').onclick = () => submitCart(type, 'phone');
            
            document.getElementById('cart-modal').style.display = 'flex';
        }
        
        function closeCartModal() {
            document.getElementById('cart-modal').style.display = 'none';
        }
        
        function removeFromCart(type, index) {
            if (type === 'purchase') {
                purchaseCart.splice(index, 1);
                localStorage.setItem('mob_purchase_cart', JSON.stringify(purchaseCart));
            } else {
                dispatchCart.splice(index, 1);
                localStorage.setItem('mob_dispatch_cart', JSON.stringify(dispatchCart));
            }
            updateCartStatus();
            openCartModal(type);
        }

        function submitCart(type, printTarget) {
            const cart = type === 'purchase' ? purchaseCart : dispatchCart;
            if (cart.length === 0) {
                showToast("Giỏ hàng đang trống!", "error");
                return;
            }
            
            const partnerSelect = document.getElementById('cart-partner-select');
            let partner = partnerSelect.value;
            if (partner === '__custom__') {
                partner = document.getElementById('cart-partner-input').value.trim();
            } else {
                partner = partner.trim();
            }
            const reason = document.getElementById('cart-reason-input').value.trim();
            const note = document.getElementById('cart-note-input').value.trim();
            
            if (!partner || !reason) {
                showToast("Vui lòng nhập đầy đủ đối tác và lý do thực hiện!", "error");
                return;
            }
            
            const url = type === 'purchase' ? '/api/purchase' : '/api/dispatch';
            const bodyData = {
                items: cart,
                reason: reason,
                note: note
            };
            if (type === 'purchase') {
                bodyData.supplier = partner;
            } else {
                bodyData.receivingUnit = partner;
            }
            
            const submitBtnPc = document.getElementById('btn-cart-submit-pc');
            const submitBtnPhone = document.getElementById('btn-cart-submit-phone');
            const oldPcText = submitBtnPc.innerHTML;
            const oldPhoneText = submitBtnPhone.innerHTML;
            
            submitBtnPc.disabled = true;
            submitBtnPhone.disabled = true;
            submitBtnPc.innerHTML = 'Đang xử lý...';
            
            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bodyData)
            })
            .then(res => res.json())
            .then(data => {
                submitBtnPc.disabled = false;
                submitBtnPhone.disabled = false;
                submitBtnPc.innerHTML = oldPcText;
                submitBtnPhone.innerHTML = oldPhoneText;
                
                if (data.success) {
                    showToast(data.message, "success");
                    closeCartModal();
                    
                    if (type === 'purchase') {
                        purchaseCart = [];
                        localStorage.removeItem('mob_purchase_cart');
                    } else {
                        dispatchCart = [];
                        localStorage.removeItem('mob_dispatch_cart');
                    }
                    updateCartStatus();
                    loadDashboardStats();
                    
                    const noteId = type === 'purchase' ? data.purchaseId : data.dispatchId;
                    if (printTarget === 'pc') {
                        showToast("Đang gửi lệnh in tới máy tính...", "info");
                        fetch(`/api/pc-print?type=${type}&id=${noteId}`)
                            .then(res => res.json())
                            .then(pdata => {
                                if (pdata.success) {
                                    showToast("Máy tính đã nhận lệnh in!", "success");
                                } else {
                                    showToast("Lỗi in PC: " + pdata.message, "error");
                                }
                            })
                            .catch(err => showToast("Lỗi gửi lệnh in PC", "error"));
                    } else {
                        const printUrl = type === 'purchase'
                            ? `/api/print-purchase?id=${encodeURIComponent(noteId)}`
                            : `/api/print-dispatch?id=${encodeURIComponent(noteId)}`;
                        window.open(withAuthToken(printUrl), '_blank');
                    }
                } else {
                    showToast(data.message, "error");
                }
            })
            .catch(err => {
                submitBtnPc.disabled = false;
                submitBtnPhone.disabled = false;
                submitBtnPc.innerHTML = oldPcText;
                submitBtnPhone.innerHTML = oldPhoneText;
                showToast("Lỗi kết nối máy chủ: " + err, "error");
            });
        }

        function showNotePreview(type, noteId) {
            const modal = document.getElementById('preview-modal');
            const title = document.getElementById('preview-modal-title');
            const infoContainer = document.getElementById('preview-info-container');
            const tableBody = document.getElementById('preview-table-body');
            
            title.textContent = "📋 Đang tải phiếu...";
            infoContainer.innerHTML = '<div style="text-align: center; padding: 10px;">Đang truy vấn thông tin...</div>';
            tableBody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 10px;">Đang tải danh sách mặt hàng...</td></tr>';
            
            modal.style.display = 'flex';
            
            fetch(`/api/note-details?type=${type}&id=${noteId}`)
                .then(res => res.json())
                .then(data => {
                    if (!data.success) {
                        showToast(data.message, "error");
                        modal.style.display = 'none';
                        return;
                    }
                    
                    title.textContent = data.type === 'nhap' ? '📥 Xem Trước Phiếu Nhập' : '📤 Xem Trước Phiếu Xuất';
                    
                    infoContainer.innerHTML = `
                        <div style="margin-bottom: 4px;"><b>Số phiếu:</b> <span style="color: var(--primary); font-weight: bold;">${escapeHtml(data.noteNumber)}</span></div>
                        <div style="margin-bottom: 4px;"><b>Thời gian:</b> ${escapeHtml(data.createdAt)}</div>
                        <div style="margin-bottom: 4px;"><b>${data.type === 'nhap' ? 'Nhà cung cấp' : 'Đơn vị nhận'}:</b> ${escapeHtml(data.partner)}</div>
                        <div style="margin-bottom: 4px;"><b>Lý do:</b> ${escapeHtml(data.reason)}</div>
                        ${data.note ? `<div style="margin-bottom: 4px;"><b>Ghi chú:</b> ${escapeHtml(data.note)}</div>` : ''}
                    `;
                    
                    let rowsHtml = '';
                    data.items.forEach(item => {
                        rowsHtml += `
                            <tr>
                                <td style="padding: 8px 10px;">${escapeHtml(item.productName)}</td>
                                <td style="padding: 8px 10px; text-align: center;">${escapeHtml(item.lotNo)}</td>
                                <td style="padding: 8px 10px; text-align: right; font-weight: 600;">${escapeHtml(item.qty)} ${escapeHtml(item.unit)}</td>
                            </tr>
                        `;
                    });
                    tableBody.innerHTML = rowsHtml;
                    
                    document.getElementById('btn-preview-submit-pc').onclick = () => {
                        const btn = document.getElementById('btn-preview-submit-pc');
                        btn.disabled = true;
                        const origText = btn.innerHTML;
                        btn.innerHTML = '⌛...';
                        
                        fetch(`/api/pc-print?type=${type}&id=${noteId}`)
                            .then(res => res.json())
                            .then(pdata => {
                                btn.disabled = false;
                                btn.innerHTML = origText;
                                showToast(pdata.message, pdata.success ? "success" : "error");
                                if (pdata.success) modal.style.display = 'none';
                            })
                            .catch(err => {
                                btn.disabled = false;
                                btn.innerHTML = origText;
                                showToast("Lỗi gửi lệnh in PC", "error");
                            });
                    };
                    
                    document.getElementById('btn-preview-submit-phone').onclick = () => {
                        const url = data.type === 'nhap'
                            ? `/api/print-purchase?id=${encodeURIComponent(noteId)}`
                            : `/api/print-dispatch?id=${encodeURIComponent(noteId)}`;
                        window.open(withAuthToken(url), '_blank');
                        modal.style.display = 'none';
                    };
                })
                .catch(err => {
                    showToast("Lỗi kết nối máy chủ", "error");
                    modal.style.display = 'none';
                });
        }
        
        function closePreviewModal() {
            document.getElementById('preview-modal').style.display = 'none';
        }

        function checkStock(barcode, byId = false) {
            if (!barcode) return;
            
            resultCard.style.display = 'block';
            closeForms();
            resultContent.innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    Đang truy vấn dữ liệu kho...
                </div>
            `;

            const url = byId
                ? `/api/stock?id=${encodeURIComponent(barcode)}`
                : `/api/stock?barcode=${encodeURIComponent(barcode)}`;
            fetch(url)
                .then(res => {
                    if (!res.ok) {
                        return res.json().then(err => { throw new Error(err.message || 'Không tìm thấy sản phẩm') });
                    }
                    return res.json();
                })
                .then(data => {
                    if (!data.success) {
                        showNoResult();
                        return;
                    }
                    currentProduct = data.product;
                    currentProductBatches = data.batches;
                    displayResult(data);
                })
                .catch(err => {
                    showError(err.message);
                });
        }

        function showNoResult() {
            currentProduct = null;
            currentProductBatches = [];
            resultContent.innerHTML = `
                <div class="no-result">
                    ❌ Không tìm thấy sản phẩm trùng khớp.
                </div>
            `;
        }

        function showError(msg) {
            currentProduct = null;
            currentProductBatches = [];
            resultContent.innerHTML = `
                <div class="error-msg">
                    ⚠ Lỗi: ${escapeHtml(msg)}
                </div>
            `;
        }

        function displayResult(data) {
            const p = data.product;
            const batches = data.batches;
            
            let typeText = "Thuốc / Dược phẩm";
            if (p.type === 'vaccine') typeText = "Vaccine";
            else if (p.type === 'vtyt') typeText = "Vật tư y tế";
            else if (p.type === 'khac') typeText = "Sản phẩm khác";

            let batchesHtml = '';
            if (batches.length === 0) {
                batchesHtml = '<div class="no-result" style="padding: 10px;">Sản phẩm hiện hết hàng hoặc chưa nhập lô.</div>';
            } else {
                batches.forEach(b => {
                    const expDate = new Date(b.expiryDate);
                    const today = new Date();
                    const diffTime = expDate - today;
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    
                    let badgeHtml = '';
                    if (diffDays <= 0) {
                        badgeHtml = '<span class="badge badge-expired">Hết hạn</span>';
                    } else if (diffDays <= 180) {
                        badgeHtml = `<span class="badge badge-warning">Cận hạn (${diffDays} ngày)</span>`;
                    } else {
                        badgeHtml = '<span class="badge badge-ok">Hạn tốt</span>';
                    }

                    batchesHtml += `
                        <div class="batch-item">
                            <div class="batch-header">
                                <span class="batch-lot">Lô: ${escapeHtml(b.lotNo)}</span>
                                <span class="batch-qty">${escapeHtml(b.qty)} ${escapeHtml(p.unit)}</span>
                            </div>
                            <div class="batch-expiry">
                                <span>Hạn dùng: ${escapeHtml(b.expiryDate)}</span>
                                ${badgeHtml}
                            </div>
                        </div>
                    `;
                });
            }

            resultContent.innerHTML = `
                <div class="product-info">
                    <div class="info-row">
                        <span class="info-label">Tên sản phẩm</span>
                        <span class="info-value" style="color: #a5b4fc; text-align: right; max-width: 65%;">${escapeHtml(p.name)}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Mã vạch</span>
                        <span class="info-value">${escapeHtml(p.barcode || 'Chưa gán')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Phân loại</span>
                        <span class="info-value">${escapeHtml(typeText)}</span>
                    </div>
                    <div class="info-row" style="margin-top: 5px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                        <span class="info-label" style="font-weight: bold; color: #fff;">Tổng tồn kho</span>
                        <span class="info-value" style="color: var(--success); font-size: 1.1rem;">${escapeHtml(data.totalQty)} ${escapeHtml(p.unit)}</span>
                    </div>
                </div>
                
                <div class="result-title" style="font-size: 0.95rem; border: none; margin-top: 12px; margin-bottom: 5px; padding: 0;">📦 Chi tiết tồn kho theo lô</div>
                <div class="batch-list" style="max-height: 200px; overflow-y: auto;">
                    ${batchesHtml}
                </div>
                
                <div class="action-buttons">
                    <button class="action-btn btn-purchase" onclick="openForm('purchase')">📥 Nhập Kho</button>
                    <button class="action-btn btn-dispatch" onclick="openForm('dispatch')">📤 Xuất Kho</button>
                    <button class="action-btn btn-barcode" onclick="openForm('barcode')">🏷️ Gán / Liên Kết Mã Vạch</button>
                </div>
            `;
        }

        function closeForms() {
            document.querySelectorAll('.form-container').forEach(el => el.style.display = 'none');
        }

        function openForm(type) {
            closeForms();
            const form = document.getElementById(`form-${type}`);
            form.style.display = 'block';
            form.scrollIntoView({ behavior: 'smooth', block: 'end' });
            
            if (type === 'purchase') {
                document.getElementById('pur-qty').value = '';
                document.getElementById('pur-lot').value = '';
                document.getElementById('pur-expiry').value = '';
            } else if (type === 'dispatch') {
                document.getElementById('disp-qty').value = '';
                const select = document.getElementById('disp-batch-id');
                select.innerHTML = '';
                
                if (currentProductBatches.length === 0) {
                    select.innerHTML = '<option value="">(Không có lô hàng nào còn tồn)</option>';
                } else {
                    currentProductBatches.forEach(b => {
                        const opt = document.createElement('option');
                        opt.value = b.lotNo;
                        opt.textContent = `Lô: ${b.lotNo} (Còn tồn: ${b.qty})`;
                        select.appendChild(opt);
                    });
                }
            } else if (type === 'barcode') {
                document.getElementById('link-barcode').value = barcodeInput.value || '';
            }
        }

        function submitPurchase() {
            if (!currentProduct) return;
            const qty = parseFloat(document.getElementById('pur-qty').value);
            const lotNo = document.getElementById('pur-lot').value.trim();
            const expiry = document.getElementById('pur-expiry').value;
            
            const supplierSelect = document.getElementById('pur-supplier');
            let supplier = supplierSelect.value;
            if (supplier === '__custom__') {
                supplier = document.getElementById('pur-supplier-custom').value.trim();
            } else {
                supplier = supplier.trim();
            }
            
            const fundSelect = document.getElementById('pur-fund');
            let fundSource = fundSelect.value;
            if (fundSource === '__custom__') {
                fundSource = document.getElementById('pur-fund-custom').value.trim();
            } else {
                fundSource = fundSource.trim();
            }
            
            if (!qty || qty <= 0 || !lotNo || !expiry) {
                showToast("Vui lòng điền đầy đủ và chính xác thông tin!", "error");
                return;
            }
            
            fetch('/api/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    productId: currentProduct.id,
                    qty: qty,
                    lotNo: lotNo,
                    expiryDate: expiry,
                    supplier: supplier || "Nhập kho di động",
                    fundSource: fundSource
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, "success");
                    closeForms();
                    checkStock(currentProduct.barcode || currentProduct.id);
                    showNotePreview('purchase', data.purchaseId);
                    loadDashboardStats();
                } else {
                    showToast(data.message, "error");
                }
            })
            .catch(err => showToast("Lỗi kết nối máy chủ", "error"));
        }

        function submitDispatch() {
            if (!currentProduct) return;
            const lotNo = document.getElementById('disp-batch-id').value;
            const qty = parseFloat(document.getElementById('disp-qty').value);
            const reason = document.getElementById('disp-reason').value.trim();
            const fundSource = document.getElementById('disp-fund').value;
            
            const unitSelect = document.getElementById('disp-unit');
            let receivingUnit = unitSelect.value;
            if (receivingUnit === '__custom__') {
                receivingUnit = document.getElementById('disp-unit-custom').value.trim();
            } else {
                receivingUnit = receivingUnit.trim();
            }
            
            if (!lotNo || !qty || qty <= 0) {
                showToast("Vui lòng nhập đầy đủ thông tin!", "error");
                return;
            }
            
            fetch('/api/dispatch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    productId: currentProduct.id,
                    lotNo: lotNo,
                    qty: qty,
                    reason: reason,
                    receivingUnit: receivingUnit || "Điện thoại di động",
                    fundSource: fundSource
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, "success");
                    closeForms();
                    checkStock(currentProduct.barcode || currentProduct.id);
                    showNotePreview('dispatch', data.dispatchId);
                    loadDashboardStats();
                } else {
                    showToast(data.message, "error");
                }
            })
            .catch(err => showToast("Lỗi kết nối máy chủ", "error"));
        }

        function submitLinkBarcode() {
            if (!currentProduct) return;
            const barcode = document.getElementById('link-barcode').value.trim();
            
            if (!barcode) {
                showToast("Vui lòng nhập hoặc quét mã vạch!", "error");
                return;
            }
            
            fetch('/api/update-barcode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    productId: currentProduct.id,
                    barcode: barcode
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, "success");
                    closeForms();
                    barcodeInput.value = barcode;
                    checkStock(barcode);
                } else {
                    showToast(data.message, "error");
                }
            })
            .catch(err => showToast("Lỗi kết nối máy chủ", "error"));
        }

        let activeCatalogFilter = 'all';
        function loadCatalog(query = '', filterType = 'all') {
            activeCatalogFilter = filterType;
            
            const btnAll = document.getElementById('filter-btn-all');
            const btnOutOfStock = document.getElementById('filter-btn-outofstock');
            const btnExpiring = document.getElementById('filter-btn-expiring');
            
            if (btnAll && btnOutOfStock && btnExpiring) {
                btnAll.style.background = activeCatalogFilter === 'all' ? 'var(--primary)' : '#fff';
                btnAll.style.color = activeCatalogFilter === 'all' ? '#fff' : 'var(--text-muted)';
                btnAll.style.border = activeCatalogFilter === 'all' ? '1px solid var(--primary)' : '1px solid var(--glass-border)';
                
                btnOutOfStock.style.background = activeCatalogFilter === 'outofstock' ? '#ef4444' : '#fff';
                btnOutOfStock.style.color = activeCatalogFilter === 'outofstock' ? '#fff' : '#ef4444';
                btnOutOfStock.style.border = activeCatalogFilter === 'outofstock' ? '1px solid #ef4444' : '1px solid var(--glass-border)';
                
                btnExpiring.style.background = activeCatalogFilter === 'expiring' ? '#f59e0b' : '#fff';
                btnExpiring.style.color = activeCatalogFilter === 'expiring' ? '#fff' : '#f59e0b';
                btnExpiring.style.border = activeCatalogFilter === 'expiring' ? '1px solid #f59e0b' : '1px solid var(--glass-border)';
            }
            
            const list = document.getElementById('catalog-list');
            list.innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    Đang tải danh sách...
                </div>
            `;
            
            let url = `/api/products?q=${encodeURIComponent(query)}`;
            if (filterType !== 'all') {
                url += `&filter=${filterType}`;
            }
            
            fetch(url)
                .then(res => res.json())
                .then(data => {
                    if (!data.success || data.products.length === 0) {
                        list.innerHTML = '<div class="no-result">Không tìm thấy sản phẩm nào.</div>';
                        return;
                    }
                    
                    let html = '';
                    data.products.forEach(p => {
                        html += `
                            <div class="product-item" onclick="selectProductFromCatalog(${p.id})">
                                <div class="product-item-details">
                                    <span class="product-item-name">${p.name}</span>
                                    <span class="product-item-sub">ĐVT: ${p.unit} ${p.barcode ? ' | Mã vạch: ' + p.barcode : ''}</span>
                                </div>
                                <span class="product-item-arrow">➔</span>
                            </div>
                        `;
                    });
                    list.innerHTML = html;
                })
                .catch(err => {
                    list.innerHTML = '<div class="error-msg">Không thể tải danh sách sản phẩm.</div>';
                });
        }

        function filterCatalog(type) {
            switchTab('tab-catalog');
            document.getElementById('catalog-search').value = '';
            loadCatalog('', type);
        }

        function loadDashboardStats() {
            const refreshBtn = document.getElementById('dashboard-refresh');
            if (refreshBtn) refreshBtn.textContent = '⌛...';
            
            fetch('/api/dashboard-stats')
                .then(res => res.json())
                .then(data => {
                    if (refreshBtn) refreshBtn.textContent = 'Cập nhật';
                    if (data.success) {
                        document.getElementById('dash-total-products').textContent = data.totalProducts;
                        document.getElementById('dash-outofstock-products').textContent = data.outofstockProducts;
                        document.getElementById('dash-expiring-products').textContent = data.expiringProducts;
                    }
                })
                .catch(err => {
                    if (refreshBtn) refreshBtn.textContent = 'Cập nhật';
                    console.error("Lỗi tải dashboard stats:", err);
                });
        }

        function selectProductFromCatalog(productId) {
            barcodeInput.value = `ID:${productId}`;
            switchTab('tab-checker');
            checkStock(productId, true);
        }

        function openCreateProductForm() {
            const form = document.getElementById('form-create-product');
            form.style.display = 'block';
            document.getElementById('new-name').value = '';
            document.getElementById('new-unit').value = '';
            document.getElementById('new-type').value = 'thuoc';
            document.getElementById('new-barcode').value = '';
            document.getElementById('new-regnumber').value = '';
            form.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }

        function closeCreateProductForm() {
            document.getElementById('form-create-product').style.display = 'none';
        }

        function submitCreateProduct() {
            const name = document.getElementById('new-name').value.trim();
            const unit = document.getElementById('new-unit').value.trim();
            const type = document.getElementById('new-type').value;
            const barcode = document.getElementById('new-barcode').value.trim();
            const regNumber = document.getElementById('new-regnumber').value.trim();
            
            if (!name || !unit) {
                showToast("Vui lòng nhập tên và đơn vị tính gốc!", "error");
                return;
            }
            
            fetch('/api/create-product', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    defaultUnit: unit,
                    productType: type,
                    barcode: barcode,
                    registrationNumber: regNumber
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, "success");
                    closeCreateProductForm();
                    loadDashboardStats();
                    
                    const identifier = data.productId;
                    barcodeInput.value = identifier;
                    switchTab('tab-checker');
                    checkStock(identifier, true);
                    
                    setTimeout(() => {
                        openForm('purchase');
                    }, 600);
                } else {
                    showToast(data.message, "error");
                }
            })
            .catch(err => showToast("Lỗi kết nối máy chủ", "error"));
        }

        searchBtn.addEventListener('click', () => {
            checkStock(barcodeInput.value.trim());
        });

        barcodeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                checkStock(barcodeInput.value.trim());
            }
        });

        document.getElementById('catalog-search-btn').addEventListener('click', () => {
            loadCatalog(document.getElementById('catalog-search').value.trim());
        });

        document.getElementById('catalog-search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadCatalog(document.getElementById('catalog-search').value.trim());
            }
        });

        let lastScannedCode = "";
        let scanTime = 0;

        function onScanSuccess(decodedText, decodedResult) {
            const now = Date.now();
            if (decodedText === lastScannedCode && (now - scanTime < 2500)) {
                return;
            }
            lastScannedCode = decodedText;
            scanTime = now;
            
            const barcodeForm = document.getElementById('form-barcode');
            const createForm = document.getElementById('form-create-product');
            if (barcodeForm.style.display === 'block') {
                document.getElementById('link-barcode').value = decodedText;
                showToast(`Đã quét mã mới: ${decodedText}`);
                if (navigator.vibrate) navigator.vibrate(100);
            } else if (createForm && createForm.style.display === 'block') {
                document.getElementById('new-barcode').value = decodedText;
                showToast(`Đã quét mã sản phẩm mới: ${decodedText}`);
                if (navigator.vibrate) navigator.vibrate(100);
            } else {
                barcodeInput.value = decodedText;
                if (navigator.vibrate) navigator.vibrate(100);
                checkStock(decodedText);
            }
        }

        function onScanFailure(error) {}

        const html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", 
            { 
                fps: 10, 
                qrbox: function(width, height) {
                    const size = Math.min(width, height) * 0.65;
                    return { width: size, height: size * 0.6 };
                },
                aspectRatio: 1.0,
                supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA]
            },
            false
        );
        html5QrcodeScanner.render(onScanSuccess, onScanFailure);
        let partnersData = {
            suppliers: [],
            receivingUnits: [],
            fundSources: [],
            tempLocations: []
        };

        function loadPartnersAndFunds() {
            const todayStr = new Date().toISOString().split('T')[0];
            document.getElementById('temp-date').value = todayStr;
            
            const currentMonthStr = todayStr.substring(0, 7); // YYYY-MM
            document.getElementById('temp-filter-month').value = currentMonthStr;
            document.getElementById('xnt-filter-month').value = currentMonthStr;
            
            const savedRecordedBy = localStorage.getItem('temp-recorded-by');
            if (savedRecordedBy) {
                document.getElementById('temp-recorded-by').value = savedRecordedBy;
            }

            fetch('/api/partners')
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        partnersData.suppliers = data.suppliers || [];
                        partnersData.receivingUnits = data.receivingUnits || [];
                        partnersData.fundSources = data.fundSources || [];
                        
                        populateDropdowns();
                    }
                })
                .catch(err => console.error("Lỗi fetch partners:", err));
                
            fetch('/api/temperature-locations')
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        partnersData.tempLocations = data.locations || [];
                        populateTempLocations();
                    }
                })
                .catch(err => console.error("Lỗi fetch temp locations:", err));
        }

        function populateDropdowns() {
            const purSupplier = document.getElementById('pur-supplier');
            let htmlSupplier = '<option value="">-- Chọn nhà cung cấp --</option>';
            partnersData.suppliers.forEach(s => {
                htmlSupplier += `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`;
            });
            htmlSupplier += '<option value="__custom__">Khác (Nhập tay)...</option>';
            purSupplier.innerHTML = htmlSupplier;
            toggleCustomSupplier();

            const purFund = document.getElementById('pur-fund');
            let htmlFund = '<option value="">-- Không chọn --</option>';
            partnersData.fundSources.forEach(f => {
                htmlFund += `<option value="${escapeHtml(f)}">${escapeHtml(f)}</option>`;
            });
            htmlFund += '<option value="__custom__">Khác (Nhập tay)...</option>';
            purFund.innerHTML = htmlFund;
            toggleCustomFund();

            const dispUnit = document.getElementById('disp-unit');
            let htmlUnit = '<option value="">-- Chọn đơn vị nhận --</option>';
            partnersData.receivingUnits.forEach(u => {
                htmlUnit += `<option value="${escapeHtml(u)}">${escapeHtml(u)}</option>`;
            });
            htmlUnit += '<option value="__custom__">Khác (Nhập tay)...</option>';
            dispUnit.innerHTML = htmlUnit;
            toggleCustomDispatchUnit();

            const dispFund = document.getElementById('disp-fund');
            let htmlDispFund = '<option value="">[Tự động trừ kho]</option>';
            partnersData.fundSources.forEach(f => {
                htmlDispFund += `<option value="${escapeHtml(f)}">${escapeHtml(f)}</option>`;
            });
            dispFund.innerHTML = htmlDispFund;

            const xntFund = document.getElementById('xnt-filter-fund');
            let htmlXNTFund = '<option value="">Tất cả các nguồn</option>';
            partnersData.fundSources.forEach(f => {
                htmlXNTFund += `<option value="${escapeHtml(f)}">${escapeHtml(f)}</option>`;
            });
            xntFund.innerHTML = htmlXNTFund;
        }

        function populateTempLocations() {
            const tempLocSelect = document.getElementById('temp-location-select');
            let html = '<option value="">-- Chọn vị trí --</option>';
            partnersData.tempLocations.forEach(loc => {
                html += `<option value="${escapeHtml(loc)}">${escapeHtml(loc)}</option>`;
            });
            html += '<option value="__custom__">Khác (Nhập tay)...</option>';
            tempLocSelect.innerHTML = html;
            toggleCustomTempLocation();
            
            const tempFilterLoc = document.getElementById('temp-filter-location');
            let htmlFilter = '<option value="">Tất cả vị trí</option>';
            partnersData.tempLocations.forEach(loc => {
                htmlFilter += `<option value="${escapeHtml(loc)}">${escapeHtml(loc)}</option>`;
            });
            tempFilterLoc.innerHTML = htmlFilter;
        }

        function escapeHtml(str) {
            if (!str) return '';
            str = String(str);
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }

        function toggleCustomSupplier() {
            const select = document.getElementById('pur-supplier');
            const custom = document.getElementById('pur-supplier-custom');
            custom.style.display = select.value === '__custom__' ? 'block' : 'none';
        }

        function toggleCustomFund() {
            const select = document.getElementById('pur-fund');
            const custom = document.getElementById('pur-fund-custom');
            custom.style.display = select.value === '__custom__' ? 'block' : 'none';
        }

        function toggleCustomDispatchUnit() {
            const select = document.getElementById('disp-unit');
            const custom = document.getElementById('disp-unit-custom');
            custom.style.display = select.value === '__custom__' ? 'block' : 'none';
        }

        function toggleCustomTempLocation() {
            const select = document.getElementById('temp-location-select');
            const custom = document.getElementById('temp-location-custom');
            custom.style.display = select.value === '__custom__' ? 'block' : 'none';
        }

        function toggleCartCustomPartner() {
            const select = document.getElementById('cart-partner-select');
            const input = document.getElementById('cart-partner-input');
            input.style.display = select.value === '__custom__' ? 'block' : 'none';
        }

        function onDispatchBatchChange() {
            // Can be extended to preset default lot-specific fund source if desired
        }

        function submitTemperatureLog() {
            const logDate = document.getElementById('temp-date').value;
            const session = document.getElementById('temp-session').value;
            
            const locSelect = document.getElementById('temp-location-select');
            let location = locSelect.value;
            if (location === '__custom__') {
                location = document.getElementById('temp-location-custom').value.trim();
            } else {
                location = location.trim();
            }
            
            const temperature = parseFloat(document.getElementById('temp-val').value);
            const humidityVal = document.getElementById('temp-humidity').value.trim();
            const humidity = humidityVal ? parseFloat(humidityVal) : null;
            const recordedBy = document.getElementById('temp-recorded-by').value.trim();
            
            if (!logDate || !location || isNaN(temperature)) {
                showToast("Vui lòng nhập đầy đủ Ngày, Vị trí và Nhiệt độ!", "error");
                return;
            }
            
            if (recordedBy) {
                localStorage.setItem('temp-recorded-by', recordedBy);
            }
            
            fetch('/api/temperature-log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    logDate: logDate,
                    session: session,
                    location: location,
                    temperature: temperature,
                    humidity: humidity,
                    recordedBy: recordedBy
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, "success");
                    document.getElementById('temp-val').value = '';
                    document.getElementById('temp-humidity').value = '';
                    
                    fetch('/api/temperature-locations')
                        .then(res => res.json())
                        .then(locData => {
                            if (locData.success) {
                                partnersData.tempLocations = locData.locations || [];
                                populateTempLocations();
                                document.getElementById('temp-location-select').value = location;
                                toggleCustomTempLocation();
                            }
                            loadTemperatureLogs();
                        });
                } else {
                    showToast(data.message, "error");
                }
            })
            .catch(err => showToast("Lỗi kết nối máy chủ", "error"));
        }

        function loadTemperatureLogs() {
            const filterMonth = document.getElementById('temp-filter-month').value;
            const filterLoc = document.getElementById('temp-filter-location').value;
            const listDiv = document.getElementById('temp-logs-list');
            
            if (!filterMonth) {
                listDiv.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 15px;">Chọn tháng để tra cứu</div>';
                return;
            }
            
            listDiv.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 15px;">Đang tải nhật ký...</div>';
            
            let url = `/api/temperature-logs?month=${filterMonth}`;
            if (filterLoc) {
                url += `&location=${encodeURIComponent(filterLoc)}`;
            }
            
            fetch(url)
                .then(res => res.json())
                .then(data => {
                    if (!data.success || data.logs.length === 0) {
                        listDiv.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 15px;">Không có dữ liệu cho bộ lọc này.</div>';
                        return;
                    }
                    
                    let html = '';
                    data.logs.forEach(log => {
                        const isAlert = log.temperature < 2.0 || log.temperature > 25.0;
                        const alertClass = isAlert ? 'temp-status-alert' : '';
                        
                        html += `
                            <div class="card ${alertClass}" style="margin: 0; padding: 10px; border-radius: 8px; border: 1px solid var(--glass-border); font-size: 0.8rem;">
                                <div style="display: flex; justify-content: space-between; font-weight: 600; margin-bottom: 4px;">
                                    <span>📍 ${escapeHtml(log.location)}</span>
                                    <span>📅 ${log.logDate} (${log.session})</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; color: var(--text-light);">
                                    <span>🌡️ Nhiệt độ: <strong>${log.temperature}°C</strong></span>
                                    <span>💧 Độ ẩm: <strong>${log.humidity !== null ? log.humidity + '%' : 'N/A'}</strong></span>
                                </div>
                                <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px; border-top: 1px dashed rgba(0,0,0,0.05); padding-top: 4px; display: flex; justify-content: space-between;">
                                    <span>Người ghi: ${escapeHtml(log.recordedBy || 'N/A')}</span>
                                    <span>${isAlert ? '⚠️ Chỉ số ngoài ngưỡng an toàn!' : '✅ Bình thường'}</span>
                                </div>
                            </div>
                        `;
                    });
                    listDiv.innerHTML = html;
                })
                .catch(err => {
                    listDiv.innerHTML = '<div style="text-align: center; color: var(--danger); padding: 15px;">Lỗi tải dữ liệu.</div>';
                });
        }

        function loadXNTReport() {
            const filterMonth = document.getElementById('xnt-filter-month').value;
            const filterFund = document.getElementById('xnt-filter-fund').value;
            const reportCard = document.getElementById('xnt-report-card');
            const tbody = document.getElementById('xnt-report-body');
            
            if (!filterMonth) {
                showToast("Vui lòng chọn tháng tra cứu!", "error");
                return;
            }
            
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 15px; color: var(--text-muted);">Đang tính toán báo cáo...</td></tr>';
            reportCard.style.display = 'block';
            
            let url = `/api/xnt-report?month=${filterMonth}`;
            if (filterFund) {
                url += `&fundSource=${encodeURIComponent(filterFund)}`;
            }
            
            fetch(url)
                .then(res => res.json())
                .then(data => {
                    if (!data.success || data.report.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 15px; color: var(--text-muted);">Không có số liệu nhập xuất trong tháng này.</td></tr>';
                        return;
                    }
                    
                    let html = '';
                    data.report.forEach(row => {
                        const lotText = row.lotNo || '-';
                        const fundText = row.fundSource || '-';
                        const openingQty = Number(row.opening || 0);
                        const importedQty = Number(row.inbound || 0);
                        const exportedQty = Number(row.outbound || 0);
                        const closingQty = Number(row.closing || 0);
                        
                        html += `
                            <tr>
                                <td style="font-weight: 600;">${escapeHtml(row.productName)}</td>
                                <td>Lô: ${escapeHtml(lotText)}<br><small style="color: var(--text-muted);">${escapeHtml(fundText)}</small></td>
                                <td style="text-align: right; font-weight: 500;">${openingQty.toLocaleString('vi-VN')} ${escapeHtml(row.unit)}</td>
                                <td style="text-align: right; color: #0d9488; font-weight: 500;">+${importedQty.toLocaleString('vi-VN')}</td>
                                <td style="text-align: right; color: #e11d48; font-weight: 500;">-${exportedQty.toLocaleString('vi-VN')}</td>
                                <td style="text-align: right; font-weight: 700; color: var(--primary);">${closingQty.toLocaleString('vi-VN')} ${escapeHtml(row.unit)}</td>
                            </tr>
                        `;
                    });
                    tbody.innerHTML = html;
                })
                .catch(err => {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 15px; color: var(--danger);">Không thể tải dữ liệu báo cáo.</td></tr>';
                });
        }

        function initializeApp() {
            const token = localStorage.getItem('inventory_token');
            if (token) {
                updateCartStatus();
                loadDashboardStats();
                loadPartnersAndFunds();
            }
        }
        initializeApp();
    </script>
</body>
</html>"""
