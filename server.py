# server.py — Máy chủ HTTP phục vụ ứng dụng Kiểm Kho Di Động
import http.server
import socket
import threading
import json
import urllib.parse
import sqlite3
import tempfile
import os
from datetime import datetime
import datetime as dt_module

from config import DB_PATH
from database import DB

QR_CODE_AVAILABLE = False
try:
    import qrcode
    QR_CODE_AVAILABLE = True
except ImportError:
    pass

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
        
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(MOBILE_HTML.encode("utf-8"))
            
        elif path == "/api/stock":
            barcode = query.get("barcode", [""])[0].strip()
            if not barcode:
                self.send_json({"success": False, "message": "Mã vạch trống"}, 400)
                return
                
            try:
                conn = sqlite3.connect(DB_PATH)
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
                    SELECT b.lotNo, b.expiryDate, COALESCE(SUM(sm.qty), 0) as qtyBase
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
                self.send_json({"success": False, "message": f"Database error: {str(e)}"}, 500)
            
        elif path == "/api/products":
            q_term = query.get("q", [""])[0].strip()
            filter_type = query.get("filter", [""])[0].strip()
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                
                if filter_type == 'expiring':
                    rows = conn.execute("""
                        SELECT DISTINCT p.id, p.name, p.defaultUnit, p.barcode
                        FROM products p
                        JOIN batches b ON p.id = b.productId
                        JOIN stock_movements sm ON sm.productId = b.productId AND sm.batchId = b.id
                        GROUP BY p.id, b.id
                        HAVING SUM(sm.qty) > 0.001 AND DATE(b.expiryDate) <= DATE('now', '+180 days')
                        ORDER BY p.name ASC
                    """).fetchall()
                elif filter_type == 'outofstock':
                    rows = conn.execute("""
                        SELECT p.id, p.name, p.defaultUnit, p.barcode, COALESCE(SUM(sm.qty), 0) as totalQty
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
                self.send_json({"success": False, "message": f"Database error: {str(e)}"}, 500)

        elif path == "/api/dashboard-stats":
            try:
                conn = sqlite3.connect(DB_PATH)
                total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                
                outofstock_products = conn.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT p.id, COALESCE(SUM(sm.qty), 0) as totalQty 
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
                        HAVING SUM(sm.qty) > 0.001 AND DATE(b.expiryDate) <= DATE('now', '+180 days')
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
                self.send_json({"success": False, "message": f"Database error: {str(e)}"}, 500)
            
        elif path == "/api/print-purchase":
            note_id = query.get("id", [""])[0].strip()
            if not note_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Yeu cau ID phieu nhap")
                return
            try:
                conn = sqlite3.connect(DB_PATH)
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
                """, (note_id,)).fetchall()
                conn.close()
                html = self.render_print_purchase_html(note, items)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Database error: {str(e)}".encode("utf-8"))

        elif path == "/api/print-dispatch":
            note_id = query.get("id", [""])[0].strip()
            if not note_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Yeu cau ID phieu xuat")
                return
            try:
                conn = sqlite3.connect(DB_PATH)
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
                """, (note_id,)).fetchall()
                conn.close()
                html = self.render_print_dispatch_html(note, items)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Database error: {str(e)}".encode("utf-8"))

        elif path == "/api/pc-print":
            note_type = query.get("type", [""])[0].strip() # purchase or dispatch
            note_id = query.get("id", [""])[0].strip()
            if note_type == 'nhap':
                note_type = 'purchase'
            elif note_type == 'xuat':
                note_type = 'dispatch'
                
            if not note_type or not note_id:
                self.send_json({"success": False, "message": "Thiếu thông tin loại phiếu hoặc ID"}, 400)
                return
            
            success, msg = self.print_to_pc_printer(note_type, note_id)
            self.send_json({"success": success, "message": msg})

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
                conn = sqlite3.connect(DB_PATH)
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
                self.send_json({"success": False, "message": f"Database error: {str(e)}"}, 500)

        elif path == "/api/recent-activities":
            try:
                conn = sqlite3.connect(DB_PATH)
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
                self.send_json({"success": False, "message": str(e)}, 500)

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
                self.send_json({"success": False, "message": str(e)}, 500)

        elif path == "/api/temperature-locations":
            try:
                db = DB(DB_PATH)
                locations = db.get_temperature_locations()
                self.send_json({
                    "success": True,
                    "locations": locations
                })
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, 500)

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
                self.send_json({"success": False, "message": str(e)}, 500)

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
                self.send_json({"success": False, "message": str(e)}, 500)

        else:
            self.send_response(404)
            self.end_headers()

    def render_print_purchase_html(self, note, items):
        created_str = note['createdAt']
        try:
            dt_val = datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S')
            date_formatted = dt_val.strftime('%d/%m/%Y %H:%M:%S')
        except Exception:
            date_formatted = created_str

        # Generate table rows
        rows_html = ""
        total_amount = 0.0
        for idx, it in enumerate(items, 1):
            qty = float(it['qty'])
            cost = float(it['cost'])
            amount = qty * cost
            total_amount += amount
            
            cost_str = f"{cost:,.1f}".replace(".0", "") if cost > 0 else "0"
            amount_str = f"{amount:,.1f}".replace(".0", "") if amount > 0 else "0"
            qty_str = f"{qty:,.2f}".rstrip('0').rstrip('.')
            
            expiry_str = it['expiryDate']
            try:
                exp_dt = datetime.strptime(expiry_str, '%Y-%m-%d')
                expiry_formatted = exp_dt.strftime('%d/%m/%Y')
            except Exception:
                expiry_formatted = expiry_str
                
            rows_html += f"""
            <tr>
                <td style="text-align: center;">{idx}</td>
                <td>{it['productName']}</td>
                <td style="text-align: center;">{it['unitCode']}</td>
                <td style="text-align: right;">{qty_str}</td>
                <td style="text-align: right;">{cost_str}</td>
                <td style="text-align: right;">{amount_str}</td>
                <td style="text-align: center;">{it['lotNo']}</td>
                <td style="text-align: center;">{expiry_formatted}</td>
            </tr>
            """
            
        total_amount_str = f"{total_amount:,.1f}".replace(".0", "") if total_amount > 0 else "0"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Phieu Nhap Kho {note['noteNumber']}</title>
    <style>
        body {{
            font-family: "Times New Roman", Times, serif;
            font-size: 13pt;
            line-height: 1.3;
            margin: 0;
            padding: 20px;
            color: #000;
            background-color: #fff;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        .header-left {{
            font-weight: bold;
            font-size: 11pt;
            text-align: center;
        }}
        .header-right {{
            font-size: 10pt;
            text-align: center;
        }}
        .title-block {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .title {{
            font-size: 16pt;
            font-weight: bold;
            margin: 0;
        }}
        .subtitle {{
            font-size: 12pt;
            font-weight: bold;
            margin: 5px 0 0 0;
        }}
        .info-table {{
            width: 100%;
            margin-bottom: 15px;
            border-collapse: collapse;
        }}
        .info-table td {{
            padding: 4px 0;
            vertical-align: top;
        }}
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .items-table th, .items-table td {{
            border: 1px solid #000;
            padding: 6px 8px;
            font-size: 11pt;
        }}
        .items-table th {{
            font-weight: bold;
            text-align: center;
            background-color: #f2f2f2;
        }}
        .signatures {{
            display: flex;
            justify-content: space-around;
            margin-top: 40px;
            page-break-inside: avoid;
        }}
        .signature-block {{
            text-align: center;
            width: 30%;
        }}
        .signature-title {{
            font-weight: bold;
            margin-bottom: 60px;
        }}
        .no-print-btn {{
            background: #4f46e5;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 11pt;
            font-weight: bold;
            cursor: pointer;
            margin-bottom: 20px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        @media print {{
            .no-print {{
                display: none !important;
            }}
            body {{
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align: right;">
        <button class="no-print-btn" onclick="window.print()">
            🖨️ In Phieu / Luu PDF
        </button>
    </div>
    
    <div class="header">
        <div class="header-left">
            SO Y TE THANH PHO CAN THO<br>
            TRUNG TAM KIEM SOAT BENH TAT (CDC)
        </div>
        <div class="header-right">
            <strong>Mau so: C30-HD</strong><br>
            <em>(Ban hanh theo Thong tu so 107/2017/TT-BTC)</em>
        </div>
    </div>
    
    <div class="title-block">
        <h1 class="title">PHIEU NHAP KHO</h1>
        <div class="subtitle">So: {note['noteNumber']}</div>
    </div>
    
    <table class="info-table">
        <tr>
            <td style="width: 180px;"><strong>Nguon cap / Nha CC:</strong></td>
            <td>{note['supplier']}</td>
        </tr>
        <tr>
            <td><strong>Ly do nhap:</strong></td>
            <td>{note['reason']}</td>
        </tr>
        <tr>
            <td><strong>Kho nhap:</strong></td>
            <td>Kho Duoc CDC Can Tho</td>
        </tr>
        <tr>
            <td><strong>Ngay nhap:</strong></td>
            <td>{date_formatted}</td>
        </tr>
        <tr>
            <td><strong>Ghi chu:</strong></td>
            <td>{note['note'] or 'Khong'}</td>
        </tr>
    </table>
    
    <table class="items-table">
        <thead>
            <tr>
                <th style="width: 5%;">STT</th>
                <th>Ten thuoc, vaccine, VTYT</th>
                <th style="width: 8%;">DVT</th>
                <th style="width: 12%;">So luong</th>
                <th style="width: 12%;">Don gia</th>
                <th style="width: 12%;">Thanh tien</th>
                <th style="width: 12%;">So lo</th>
                <th style="width: 12%;">Han dung</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
            <tr style="font-weight: bold;">
                <td colspan="5" style="text-align: right;">Tong cong:</td>
                <td style="text-align: right;">{total_amount_str}</td>
                <td colspan="2"></td>
            </tr>
        </tbody>
    </table>
    
    <div class="signatures">
        <div class="signature-block">
            <div class="signature-title">Nguoi giao hang</div>
            <div>(Ky, ho ten)</div>
        </div>
        <div class="signature-block">
            <div class="signature-title">Thu kho</div>
            <div>(Ky, ho ten)</div>
        </div>
        <div class="signature-block">
            <div class="signature-title">Nguoi lap phieu</div>
            <div>(Ky, ho ten)</div>
        </div>
    </div>

    <script>
        window.onload = function() {{
            setTimeout(function() {{
                window.print();
            }}, 500);
        }}
    </script>
</body>
</html>
"""
        return html

    def render_print_dispatch_html(self, note, items):
        created_str = note['createdAt']
        try:
            dt_val = datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S')
            date_formatted = dt_val.strftime('%d/%m/%Y %H:%M:%S')
        except Exception:
            date_formatted = created_str

        # Generate table rows
        rows_html = ""
        for idx, it in enumerate(items, 1):
            qty = float(it['qty'])
            qty_str = f"{qty:,.2f}".rstrip('0').rstrip('.')
            
            expiry_str = it['expiryDate']
            try:
                exp_dt = datetime.strptime(expiry_str, '%Y-%m-%d')
                expiry_formatted = exp_dt.strftime('%d/%m/%Y')
            except Exception:
                expiry_formatted = expiry_str
                
            rows_html += f"""
            <tr>
                <td style="text-align: center;">{idx}</td>
                <td>{it['productName']}</td>
                <td style="text-align: center;">{it['unitCode']}</td>
                <td style="text-align: right;">{qty_str}</td>
                <td style="text-align: center;">{it['lotNo']}</td>
                <td style="text-align: center;">{expiry_formatted}</td>
                <td></td>
            </tr>
            """
            
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Phieu Xuat Kho {note['noteNumber']}</title>
    <style>
        body {{
            font-family: "Times New Roman", Times, serif;
            font-size: 13pt;
            line-height: 1.3;
            margin: 0;
            padding: 20px;
            color: #000;
            background-color: #fff;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        .header-left {{
            font-weight: bold;
            font-size: 11pt;
            text-align: center;
        }}
        .header-right {{
            font-size: 10pt;
            text-align: center;
        }}
        .title-block {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .title {{
            font-size: 16pt;
            font-weight: bold;
            margin: 0;
        }}
        .subtitle {{
            font-size: 12pt;
            font-weight: bold;
            margin: 5px 0 0 0;
        }}
        .info-table {{
            width: 100%;
            margin-bottom: 15px;
            border-collapse: collapse;
        }}
        .info-table td {{
            padding: 4px 0;
            vertical-align: top;
        }}
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .items-table th, .items-table td {{
            border: 1px solid #000;
            padding: 6px 8px;
            font-size: 11pt;
        }}
        .items-table th {{
            font-weight: bold;
            text-align: center;
            background-color: #f2f2f2;
        }}
        .signatures {{
            display: flex;
            justify-content: space-around;
            margin-top: 40px;
            page-break-inside: avoid;
        }}
        .signature-block {{
            text-align: center;
            width: 30%;
        }}
        .signature-title {{
            font-weight: bold;
            margin-bottom: 60px;
        }}
        .no-print-btn {{
            background: #4f46e5;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 11pt;
            font-weight: bold;
            cursor: pointer;
            margin-bottom: 20px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        @media print {{
            .no-print {{
                display: none !important;
            }}
            body {{
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align: right;">
        <button class="no-print-btn" onclick="window.print()">
            🖨️ In Phieu / Luu PDF
        </button>
    </div>
    
    <div class="header">
        <div class="header-left">
            SO Y TE THANH PHO CAN THO<br>
            TRUNG TAM KIEM SOAT BENH TAT (CDC)
        </div>
        <div class="header-right">
            <strong>Mau so: C31-HD</strong><br>
            <em>(Ban hanh theo Thong tu so 107/2017/TT-BTC)</em>
        </div>
    </div>
    
    <div class="title-block">
        <h1 class="title">PHIEU XUAT KHO</h1>
        <div class="subtitle">So: {note['noteNumber']}</div>
    </div>
    
    <table class="info-table">
        <tr>
            <td style="width: 180px;"><strong>Don vi nhan:</strong></td>
            <td>{note['receivingUnit']}</td>
        </tr>
        <tr>
            <td><strong>Ly do xuat:</strong></td>
            <td>{note['reason']}</td>
        </tr>
        <tr>
            <td><strong>Kho xuat:</strong></td>
            <td>Kho Duoc CDC Can Tho</td>
        </tr>
        <tr>
            <td><strong>Ngay xuat:</strong></td>
            <td>{date_formatted}</td>
        </tr>
        <tr>
            <td><strong>Ghi chu:</strong></td>
            <td>{note['note'] or 'Khong'}</td>
        </tr>
    </table>
    
    <table class="items-table">
        <thead>
            <tr>
                <th style="width: 5%;">STT</th>
                <th>Ten thuoc, vaccine, VTYT</th>
                <th style="width: 10%;">DVT</th>
                <th style="width: 15%;">So luong</th>
                <th style="width: 15%;">So lo</th>
                <th style="width: 15%;">Han dung</th>
                <th style="width: 15%;">Ghi chu</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    
    <div class="signatures">
        <div class="signature-block">
            <div class="signature-title">Nguoi nhan hang</div>
            <div>(Ky, ho ten)</div>
        </div>
        <div class="signature-block">
            <div class="signature-title">Thu kho</div>
            <div>(Ky, ho ten)</div>
        </div>
        <div class="signature-block">
            <div class="signature-title">Nguoi lap phieu</div>
            <div>(Ky, ho ten)</div>
        </div>
    </div>

    <script>
        window.onload = function() {{
            setTimeout(function() {{
                window.print();
            }}, 500);
        }}
    </script>
</body>
</html>
"""
        return html

    def print_to_pc_printer(self, note_type, note_id):
        try:
            conn = sqlite3.connect(DB_PATH)
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
                    f"<b>Nguồn cấp / Nhà CC:</b> {note['supplier']}",
                    f"<b>Lý do nhập:</b> {note['reason']}",
                    f"<b>Kho nhập:</b> Kho Dược CDC Cần Thơ",
                    f"<b>Ngày nhập:</b> {created_at_dt.strftime('%d/%m/%Y')}",
                    f"<b>Ghi chú:</b> {note['note'] or 'Không'}"
                ]
            else:
                info_lines = [
                    f"<b>Đơn vị nhận:</b> {note['receivingUnit']}",
                    f"<b>Lý do xuất:</b> {note['reason']}",
                    f"<b>Kho xuất:</b> Kho Dược CDC Cần Thơ",
                    f"<b>Ngày xuất:</b> {created_at_dt.strftime('%d/%m/%Y')}",
                    f"<b>Ghi chú:</b> {note['note'] or 'Không'}"
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
                    sub_total = qty * cost
                    total_sum += sub_total
                    table_data.append([
                        Paragraph(str(idx), style_cell_center),
                        Paragraph(it['productName'], style_cell),
                        Paragraph(it['unitCode'], style_cell_center),
                        Paragraph(f"{qty:g}", style_cell_right),
                        Paragraph(f"{cost:,.0f}", style_cell_right),
                        Paragraph(f"{sub_total:,.0f}", style_cell_right),
                        Paragraph(it['lotNo'] or '', style_cell_center),
                        Paragraph(it['expiryDate'] or '', style_cell_center)
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
                        Paragraph(it['productName'], style_cell),
                        Paragraph(it['unitCode'], style_cell_center),
                        Paragraph(f"{qty:g}", style_cell_right),
                        Paragraph(it['lotNo'] or '', style_cell_center),
                        Paragraph(it['expiryDate'] or '', style_cell_center),
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
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception:
            self.send_json({"success": False, "message": "Dữ liệu JSON không hợp lệ"}, 400)
            return
            
        if path == "/api/create-product":
            name = data.get("name", "").strip()
            default_unit = data.get("defaultUnit", "").strip()
            barcode = data.get("barcode", "").strip() or None
            product_type = data.get("productType", "thuoc").strip()
            reg_number = data.get("registrationNumber", "").strip() or None
            
            if not name or not default_unit:
                self.send_json({"success": False, "message": "Tên sản phẩm và Đơn vị tính không được để trống"}, 400)
                return
                
            try:
                conn = sqlite3.connect(DB_PATH)
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
                self.send_json({"success": False, "message": f"Lỗi cơ sở dữ liệu: {str(e)}"}, 500)
                
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
                
                if not product_id or qty is None or not lot_no or not expiry_date:
                    self.send_json({"success": False, "message": "Vui lòng nhập đầy đủ thông tin"}, 400)
                    return
                items = [{
                    "productId": product_id,
                    "qty": qty,
                    "lotNo": lot_no,
                    "expiryDate": expiry_date,
                    "fundSource": fund_source,
                    "cost": cost
                }]

            if not isinstance(items, list) or len(items) == 0:
                self.send_json({"success": False, "message": "Danh sách mặt hàng nhập trống"}, 400)
                return

            try:
                db = DB(DB_PATH)
                conn = sqlite3.connect(DB_PATH)
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
                    if "fundSource" not in item:
                        item["fundSource"] = ""
                        
                conn.close()
                
                purchase_id, note_num, details = db.record_purchase(items, supplier, reason, note)
                
                if hasattr(self.server, 'app_instance') and self.server.app_instance:
                    self.server.app_instance.after(0, self.server.app_instance.refresh_all_data)
                    
                self.send_json({
                    "success": True,
                    "message": f"Đã tạo phiếu nhập {note_num} thành công!",
                    "purchaseId": purchase_id,
                    "noteNumber": note_num
                })
            except Exception as e:
                self.send_json({"success": False, "message": f"Lỗi cơ sở dữ liệu: {str(e)}"}, 500)
                
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
                conn = sqlite3.connect(DB_PATH)
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
                
                dispatch_id, note_num, details = db.dispatch(items, receiving_unit, reason_str, note)
                
                if hasattr(self.server, 'app_instance') and self.server.app_instance:
                    self.server.app_instance.after(0, self.server.app_instance.refresh_all_data)
                    
                self.send_json({
                    "success": True,
                    "message": f"Đã tạo phiếu xuất {note_num} thành công!",
                    "dispatchId": dispatch_id,
                    "noteNumber": note_num
                })
            except Exception as e:
                self.send_json({"success": False, "message": f"Lỗi xuất kho: {str(e)}"}, 500)
                
        elif path == "/api/update-barcode":
            product_id = data.get("productId")
            barcode = data.get("barcode", "").strip()
            
            if not product_id or not barcode:
                self.send_json({"success": False, "message": "Vui lòng nhập đầy đủ thông tin"}, 400)
                return
                
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                
                existing = conn.execute("SELECT id, name FROM products WHERE barcode=? AND id<>?", (barcode, product_id)).fetchone()
                if existing:
                    self.send_json({"success": False, "message": f"Mã vạch này đã được sử dụng cho sản phẩm: {existing['name']}"}, 400)
                    conn.close()
                    return
                    
                with conn:
                    conn.execute("UPDATE products SET barcode=? WHERE id=?", (barcode, product_id))
                    
                conn.close()
                
                if hasattr(self.server, 'app_instance') and self.server.app_instance:
                    self.server.app_instance.after(0, self.server.app_instance.refresh_all_data)
                    
                self.send_json({"success": True, "message": "Đã liên kết mã vạch thành công!"})
            except Exception as e:
                self.send_json({"success": False, "message": f"Lỗi cơ sở dữ liệu: {str(e)}"}, 500)
                
        else:
            self.send_response(404)
            self.end_headers()
            
    def send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
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
        attempts = 0
        while attempts < 10:
            try:
                self.server = http.server.HTTPServer((self.host, self.port), MobileInventoryRequestHandler)
                self.server.db_instance = self.db_instance
                self.server.app_instance = self.app_instance
                self.is_running = True
                print(f"Mobile inventory server started on http://{self.host}:{self.port}")
                self.server.serve_forever()
                break
            except Exception as e:
                print(f"Failed to start mobile server on port {self.port}: {e}")
                self.port += 1
                attempts += 1
                
    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.is_running = False
            print("Mobile inventory server stopped")

MOBILE_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Kiểm Kho Di Động</title>
    <style>
        :root {
            --primary: #0284c7;
            --primary-hover: #0369a1;
            --bg-grad: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            --glass-bg: rgba(255, 255, 255, 0.65);
            --glass-border: rgba(2, 132, 199, 0.12);
            --text-light: #0f172a;
            --text-muted: #475569;
            --success: #0d9488;
            --warning: #ea580c;
            --danger: #e11d48;
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
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 500px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        header {
            text-align: center;
            padding: 5px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }
        header h1 {
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #0369a1;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        header p {
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        .nav-tabs {
            display: flex;
            width: 100%;
            background: rgba(2, 132, 199, 0.04);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 4px;
        }
        .tab-btn {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 8px 4px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }
        .tab-btn span {
            display: inline;
        }
        @media (max-width: 480px) {
            .tab-btn {
                padding: 6px 2px;
                font-size: 0.72rem;
                flex-direction: column;
                gap: 2px;
            }
            .tab-btn span {
                font-size: 0.62rem;
            }
        }
        .tab-btn.active {
            background: var(--primary);
            color: #fff;
            box-shadow: 0 4px 12px rgba(2, 130, 199, 0.3);
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
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 15px;
            box-shadow: 0 8px 32px 0 rgba(2, 132, 199, 0.08);
        }
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
            gap: 8px;
            max-height: 50vh;
            overflow-y: auto;
            margin-top: 8px;
            padding-right: 2px;
        }
        .product-item {
            background: rgba(255, 255, 255, 0.55);
            border: 1px solid rgba(2, 132, 199, 0.08);
            border-radius: 10px;
            padding: 10px 12px;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .product-item:hover {
            background: rgba(255, 255, 255, 0.85);
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
            min-width: 500px;
        }
        .report-table th, .report-table td {
            padding: 8px 10px;
            border-bottom: 1px solid rgba(0,0,0,0.06);
            white-space: nowrap;
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
            <h1>🏥 Quản Lý Kho Di Động</h1>
            <p>Kiểm kho, Nhập/Xuất & Liên kết mã vạch nhanh chóng</p>
        </header>

        <div class="card dashboard-card" style="margin-bottom: 15px; padding: 14px; background: linear-gradient(135deg, rgba(2, 132, 199, 0.06) 0%, rgba(13, 148, 136, 0.06) 100%); border: 1px solid rgba(2, 132, 199, 0.15);">
            <div style="font-weight: 700; font-size: 0.95rem; color: var(--primary); display: flex; align-items: center; gap: 6px; margin-bottom: 12px;">
                📊 Tổng Quan Kho Hàng
                <span id="dashboard-refresh" onclick="loadDashboardStats()" style="cursor: pointer; font-size: 0.85rem; font-weight: normal; color: var(--text-muted); margin-left: auto;">🔄 Cập nhật</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; text-align: center;">
                <div style="background: rgba(255,255,255,0.75); border: 1px solid var(--glass-border); padding: 8px; border-radius: 10px;">
                    <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">Tổng Thuốc</div>
                    <div id="dash-total-products" style="font-size: 1.1rem; font-weight: 800; color: var(--text-light); margin-top: 4px;">0</div>
                </div>
                <div onclick="filterCatalog('outofstock')" style="background: rgba(255,255,255,0.75); border: 1px solid var(--glass-border); padding: 8px; border-radius: 10px; cursor: pointer; transition: transform 0.2s;">
                    <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">❌ Hết Hàng</div>
                    <div id="dash-outofstock-products" style="font-size: 1.1rem; font-weight: 800; color: #ef4444; margin-top: 4px;">0</div>
                </div>
                <div onclick="filterCatalog('expiring')" style="background: rgba(255,255,255,0.75); border: 1px solid var(--glass-border); padding: 8px; border-radius: 10px; cursor: pointer; transition: transform 0.2s;">
                    <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">⚠️ Cận Hạn</div>
                    <div id="dash-expiring-products" style="font-size: 1.1rem; font-weight: 800; color: #f59e0b; margin-top: 4px;">0</div>
                </div>
            </div>
        </div>

        <div class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('tab-checker')">🔍 <span>Kiểm Kho</span></button>
            <button class="tab-btn" onclick="switchTab('tab-temp')">🌡️ <span>Nhiệt Độ</span></button>
            <button class="tab-btn" onclick="switchTab('tab-xnt')">📊 <span>Báo cáo XNT</span></button>
            <button class="tab-btn" onclick="switchTab('tab-catalog')">📋 <span>Danh Sách</span></button>
            <button class="tab-btn" onclick="switchTab('tab-history')">📜 <span>Lịch Sử</span></button>
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
                <div class="result-title">📦 Kết quả truy vấn</div>
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
                <div class="form-title">🌡️ Nhật ký nhiệt độ & độ ẩm</div>
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
                <div style="font-weight: 700; font-size: 0.95rem; color: var(--primary); display: flex; align-items: center; gap: 6px; margin-bottom: 12px; border-bottom: 1px solid var(--glass-border); padding-bottom: 6px;">
                    📋 Nhật ký đo gần đây
                </div>
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
                <div class="form-title">📊 Tra cứu Xuất Nhập Tồn</div>
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
                <div style="font-weight: 700; font-size: 0.95rem; color: var(--primary); display: flex; align-items: center; gap: 6px; margin-bottom: 12px;">
                    📋 Bảng số liệu XNT
                </div>
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

        <div id="tab-catalog" class="tab-content">
            <div class="card">
                <button class="action-btn" style="margin-bottom: 12px; width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px; background: var(--primary); font-size: 0.9rem;" onclick="openCreateProductForm()">➕ Thêm Sản Phẩm Mới</button>
                
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
                <div class="result-title">📜 Lịch sử hoạt động gần đây</div>
                <div id="history-list" class="product-list">
                    <div style="text-align: center; color: var(--text-muted); padding: 20px;">Đang tải...</div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
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
            toast.innerHTML = (type === 'success' ? '✅' : '❌') + ` <span>${message}</span>`;
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
                    window.open(`/api/print-purchase?id=${noteId}`, '_blank');
                    closePrintModal();
                };
            } else {
                document.getElementById('print-modal-title').textContent = 'Xuất Kho Thành Công';
                btnPhone.onclick = function() {
                    window.open(`/api/print-dispatch?id=${noteId}`, '_blank');
                    closePrintModal();
                };
            }
            
            document.getElementById('print-modal').style.display = 'flex';
        }
        
        function closePrintModal() {
            document.getElementById('print-modal').style.display = 'none';
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
                            item.className = 'product-item';
                            item.style.cursor = 'default';
                            item.style.flexDirection = 'column';
                            item.style.alignItems = 'stretch';
                            item.style.gap = '8px';
                            
                            const isPurchase = act.type === 'nhap';
                            const badgeColor = isPurchase ? 'var(--success)' : 'var(--danger)';
                            const typeLabel = isPurchase ? 'NHẬP KHO' : 'XUẤT KHO';
                            
                            item.innerHTML = `
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: bold; font-size: 0.8rem; padding: 2px 6px; border-radius: 4px; background: ${badgeColor}; color: #fff;">${typeLabel}</span>
                                    <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">${formattedDate}</span>
                                </div>
                                <div style="font-weight: 600; font-size: 0.9rem; color: var(--text-light); margin: 2px 0;">Số phiếu: ${act.noteNumber}</div>
                                <div style="font-size: 0.8rem; color: var(--text-muted);">${isPurchase ? 'Nhà cung cấp' : 'Đơn vị nhận'}: ${act.details}</div>
                                <div style="display: flex; gap: 8px; margin-top: 6px; border-top: 1px solid var(--glass-border); padding-top: 8px;">
                                    <button onclick="showNotePreview('${act.type}', ${act.id})" style="flex: 1; padding: 8px; background: var(--primary); border: none; border-radius: 8px; color: #fff; font-weight: bold; font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;">
                                        🔎 Xem trước & In phiếu
                                    </button>
                                </div>
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
            const url = type === 'nhap' ? `/api/print-purchase?id=${noteId}` : `/api/print-dispatch?id=${noteId}`;
            window.open(url, '_blank');
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
                            <div class="cart-item-name">${item.productName}</div>
                            <div class="cart-item-meta">${metaText}</div>
                        </div>
                        <button class="btn-cart-remove" onclick="removeFromCart('${type}', ${index})">❌</button>
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
                        const printUrl = type === 'purchase' ? `/api/print-purchase?id=${noteId}` : `/api/print-dispatch?id=${noteId}`;
                        window.open(printUrl, '_blank');
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
                        <div style="margin-bottom: 4px;"><b>Số phiếu:</b> <span style="color: var(--primary); font-weight: bold;">${data.noteNumber}</span></div>
                        <div style="margin-bottom: 4px;"><b>Thời gian:</b> ${data.createdAt}</div>
                        <div style="margin-bottom: 4px;"><b>${data.type === 'nhap' ? 'Nhà cung cấp' : 'Đơn vị nhận'}:</b> ${data.partner}</div>
                        <div style="margin-bottom: 4px;"><b>Lý do:</b> ${data.reason}</div>
                        ${data.note ? `<div style="margin-bottom: 4px;"><b>Ghi chú:</b> ${data.note}</div>` : ''}
                    `;
                    
                    let rowsHtml = '';
                    data.items.forEach(item => {
                        rowsHtml += `
                            <tr>
                                <td style="padding: 8px 10px;">${item.productName}</td>
                                <td style="padding: 8px 10px; text-align: center;">${item.lotNo}</td>
                                <td style="padding: 8px 10px; text-align: right; font-weight: 600;">${item.qty} ${item.unit}</td>
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
                        const url = data.type === 'nhap' ? `/api/print-purchase?id=${noteId}` : `/api/print-dispatch?id=${noteId}`;
                        window.open(url, '_blank');
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

        function checkStock(barcode) {
            if (!barcode) return;
            
            resultCard.style.display = 'block';
            closeForms();
            resultContent.innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    Đang truy vấn dữ liệu kho...
                </div>
            `;

            fetch(`/api/stock?barcode=${encodeURIComponent(barcode)}`)
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
                    ⚠ Lỗi: ${msg}
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
                                <span class="batch-lot">Lô: ${b.lotNo}</span>
                                <span class="batch-qty">${b.qty} ${p.unit}</span>
                            </div>
                            <div class="batch-expiry">
                                <span>Hạn dùng: ${b.expiryDate}</span>
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
                        <span class="info-value" style="color: #a5b4fc; text-align: right; max-width: 65%;">${p.name}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Mã vạch</span>
                        <span class="info-value">${p.barcode || 'Chưa gán'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Phân loại</span>
                        <span class="info-value">${typeText}</span>
                    </div>
                    <div class="info-row" style="margin-top: 5px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                        <span class="info-label" style="font-weight: bold; color: #fff;">Tổng tồn kho</span>
                        <span class="info-value" style="color: var(--success); font-size: 1.1rem;">${data.totalQty} ${p.unit}</span>
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
                            <div class="product-item" onclick="selectProductFromCatalog('${p.barcode || p.id}')">
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
                    if (refreshBtn) refreshBtn.innerHTML = '🔄 Cập nhật';
                    if (data.success) {
                        document.getElementById('dash-total-products').textContent = data.totalProducts;
                        document.getElementById('dash-outofstock-products').textContent = data.outofstockProducts;
                        document.getElementById('dash-expiring-products').textContent = data.expiringProducts;
                    }
                })
                .catch(err => {
                    if (refreshBtn) refreshBtn.innerHTML = '🔄 Cập nhật';
                    console.error("Lỗi tải dashboard stats:", err);
                });
        }

        function selectProductFromCatalog(identifier) {
            barcodeInput.value = identifier;
            switchTab('tab-checker');
            checkStock(identifier);
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
                    
                    const identifier = data.barcode || barcode || data.productId;
                    barcodeInput.value = identifier;
                    switchTab('tab-checker');
                    checkStock(identifier);
                    
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
                url += `&fund=${encodeURIComponent(filterFund)}`;
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
                        
                        html += `
                            <tr>
                                <td style="font-weight: 600;">${escapeHtml(row.productName)}</td>
                                <td>Lô: ${escapeHtml(lotText)}<br><small style="color: var(--text-muted);">${escapeHtml(fundText)}</small></td>
                                <td style="text-align: right; font-weight: 500;">${row.openingQty} ${escapeHtml(row.unit)}</td>
                                <td style="text-align: right; color: #0d9488; font-weight: 500;">+${row.importedQty}</td>
                                <td style="text-align: right; color: #e11d48; font-weight: 500;">-${row.exportedQty}</td>
                                <td style="text-align: right; font-weight: 700; color: var(--primary);">${row.closingQty} ${escapeHtml(row.unit)}</td>
                            </tr>
                        `;
                    });
                    tbody.innerHTML = html;
                })
                .catch(err => {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 15px; color: var(--danger);">Không thể tải dữ liệu báo cáo.</td></tr>';
                });
        }

        updateCartStatus();
        loadDashboardStats();
        loadPartnersAndFunds();
    </script>
</body>
</html>"""
