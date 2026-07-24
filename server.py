import http.server
import socket
import threading
import json
import urllib.parse
import sqlite3
import tempfile
import os
import time
import secrets
import html
from datetime import datetime
import datetime as dt_module

from config import DB_PATH
from database import DB
from mobile_templates import MOBILE_HTML
from print_templates import render_print_dispatch_html, render_print_purchase_html

SESSION_COOKIE_NAME = "inventory_token"


def open_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn

# Module-level variables for authentication (Lỗi 3)
SERVER_PIN = ""
ACTIVE_TOKENS = {}      # token -> {"ip": ip, "expiry": float}
FAILED_ATTEMPTS = {}    # ip -> {"count": int, "blocked_until": float}


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class MobileInventoryRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Mute logging to keep console clean
        pass

    def get_cookie(self, name):
        cookie_header = self.headers.get("Cookie", "")
        for part in cookie_header.split(";"):
            if "=" not in part:
                continue
            key, value = part.strip().split("=", 1)
            if key == name:
                return urllib.parse.unquote(value)
        return ""
        
    def check_auth(self):
        """Lỗi 3: Kiểm tra token hợp lệ cho LAN API"""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        # Không yêu cầu auth cho trang chủ, tĩnh và API đăng nhập
        if path in ["/", "/index.html", "/api/auth"] or path.startswith("/static/"):
            return True
            
        token = None
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        else:
            token = self.get_cookie(SESSION_COOKIE_NAME)
            
        if not token:
            self.send_json({"success": False, "message": "Yêu cầu xác thực PIN", "auth_required": True}, 401)
            return False
            
        token_info = ACTIVE_TOKENS.get(token)
        if not token_info:
            self.send_json({"success": False, "message": "Phiên làm việc không hợp lệ hoặc đã hết hạn", "auth_required": True}, 401)
            return False
            
        if token_info.get("ip") != self.client_address[0]:
            ACTIVE_TOKENS.pop(token, None)
            self.send_json({"success": False, "message": "Phiên không hợp lệ", "auth_required": True}, 401)
            return False

        if time.time() > token_info["expiry"]:
            ACTIVE_TOKENS.pop(token, None)
            self.send_json({"success": False, "message": "Phiên làm việc đã hết hạn", "auth_required": True}, 401)
            return False
            
        return True

    def do_GET(self):
        if not self.check_auth():
            return
            
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            # CSP Header (Bug 7)
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'")
            self.end_headers()
            self.wfile.write(MOBILE_HTML.encode("utf-8"))
            
        elif path == "/static/html5-qrcode.min.js":
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            js_file_path = os.path.join(base_dir, "static", "html5-qrcode.min.js")
            if os.path.exists(js_file_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.end_headers()
                try:
                    with open(js_file_path, "rb") as f:
                        self.wfile.write(f.read())
                except Exception as e:
                    print(f"Error serving offline QR js: {e}")
                    self.send_response(500)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
            
        elif path == "/api/stock":
            barcode = query.get("barcode", [""])[0].strip()
            if not barcode:
                self.send_json({"success": False, "message": "Mã vạch trống"}, 400)
                return
                
            try:
                conn = open_db()
                conn.row_factory = sqlite3.Row
                
                # Tìm kiếm sản phẩm theo barcode hoặc tên gần đúng
                product_rows = conn.execute("""
                    SELECT id, name, defaultUnit, barcode, productType, registrationNumber 
                    FROM products 
                    WHERE barcode=? OR name LIKE ? LIMIT 1
                """, (barcode, f"%{barcode}%")).fetchall()
                
                if not product_rows:
                    self.send_json({"success": False, "message": "Không tìm thấy sản phẩm"}, 404)
                    conn.close()
                    return
                    
                p = product_rows[0]
                pid = p['id']
                
                # Lấy thông tin tồn kho chi tiết từng lô
                batches_rows = conn.execute("""
                    SELECT b.lotNo, b.expiryDate, COALESCE(SUM(sm.qtyBase), 0) as qtyBase
                     FROM batches b
                    LEFT JOIN stock_movements sm ON sm.productId = b.productId AND sm.batchId = b.id
                    WHERE b.productId = ?
                    GROUP BY b.id
                    ORDER BY DATE(b.expiryDate) ASC
                """, (pid,)).fetchall()
                
                batches_list = []
                total_qty = 0
                for b in batches_rows:
                    q_val = float(b["qtyBase"])
                    # Chỉ hiện các lô có số lượng khác 0
                    if abs(q_val) > 0.001:
                        batches_list.append({
                            "lotNo": b["lotNo"],
                            "expiryDate": b["expiryDate"],
                            "qty": q_val
                        })
                        total_qty += q_val
                    
                self.send_json({
                    "success": True,
                    "product": {
                        "id": pid,
                        "name": p["name"],
                        "unit": p["defaultUnit"],
                        "barcode": p["barcode"] or "",
                        "type": p["productType"] or "thuoc",
                        "regNumber": p["registrationNumber"] or ""
                    },
                    "batches": batches_list,
                    "totalQty": total_qty
                })
                conn.close()
            except Exception as e:
                print(f"Error in api/stock: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi tải thông tin lô hàng"}, 500)
            
        elif path == "/api/products":
            q_term = query.get("q", [""])[0].strip()
            filter_type = query.get("filter", [""])[0].strip()
            try:
                conn = open_db()
                conn.row_factory = sqlite3.Row
                
                if filter_type == 'expiring':
                    rows = conn.execute("""
                        SELECT DISTINCT p.id, p.name, p.defaultUnit, p.barcode
                        FROM products p
                        JOIN batches b ON p.id = b.productId
                        JOIN stock_movements sm ON sm.productId = b.productId AND sm.batchId = b.id
                        GROUP BY p.id, b.id
                        HAVING SUM(sm.qtyBase) > 0.001 AND DATE(b.expiryDate) <= DATE('now', '+180 days')
                        ORDER BY p.name ASC
                    """).fetchall()
                elif filter_type == 'outofstock':
                    rows = conn.execute("""
                        SELECT p.id, p.name, p.defaultUnit, p.barcode, COALESCE(SUM(sm.qtyBase), 0) as totalQty
                        FROM products p
                        LEFT JOIN stock_movements sm ON sm.productId = p.id
                        GROUP BY p.id
                        HAVING totalQty <= 0.001
                        ORDER BY p.name ASC
                    """).fetchall()
                elif q_term:
                    rows = conn.execute("""
                        SELECT id, name, defaultUnit, barcode 
                        FROM products 
                        WHERE name LIKE ? OR barcode=? LIMIT 50
                    """, (f"%{q_term}%", q_term)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT id, name, defaultUnit, barcode 
                        FROM products 
                        ORDER BY name ASC LIMIT 50
                    """).fetchall()
                
                products_list = []
                for r in rows:
                    products_list.append({
                        "id": r["id"],
                        "name": r["name"],
                        "unit": r["defaultUnit"],
                        "barcode": r["barcode"] or ""
                    })
                
                self.send_json({"success": True, "products": products_list})
                conn.close()
            except Exception as e:
                print(f"Error in api/products: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi tải danh sách sản phẩm"}, 500)

        elif path == "/api/dashboard-stats":
            try:
                conn = open_db()
                total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                
                outofstock_products = conn.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT p.id, COALESCE(SUM(sm.qtyBase), 0) as totalQty 
                        FROM products p 
                        LEFT JOIN stock_movements sm ON sm.productId = p.id 
                        GROUP BY p.id 
                        HAVING totalQty <= 0.001
                    )
                """).fetchone()[0]
                
                expiring_products = conn.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT DISTINCT p.id
                        FROM products p
                        JOIN batches b ON p.id = b.productId
                        JOIN stock_movements sm ON sm.productId = b.productId AND sm.batchId = b.id
                        GROUP BY p.id, b.id
                        HAVING SUM(sm.qtyBase) > 0.001 AND DATE(b.expiryDate) <= DATE('now', '+180 days')
                    )
                """).fetchone()[0]
                
                conn.close()
                self.send_json({
                    "success": True,
                    "totalProducts": total_products,
                    "outofstockProducts": outofstock_products,
                    "expiringProducts": expiring_products
                })
            except Exception as e:
                print(f"Error in api/dashboard-stats: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi tải thống kê"}, 500)
            
        elif path == "/api/print-purchase":
            note_id = query.get("id", [""])[0].strip()
            if not note_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Yeu cau ID phieu nhap")
                return
            try:
                conn = open_db()
                conn.row_factory = sqlite3.Row
                note = conn.execute("SELECT * FROM purchase_notes WHERE id=?", (note_id,)).fetchone()
                if not note:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Khong tim thay phieu nhap")
                    conn.close()
                    return
                items = conn.execute("""
                    SELECT pi.*, p.name as productName 
                    FROM purchase_items pi
                    JOIN products p ON pi.productId = p.id
                    WHERE pi.purchaseId = ?
                    ORDER BY pi.id
                """, (note_id,)).fetchall()
                conn.close()
                html = render_print_purchase_html(note, items)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                print(f"Error printing purchase: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write("Lỗi hệ thống khi tải phiếu nhập".encode("utf-8"))

        elif path == "/api/print-dispatch":
            note_id = query.get("id", [""])[0].strip()
            if not note_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Yeu cau ID phieu xuat")
                return
            try:
                conn = open_db()
                conn.row_factory = sqlite3.Row
                note = conn.execute("SELECT * FROM dispatch_notes WHERE id=?", (note_id,)).fetchone()
                if not note:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Khong tim thay phieu xuat")
                    conn.close()
                    return
                items = conn.execute("""
                    SELECT di.*, p.name as productName 
                    FROM dispatch_items di
                    JOIN products p ON di.productId = p.id
                    WHERE di.dispatchId = ?
                    ORDER BY di.id
                """, (note_id,)).fetchall()
                conn.close()
                html = render_print_dispatch_html(note, items)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                print(f"Error printing dispatch: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write("Lỗi hệ thống khi tải phiếu xuất".encode("utf-8"))

        elif path == "/api/note-details":
            note_type = query.get("type", [""])[0].strip()
            note_id = query.get("id", [""])[0].strip()
            if note_type == 'nhap':
                note_type = 'purchase'
            elif note_type == 'xuat':
                note_type = 'dispatch'
                
            if not note_type or not note_id:
                self.send_json({"success": False, "message": "Thiếu thông tin loại phiếu hoặc ID"}, 400)
                return
            
            try:
                conn = open_db()
                conn.row_factory = sqlite3.Row
                
                if note_type == 'purchase':
                    note = conn.execute("SELECT id, noteNumber, supplier as partner, createdAt, reason, note FROM purchase_notes WHERE id=?", (note_id,)).fetchone()
                    if not note:
                        conn.close()
                        self.send_json({"success": False, "message": "Không tìm thấy phiếu nhập"}, 404)
                        return
                    items = conn.execute("""
                        SELECT pi.qty, pi.lotNo, pi.expiryDate, p.name as productName, p.defaultUnit as unit
                        FROM purchase_items pi
                        JOIN products p ON pi.productId = p.id
                        WHERE pi.purchaseId = ?
                        ORDER BY pi.id
                    """, (note_id,)).fetchall()
                else:
                    note = conn.execute("SELECT id, noteNumber, receivingUnit as partner, createdAt, reason, note FROM dispatch_notes WHERE id=?", (note_id,)).fetchone()
                    if not note:
                        conn.close()
                        self.send_json({"success": False, "message": "Không tìm thấy phiếu xuất"}, 404)
                        return
                    items = conn.execute("""
                        SELECT di.qty, di.lotNo, p.name as productName, p.defaultUnit as unit
                        FROM dispatch_items di
                        JOIN products p ON di.productId = p.id
                        WHERE di.dispatchId = ?
                        ORDER BY di.id
                    """, (note_id,)).fetchall()
                
                conn.close()
                
                res_items = []
                for it in items:
                    res_items.append({
                        "productName": it["productName"],
                        "qty": it["qty"],
                        "unit": it["unit"],
                        "lotNo": it["lotNo"],
                        "expiryDate": it["expiryDate"] if "expiryDate" in it.keys() else ""
                    })
                
                self.send_json({
                    "success": True,
                    "type": "nhap" if note_type == 'purchase' else "xuat",
                    "noteNumber": note["noteNumber"],
                    "partner": note["partner"],
                    "createdAt": note["createdAt"],
                    "reason": note["reason"],
                    "note": note["note"],
                    "items": res_items
                })
            except Exception as e:
                print(f"Error in api/note-details: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi truy vấn chi tiết phiếu"}, 500)

        elif path == "/api/recent-activities":
            try:
                conn = open_db()
                conn.row_factory = sqlite3.Row
                purchases = conn.execute("""
                    SELECT id, noteNumber, supplier as details, createdAt
                    FROM purchase_notes
                    ORDER BY id DESC LIMIT 5
                """).fetchall()
                dispatches = conn.execute("""
                    SELECT id, noteNumber, receivingUnit as details, createdAt
                    FROM dispatch_notes
                    ORDER BY id DESC LIMIT 5
                """).fetchall()
                conn.close()
                
                # Kết hợp và sắp xếp theo ngày tạo giảm dần
                combined = []
                for r in purchases:
                    combined.append({
                        "type": "nhap",
                        "id": r["id"],
                        "noteNumber": r["noteNumber"],
                        "details": r["details"],
                        "createdAt": r["createdAt"]
                    })
                for r in dispatches:
                    combined.append({
                        "type": "xuat",
                        "id": r["id"],
                        "noteNumber": r["noteNumber"],
                        "details": r["details"],
                        "createdAt": r["createdAt"]
                    })
                combined.sort(key=lambda x: x["createdAt"], reverse=True)
                
                self.send_json({"success": True, "activities": combined[:8]})
            except Exception as e:
                print(f"Error in api/recent-activities: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi tải hoạt động gần đây"}, 500)

        elif path == "/api/partners":
            try:
                db = DB(DB_PATH)
                suppliers = db.get_suppliers()
                receiving_units = db.get_receiving_units()
                fund_sources = db.get_fund_sources()
                self.send_json({
                    "success": True,
                    "suppliers": suppliers,
                    "receivingUnits": receiving_units,
                    "fundSources": fund_sources
                })
            except Exception as e:
                print(f"Error in api/partners: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi tải danh sách đối tác"}, 500)

        elif path == "/api/temperature-locations":
            try:
                db = DB(DB_PATH)
                locations = db.get_temperature_locations()
                self.send_json({
                    "success": True,
                    "locations": locations
                })
            except Exception as e:
                print(f"Error in api/temperature-locations: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi tải vị trí nhiệt độ"}, 500)

        elif path == "/api/temperature-logs":
            month = query.get("month", [None])[0]
            location = query.get("location", [None])[0]
            try:
                db = DB(DB_PATH)
                logs = db.get_temperature_logs(month, location)
                self.send_json({
                    "success": True,
                    "logs": logs
                })
            except Exception as e:
                print(f"Error in api/temperature-logs: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi tải nhật ký nhiệt độ"}, 500)

        elif path == "/api/xnt-report":
            month = query.get("month", [None])[0]
            fund_source = query.get("fundSource", [None])[0]
            if not month or "-" not in month:
                month = datetime.now().strftime("%Y-%m")
            try:
                year_part, month_part = map(int, month.split("-"))
                import calendar
                _, last_day = calendar.monthrange(year_part, month_part)
                start_date = f"{month}-01"
                end_date = f"{month}-{last_day:02d}"
                
                db = DB(DB_PATH)
                report = db.xnt_report(start_date, end_date, fund_source)
                self.send_json({
                    "success": True,
                    "report": report
                })
            except Exception as e:
                print(f"Error in api/xnt-report: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi tải báo cáo XNT"}, 500)

        else:
            self.send_response(404)
            self.end_headers()

    def print_to_pc_printer(self, note_type, note_id):
        try:
            conn = open_db()
            conn.row_factory = sqlite3.Row
            
            if note_type == 'purchase':
                note = conn.execute("SELECT * FROM purchase_notes WHERE id=?", (note_id,)).fetchone()
                if not note:
                    conn.close()
                    return False, "Không tìm thấy phiếu nhập"
                items = conn.execute("""
                    SELECT pi.*, p.name as productName 
                    FROM purchase_items pi
                    JOIN products p ON pi.productId = p.id
                    WHERE pi.purchaseId = ?
                    ORDER BY pi.id
                """, (note_id,)).fetchall()
            else:
                note = conn.execute("SELECT * FROM dispatch_notes WHERE id=?", (note_id,)).fetchone()
                if not note:
                    conn.close()
                    return False, "Không tìm thấy phiếu xuất"
                items = conn.execute("""
                    SELECT di.*, p.name as productName 
                    FROM dispatch_items di
                    JOIN products p ON di.productId = p.id
                    WHERE di.dispatchId = ?
                    ORDER BY di.id
                """, (note_id,)).fetchall()
            conn.close()
            
            temp_dir = tempfile.gettempdir()
            filename = f"Phieu_{'Nhap' if note_type == 'purchase' else 'Xuat'}_Kho_{note['noteNumber']}.pdf"
            pdf_path = os.path.join(temp_dir, filename)
            
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            try:
                pdfmetrics.registerFont(TTFont('TimesNewRoman', "C:\\Windows\\Fonts\\times.ttf"))
                pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', "C:\\Windows\\Fonts\\timesbd.ttf"))
                pdfmetrics.registerFont(TTFont('TimesNewRoman-Italic', "C:\\Windows\\Fonts\\timesi.ttf"))
                font_normal = 'TimesNewRoman'
                font_bold = 'TimesNewRoman-Bold'
                font_italic = 'TimesNewRoman-Italic'
            except Exception:
                font_normal = 'Helvetica'
                font_bold = 'Helvetica-Bold'
                font_italic = 'Helvetica-Oblique'
                
            doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            
            styles = getSampleStyleSheet()
            
            style_header_left = ParagraphStyle(
                'HeaderLeft', parent=styles['Normal'], fontName=font_bold, fontSize=10, leading=14, alignment=0
            )
            style_header_right = ParagraphStyle(
                'HeaderRight', parent=styles['Normal'], fontName=font_normal, fontSize=10, leading=14, alignment=2
            )
            style_title = ParagraphStyle(
                'Title', parent=styles['Heading1'], fontName=font_bold, fontSize=16, leading=20, alignment=1, spaceAfter=5
            )
            style_subtitle = ParagraphStyle(
                'Subtitle', parent=styles['Normal'], fontName=font_bold, fontSize=11, leading=14, alignment=1, spaceAfter=15
            )
            style_info = ParagraphStyle(
                'Info', parent=styles['Normal'], fontName=font_normal, fontSize=11, leading=16, alignment=0
            )
            style_table_header = ParagraphStyle(
                'TableHeader', parent=styles['Normal'], fontName=font_bold, fontSize=9, leading=11, alignment=1, textColor=colors.black
            )
            style_cell = ParagraphStyle(
                'Cell', parent=styles['Normal'], fontName=font_normal, fontSize=9, leading=11, alignment=0
            )
            style_cell_center = ParagraphStyle(
                'CellCenter', parent=styles['Normal'], fontName=font_normal, fontSize=9, leading=11, alignment=1
            )
            style_cell_right = ParagraphStyle(
                'CellRight', parent=styles['Normal'], fontName=font_normal, fontSize=9, leading=11, alignment=2
            )
            
            header_data = [
                [
                    Paragraph("SỞ Y TẾ THÀNH PHỐ CẦN THƠ<br/>TRUNG TÂM KIỂM SOÁT BỆNH TẬT (CDC)", style_header_left),
                    Paragraph(f"<b>Mẫu số: {'C30-HD' if note_type == 'purchase' else 'C31-HD'}</b><br/><i>(Ban hành theo Thông tư số 107/2017/TT-BTC)</i>", style_header_right)
                ]
            ]
            header_table = Table(header_data, colWidths=[280, 230])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("PHIẾU NHẬP KHO" if note_type == 'purchase' else "PHIẾU XUẤT KHO", style_title))
            story.append(Paragraph(f"Số: {note['noteNumber']}", style_subtitle))
            
            created_str = note['createdAt']
            try:
                created_at_dt = datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S')
            except Exception:
                try:
                    created_at_dt = datetime.strptime(created_str.split(' ')[0], '%Y-%m-%d')
                except Exception:
                    created_at_dt = datetime.now()
            
            if note_type == 'purchase':
                info_lines = [
                    f"<b>Nguồn cấp / Nhà CC:</b> {html.escape(note['supplier'])}",
                    f"<b>Lý do nhập:</b> {html.escape(note['reason'])}",
                    f"<b>Kho nhập:</b> Kho Dược CDC Cần Thơ",
                    f"<b>Ngày nhập:</b> {created_at_dt.strftime('%d-%m-%Y')}",
                    f"<b>Ghi chú:</b> {html.escape(note['note'] or 'Không')}"
                ]
            else:
                info_lines = [
                    f"<b>Đơn vị nhận:</b> {html.escape(note['receivingUnit'])}",
                    f"<b>Lý do xuất:</b> {html.escape(note['reason'])}",
                    f"<b>Kho xuất:</b> Kho Dược CDC Cần Thơ",
                    f"<b>Ngày xuất:</b> {created_at_dt.strftime('%d-%m-%Y')}",
                    f"<b>Ghi chú:</b> {html.escape(note['note'] or 'Không')}"
                ]
            for line in info_lines:
                story.append(Paragraph(line, style_info))
                story.append(Spacer(1, 4))
                
            story.append(Spacer(1, 10))
            
            if note_type == 'purchase':
                table_data = [
                    [
                        Paragraph("STT", style_table_header),
                        Paragraph("Tên thuốc, vaccine, VTYT", style_table_header),
                        Paragraph("ĐVT", style_table_header),
                        Paragraph("Số lượng", style_table_header),
                        Paragraph("Đơn giá", style_table_header),
                        Paragraph("Thành tiền", style_table_header),
                        Paragraph("Số lô", style_table_header),
                        Paragraph("Hạn dùng", style_table_header)
                    ]
                ]
                total_sum = 0.0
                for idx, it in enumerate(items, 1):
                    qty = float(it['qty'])
                    cost = float(it['cost'])
                    sub_total = float(it["totalAmount"]) if "totalAmount" in it.keys() and it["totalAmount"] is not None else qty * cost
                    total_sum += sub_total
                    table_data.append([
                        Paragraph(str(idx), style_cell_center),
                        Paragraph(html.escape(it['productName']), style_cell),
                        Paragraph(html.escape(it['unitCode']), style_cell_center),
                        Paragraph(f"{qty:g}", style_cell_right),
                        Paragraph(f"{cost:,.0f}", style_cell_right),
                        Paragraph(f"{sub_total:,.0f}", style_cell_right),
                        Paragraph(html.escape(it['lotNo'] or ''), style_cell_center),
                        Paragraph(html.escape(it['expiryDate'] or ''), style_cell_center)
                    ])
                table_data.append([
                    Paragraph("<b>Tổng cộng</b>", style_cell_center),
                    Paragraph("", style_cell),
                    Paragraph("", style_cell_center),
                    Paragraph("", style_cell_right),
                    Paragraph("", style_cell_right),
                    Paragraph(f"<b>{total_sum:,.0f}</b>", style_cell_right),
                    Paragraph("", style_cell_center),
                    Paragraph("", style_cell_center)
                ])
                col_widths = [25, 160, 45, 55, 65, 75, 55, 50]
                items_table = Table(table_data, colWidths=col_widths)
                items_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f2f2f2')),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                    ('SPAN', (0, -1), (4, -1)),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ]))
            else:
                table_data = [
                    [
                        Paragraph("STT", style_table_header),
                        Paragraph("Tên thuốc, vaccine, VTYT", style_table_header),
                        Paragraph("ĐVT", style_table_header),
                        Paragraph("Số lượng", style_table_header),
                        Paragraph("Số lô", style_table_header),
                        Paragraph("Hạn dùng", style_table_header),
                        Paragraph("Ghi chú", style_table_header)
                    ]
                ]
                for idx, it in enumerate(items, 1):
                    qty = float(it['qty'])
                    table_data.append([
                        Paragraph(str(idx), style_cell_center),
                        Paragraph(html.escape(it['productName']), style_cell),
                        Paragraph(html.escape(it['unitCode']), style_cell_center),
                        Paragraph(f"{qty:g}", style_cell_right),
                        Paragraph(html.escape(it['lotNo'] or ''), style_cell_center),
                        Paragraph(html.escape(it['expiryDate'] or ''), style_cell_center),
                        Paragraph('', style_cell)
                    ])
                col_widths = [30, 200, 50, 60, 70, 70, 50]
                items_table = Table(table_data, colWidths=col_widths)
                items_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f2f2f2')),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ]))
                
            story.append(items_table)
            story.append(Spacer(1, 15))
            
            date_right_style = ParagraphStyle(
                'DateRight', parent=styles['Normal'], fontName=font_italic, fontSize=11, alignment=2, spaceAfter=10
            )
            sig_title_style = ParagraphStyle(
                'SigTitle', parent=styles['Normal'], fontName=font_bold, fontSize=11, alignment=1
            )
            sig_sub_style = ParagraphStyle(
                'SigSub', parent=styles['Normal'], fontName=font_italic, fontSize=9, alignment=1
            )
            
            story.append(Paragraph(f"Cần Thơ, ngày {created_at_dt.strftime('%d')} tháng {created_at_dt.strftime('%m')} năm {created_at_dt.strftime('%Y')}", date_right_style))
            
            if note_type == 'purchase':
                sig_headers = [
                    [
                        Paragraph("<b>Người lập phiếu</b>", sig_title_style),
                        Paragraph("<b>Người giao hàng</b>", sig_title_style),
                        Paragraph("<b>Thủ kho</b>", sig_title_style),
                        Paragraph("<b>Kế toán trưởng</b>", sig_title_style),
                        Paragraph("<b>Lãnh đạo đơn vị</b>", sig_title_style)
                    ],
                    [
                        Paragraph("(Ký, họ tên)", sig_sub_style),
                        Paragraph("(Ký, họ tên)", sig_sub_style),
                        Paragraph("(Ký, họ tên)", sig_sub_style),
                        Paragraph("(Ký, họ tên)", sig_sub_style),
                        Paragraph("(Ký, đóng dấu)", sig_sub_style)
                    ]
                ]
            else:
                sig_headers = [
                    [
                        Paragraph("<b>Người lập phiếu</b>", sig_title_style),
                        Paragraph("<b>Người nhận hàng</b>", sig_title_style),
                        Paragraph("<b>Thủ kho</b>", sig_title_style),
                        Paragraph("<b>Kế toán trưởng</b>", sig_title_style),
                        Paragraph("<b>Lãnh đạo đơn vị</b>", sig_title_style)
                    ],
                    [
                        Paragraph("(Ký, họ tên)", sig_sub_style),
                        Paragraph("(Ký, họ tên)", sig_sub_style),
                        Paragraph("(Ký, họ tên)", sig_sub_style),
                        Paragraph("(Ký, họ tên)", sig_sub_style),
                        Paragraph("(Ký, đóng dấu)", sig_sub_style)
                    ]
                ]
                
            sig_table = Table(sig_headers, colWidths=[102, 102, 102, 102, 102])
            sig_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(sig_table)
            story.append(Spacer(1, 60))
            
            doc.build(story)
            
            try:
                os.startfile(pdf_path, 'print')
                return True, "Đã gửi lệnh in đến máy in trên máy tính"
            except Exception as pe:
                os.startfile(pdf_path)
                return True, f"Đã tạo PDF và mở trên máy tính: {str(pe)}"
        except Exception as e:
            return False, f"Lỗi tạo phiếu in: {str(e)}"

    def do_POST(self):
        if not self.check_auth():
            return
            
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception:
            self.send_json({"success": False, "message": "Dữ liệu JSON không hợp lệ"}, 400)
            return
            
        if path == "/api/auth":
            client_ip = self.client_address[0]
            now = time.time()
            block_info = FAILED_ATTEMPTS.get(client_ip)
            if block_info and now < block_info["blocked_until"]:
                secs_left = int(block_info["blocked_until"] - now)
                self.send_json({"success": False, "message": f"IP bị tạm khóa. Vui lòng thử lại sau {secs_left} giây"}, 429)
                return
                
            pin = data.get("pin", "").strip()
            if not pin:
                self.send_json({"success": False, "message": "Mã PIN không được để trống"}, 400)
                return
                
            if pin == SERVER_PIN:
                FAILED_ATTEMPTS.pop(client_ip, None)
                token = secrets.token_urlsafe(32)
                ACTIVE_TOKENS[token] = {
                    "ip": client_ip,
                    "expiry": now + 8 * 3600  # Hạn dùng 8 giờ
                }
                # Thêm audit log
                try:
                    conn = open_db()
                    conn.execute("INSERT INTO audit_logs (ip, action, details) VALUES (?, ?, ?)", 
                                 (client_ip, "LOGIN", "Đăng nhập thành công di động"))
                    conn.commit()
                    conn.close()
                except:
                    pass
                cookie = (
                    f"{SESSION_COOKIE_NAME}={urllib.parse.quote(token)}; "
                    f"Max-Age={8 * 3600}; Path=/; SameSite=Strict; HttpOnly"
                )
                self.send_json({"success": True, "token": token}, headers={"Set-Cookie": cookie})
            else:
                if not block_info:
                    FAILED_ATTEMPTS[client_ip] = {"count": 1, "blocked_until": 0}
                else:
                    FAILED_ATTEMPTS[client_ip]["count"] += 1
                    if FAILED_ATTEMPTS[client_ip]["count"] >= 5:
                        FAILED_ATTEMPTS[client_ip]["blocked_until"] = now + 5 * 60
                        
                # Ghi nhận đăng nhập thất bại
                try:
                    conn = open_db()
                    conn.execute("INSERT INTO audit_logs (ip, action, details) VALUES (?, ?, ?)", 
                                 (client_ip, "LOGIN_FAILED", f"Đăng nhập thất bại (Mã PIN sai)"))
                    conn.commit()
                    conn.close()
                except:
                    pass
                    
                attempts_left = 5 - FAILED_ATTEMPTS[client_ip]["count"] if FAILED_ATTEMPTS[client_ip]["count"] < 5 else 0
                self.send_json({"success": False, "message": f"Mã PIN sai. Còn {attempts_left} lần thử"}, 401)
                
        elif path == "/api/pc-print":
            note_type = str(data.get("type", "")).strip()
            note_id = str(data.get("id", "")).strip()
            if note_type == 'nhap':
                note_type = 'purchase'
            elif note_type == 'xuat':
                note_type = 'dispatch'
                
            if not note_type or not note_id:
                self.send_json({"success": False, "message": "Thiếu thông tin loại phiếu hoặc ID"}, 400)
                return
            
            success, msg = self.print_to_pc_printer(note_type, note_id)
            if success:
                try:
                    conn = open_db()
                    conn.execute("INSERT INTO audit_logs (ip, action, noteId, details) VALUES (?, ?, ?, ?)", 
                                 (self.client_address[0], "IN_PHIEU", int(note_id), f"In phiếu {note_type} từ di động"))
                    conn.commit()
                    conn.close()
                except Exception as ex:
                    print(f"Lỗi ghi log in phieu: {ex}")
            self.send_json({"success": success, "message": msg})
            
        elif path == "/api/create-product":
            name = data.get("name", "").strip()
            default_unit = data.get("defaultUnit", "").strip()
            barcode = data.get("barcode", "").strip() or None
            product_type = data.get("productType", "thuoc").strip()
            reg_number = data.get("registrationNumber", "").strip() or None
            
            if not name or not default_unit:
                self.send_json({"success": False, "message": "Tên sản phẩm và Đơn vị tính không được để trống"}, 400)
                return
                
            try:
                conn = open_db()
                conn.row_factory = sqlite3.Row
                
                if barcode:
                    existing = conn.execute("SELECT id, name FROM products WHERE barcode=?", (barcode,)).fetchone()
                    if existing:
                        self.send_json({"success": False, "message": f"Mã vạch này đã được sử dụng cho sản phẩm: {existing['name']}"}, 400)
                        conn.close()
                        return
                
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with conn:
                    cur = conn.execute("""
                        INSERT INTO products (name, defaultUnit, barcode, productType, registrationNumber, createdAt)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, default_unit, barcode, product_type, reg_number, now_str))
                    product_id = cur.lastrowid
                    conn.execute(
                        "INSERT OR IGNORE INTO product_units (productId, unitCode, toBaseQty, price) VALUES (?, ?, 1, 0)",
                        (product_id, default_unit)
                    )
                    try:
                        conn.execute("INSERT INTO audit_logs (ip, action, details) VALUES (?, ?, ?)",
                                     (self.client_address[0], "TAO_SAN_PHAM", f"Tạo sản phẩm di động: {name} (#{product_id}), ĐVCS: {default_unit}, loại: {product_type}"))
                    except Exception as log_err:
                        print(f"Lỗi ghi log tao san pham: {log_err}")
                
                conn.close()
                
                if hasattr(self.server, 'app_instance') and self.server.app_instance:
                    self.server.app_instance.after(0, self.server.app_instance.refresh_all_data)
                    
                self.send_json({
                    "success": True, 
                    "message": "Đã tạo sản phẩm mới thành công!", 
                    "productId": product_id,
                    "barcode": barcode or str(product_id)
                })
            except Exception as e:
                print(f"Error in api/create-product: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi tạo sản phẩm"}, 500)
                
        elif path == "/api/purchase":
            items = data.get("items")
            supplier = data.get("supplier", "Nhập kho di động").strip() or "Nhập kho di động"
            reason = data.get("reason", "Nhập qua điện thoại").strip() or "Nhập qua điện thoại"
            note = data.get("note", "Tạo tự động từ điện thoại").strip() or "Tạo tự động từ điện thoại"

            if items is None:
                product_id = data.get("productId")
                qty = data.get("qty")
                lot_no = str(data.get("lotNo", "")).strip()
                expiry_date = str(data.get("expiryDate", "")).strip()
                fund_source = str(data.get("fundSource", "")).strip()
                cost = float(data.get("cost", 0.0))
                total_amount = data.get("totalAmount")
                
                if not product_id or qty is None or not lot_no or not expiry_date:
                    self.send_json({"success": False, "message": "Vui lòng nhập đầy đủ thông tin"}, 400)
                    return
                items = [{
                    "productId": product_id,
                    "qty": qty,
                    "lotNo": lot_no,
                    "expiryDate": expiry_date,
                    "fundSource": fund_source,
                    "cost": cost,
                    "totalAmount": total_amount
                }]

            if not isinstance(items, list) or len(items) == 0:
                self.send_json({"success": False, "message": "Danh sách mặt hàng nhập trống"}, 400)
                return

            try:
                db = DB(DB_PATH)
                conn = open_db()
                conn.row_factory = sqlite3.Row
                
                for item in items:
                    p_id = item.get("productId")
                    qty = item.get("qty")
                    lot_no = str(item.get("lotNo", "")).strip()
                    expiry_date = str(item.get("expiryDate", "")).strip()
                    if not p_id or qty is None or not lot_no or not expiry_date:
                        self.send_json({"success": False, "message": "Thông tin mặt hàng nhập không đầy đủ"}, 400)
                        conn.close()
                        return
                    try:
                        item["qty"] = float(qty)
                        if item["qty"] <= 0: raise ValueError()
                    except ValueError:
                        self.send_json({"success": False, "message": "Số lượng phải là số dương lớn hơn 0"}, 400)
                        conn.close()
                        return
                        
                    if not item.get("unitCode"):
                        prod = conn.execute("SELECT defaultUnit FROM products WHERE id=?", (p_id,)).fetchone()
                        if not prod:
                            self.send_json({"success": False, "message": f"Không tìm thấy sản phẩm ID {p_id}"}, 404)
                            conn.close()
                            return
                        item["unitCode"] = prod["defaultUnit"]
                        
                    if "cost" not in item:
                        item["cost"] = 0.0
                    if item.get("totalAmount") not in (None, ""):
                        item["totalAmount"] = float(item["totalAmount"])
                    if "fundSource" not in item:
                        item["fundSource"] = ""
                        
                conn.close()
                
                purchase_id, note_num, details = db.record_purchase(items, supplier, reason, note, audit_ip=self.client_address[0])
                
                if hasattr(self.server, 'app_instance') and self.server.app_instance:
                    self.server.app_instance.after(0, self.server.app_instance.refresh_all_data)
                    
                self.send_json({
                    "success": True,
                    "message": f"Đã tạo phiếu nhập {note_num} thành công!",
                    "purchaseId": purchase_id,
                    "noteNumber": note_num
                })
            except Exception as e:
                print(f"Error in api/purchase: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi thực hiện nhập kho"}, 500)
                
        elif path == "/api/dispatch":
            items = data.get("items")
            receiving_unit = data.get("receivingUnit", "Điện thoại di động").strip() or "Điện thoại di động"
            reason_str = data.get("reason", "Xuất qua điện thoại").strip() or "Xuất qua điện thoại"
            note = data.get("note", "Tạo tự động từ điện thoại").strip() or "Tạo tự động từ điện thoại"

            if items is None:
                product_id = data.get("productId")
                lot_no = str(data.get("lotNo", "")).strip()
                qty = data.get("qty")
                fund_source = str(data.get("fundSource", "")).strip()
                
                if not product_id or qty is None:
                    self.send_json({"success": False, "message": "Vui lòng nhập đầy đủ thông tin"}, 400)
                    return
                items = [{
                    "productId": product_id,
                    "qty": qty,
                    "lotNo": lot_no,
                    "fundSource": fund_source
                }]

            if not isinstance(items, list) or len(items) == 0:
                self.send_json({"success": False, "message": "Danh sách mặt hàng xuất trống"}, 400)
                return

            try:
                db = DB(DB_PATH)
                conn = open_db()
                conn.row_factory = sqlite3.Row
                
                for item in items:
                    p_id = item.get("productId")
                    qty = item.get("qty")
                    lot_no = str(item.get("lotNo", "")).strip()
                    fund_source = str(item.get("fundSource", "")).strip()
                    
                    if not p_id or qty is None:
                        self.send_json({"success": False, "message": "Thông tin mặt hàng xuất không đầy đủ"}, 400)
                        conn.close()
                        return
                    try:
                        item["qty"] = float(qty)
                        if item["qty"] <= 0: raise ValueError()
                    except ValueError:
                        self.send_json({"success": False, "message": "Số lượng phải là số dương lớn hơn 0"}, 400)
                        conn.close()
                        return
                        
                    if not item.get("unitCode"):
                        prod = conn.execute("SELECT defaultUnit FROM products WHERE id=?", (p_id,)).fetchone()
                        if not prod:
                            self.send_json({"success": False, "message": f"Không tìm thấy sản phẩm ID {p_id}"}, 404)
                            conn.close()
                            return
                        item["unitCode"] = prod["defaultUnit"]
                        
                    if not lot_no or lot_no == "[Tự động - FEFO]":
                        item["lotNo"] = None
                    else:
                        item["lotNo"] = lot_no
                        
                    if not fund_source or fund_source == "[Tự động trừ kho]":
                        item["fundSource"] = None
                    else:
                        item["fundSource"] = fund_source
                        
                conn.close()
                
                date_str = data.get("dispatchDate") or data.get("createdAt") or data.get("date")
                if date_str:
                    date_str = str(date_str).strip()[:10]
                    
                dispatch_id, note_num, details = db.dispatch(items, receiving_unit, reason_str, note, date_str=date_str, audit_ip=self.client_address[0])
                
                if hasattr(self.server, 'app_instance') and self.server.app_instance:
                    self.server.app_instance.after(0, self.server.app_instance.refresh_all_data)
                    
                self.send_json({
                    "success": True,
                    "message": f"Đã tạo phiếu xuất {note_num} thành công!",
                    "dispatchId": dispatch_id,
                    "noteNumber": note_num
                })
            except Exception as e:
                print(f"Error in api/dispatch: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi thực hiện xuất kho"}, 500)
                
        elif path == "/api/update-barcode":
            product_id = data.get("productId")
            barcode = data.get("barcode", "").strip()
            
            if not product_id or not barcode:
                self.send_json({"success": False, "message": "Vui lòng nhập đầy đủ thông tin"}, 400)
                return
                
            try:
                conn = open_db()
                conn.row_factory = sqlite3.Row
                
                existing = conn.execute("SELECT id, name FROM products WHERE barcode=? AND id<>?", (barcode, product_id)).fetchone()
                if existing:
                    self.send_json({"success": False, "message": f"Mã vạch này đã được sử dụng cho sản phẩm: {existing['name']}"}, 400)
                    conn.close()
                    return
                    
                with conn:
                    conn.execute("UPDATE products SET barcode=? WHERE id=?", (barcode, product_id))
                    try:
                        conn.execute("INSERT INTO audit_logs (ip, action, details) VALUES (?, ?, ?)",
                                     (self.client_address[0], "DOI_MA_VACH", f"Cập nhật mã vạch sản phẩm #{product_id} thành: {barcode}"))
                    except Exception as log_err:
                        print(f"Lỗi ghi log cap nhat ma vach: {log_err}")
                    
                conn.close()
                
                if hasattr(self.server, 'app_instance') and self.server.app_instance:
                    self.server.app_instance.after(0, self.server.app_instance.refresh_all_data)
                    
                self.send_json({"success": True, "message": "Đã liên kết mã vạch thành công!"})
            except Exception as e:
                print(f"Error in api/update-barcode: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi gán mã vạch"}, 500)
                
        elif path == "/api/temperature-log":
            log_date = data.get("logDate", "").strip()
            session = data.get("session", "Sáng").strip()
            location = data.get("location", "").strip()
            temperature = data.get("temperature")
            humidity = data.get("humidity")
            recorded_by = data.get("recordedBy", "").strip()

            if not log_date or not location or temperature is None:
                self.send_json({"success": False, "message": "Vui lòng nhập đầy đủ Ngày, Vị trí và Nhiệt độ"}, 400)
                return

            try:
                temp_val = float(temperature)
                humidity_val = float(humidity) if humidity not in (None, "", "NaN") else None
            except (ValueError, TypeError):
                self.send_json({"success": False, "message": "Nhiệt độ/Độ ẩm không hợp lệ"}, 400)
                return

            try:
                db = DB(DB_PATH)
                db.add_temperature_log(log_date, session, location, temp_val, humidity_val, recorded_by)
                try:
                    db.add_audit_log(
                        action="GHI_NHIET_DO",
                        details=f"Ghi nhận nhiệt độ {temp_val}°C, độ ẩm {humidity_val}% tại '{location}' bởi {recorded_by}",
                        ip=self.client_address[0]
                    )
                except Exception as log_err:
                    print(f"Lỗi ghi log nhiet do: {log_err}")

                if hasattr(self.server, 'app_instance') and self.server.app_instance:
                    self.server.app_instance.after(0, self.server.app_instance.refresh_all_data)

                self.send_json({"success": True, "message": f"Đã ghi nhận nhiệt độ {temp_val}°C tại {location}"})
            except Exception as e:
                print(f"Error in api/temperature-log: {e}")
                self.send_json({"success": False, "message": "Lỗi hệ thống khi ghi nhận nhiệt độ"}, 500)

        else:
            self.send_response(404)
            self.end_headers()
            
    def send_json(self, data, status_code=200, headers=None):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

class MobileInventoryServer(threading.Thread):
    def __init__(self, app_instance, host="0.0.0.0", port=5000):
        super().__init__()
        self.app_instance = app_instance
        self.db_instance = app_instance.db
        self.host = host
        self.port = port
        self.server = None
        self.daemon = True
        self.is_running = False
        
    def run(self):
        # Tạo mã PIN 6 số ngẫu nhiên cho server (Lỗi 3)
        global SERVER_PIN, ACTIVE_TOKENS, FAILED_ATTEMPTS
        SERVER_PIN = "".join(secrets.choice("0123456789") for _ in range(6))
        ACTIVE_TOKENS.clear()
        FAILED_ATTEMPTS.clear()

        # Đảm bảo thư mục static và tệp tin html5-qrcode.min.js tồn tại ngoại tuyến (Lỗi 7)
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        static_dir = os.path.join(base_dir, "static")
        os.makedirs(static_dir, exist_ok=True)
        js_path = os.path.join(static_dir, "html5-qrcode.min.js")
        
        if not os.path.exists(js_path):
            print(f"Cảnh báo: Tệp tin thư viện QR ngoại tuyến không tồn tại tại: {js_path}")

        attempts = 0
        while attempts < 10:
            try:
                self.server = http.server.HTTPServer((self.host, self.port), MobileInventoryRequestHandler)
                self.server.db_instance = self.db_instance
                self.server.app_instance = self.app_instance
                self.is_running = True
                print(f"Mobile inventory server started on http://{self.host}:{self.port}")
                print(f"Xác thực PIN di động: {SERVER_PIN}")
                try:
                    self.db_instance.add_audit_log(
                        action="BAT_SERVER",
                        details=f"Máy chủ di động khởi chạy tại cổng {self.port}"
                    )
                except Exception as log_err:
                    print(f"Lỗi ghi log start server: {log_err}")
                self.server.serve_forever()
                break
            except Exception as e:
                print(f"Failed to start mobile server on port {self.port}: {e}")
                self.port += 1
                attempts += 1
                
    def stop(self):
        global ACTIVE_TOKENS, FAILED_ATTEMPTS
        ACTIVE_TOKENS.clear()
        FAILED_ATTEMPTS.clear()
        if self.server:
            try:
                self.db_instance.add_audit_log(
                    action="TAT_SERVER",
                    details="Máy chủ di động dừng hoạt động"
                )
            except Exception as log_err:
                print(f"Lỗi ghi log stop server: {log_err}")
            self.server.shutdown()
            self.server.server_close()
            self.is_running = False
            print("Mobile inventory server stopped")
