# nhathuoc.py — Pharmacy Manager (Desktop — Local)
# Base Unit Only + Level 2 UI (ttkbootstrap)
# - Giá bán chuyển sang tab Nhập hàng (cập nhật khi bấm "Nhập")
# - Combobox auto-dropdown khi gõ tìm
# - Theme tươi + phông lớn hơn

import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import datetime as dt
import os, webbrowser, tempfile
import shutil
import json
import threading
import schedule
import time
from collections import defaultdict

import ttkbootstrap as tb
from ttkbootstrap.widgets import DateEntry
from ttkbootstrap.constants import *

# Import matplotlib for charts
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Import pandas for Excel processing
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Import barcode scanner libraries
try:
    import cv2
    from pyzbar import pyzbar
    from PIL import Image, ImageTk
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False

# Import PDF export libraries
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
# ==== App info ====
APP_NAME     = "Quản lý kho hàng hóa"
APP_VERSION  = "1.0.0"
AUTHOR_NAME  = "Hồ Sỷ Thoảng"
AUTHOR_EMAIL = "hstptcn5@gmail.com"
AUTHOR_PHONE = "0329381189"
AUTHOR_SITE  = "x/yoshinokuna"
# ==== /App info ====

# ==== App data paths (per-user, có quyền ghi) ====
if os.name == 'nt':
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    APP_DIR = os.path.join(base, 'Nhathuoc')
else:
    base = os.environ.get('XDG_DATA_HOME', os.path.join(os.path.expanduser('~'), '.local', 'share'))
    APP_DIR = os.path.join(base, 'nhathuoc')

os.makedirs(APP_DIR, exist_ok=True)

DB_PATH  = os.path.join(APP_DIR, 'pharm.db')
LOG_PATH = os.path.join(APP_DIR, 'app.log')
LIC_PATH = os.path.join(APP_DIR, 'license.lic')  # LicenseManager cũng dùng đường dẫn này
BACKUP_DIR = os.path.join(APP_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# Di trú DB cũ (nếu tồn tại cạnh file .py/.exe) sang APP_DIR lần đầu
OLD_DB = os.path.join(os.path.dirname(__file__), 'pharm.db')
if not os.path.exists(DB_PATH) and os.path.exists(OLD_DB):
    import shutil
    shutil.copy2(OLD_DB, DB_PATH)
# ==== end paths ====


SCHEMA_SQL = r'''
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  defaultUnit TEXT NOT NULL,
  barcode TEXT,
  productType TEXT DEFAULT 'general',
  registrationNumber TEXT,
  createdAt TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_units (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  productId INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  unitCode TEXT NOT NULL,
  toBaseQty REAL NOT NULL,
  price REAL NOT NULL DEFAULT 0,
  UNIQUE(productId, unitCode)
);

CREATE TABLE IF NOT EXISTS batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  productId INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  lotNo TEXT NOT NULL,
  expiryDate TEXT NOT NULL,
  UNIQUE(productId, lotNo)
);

CREATE TABLE IF NOT EXISTS stock_movements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  productId INTEGER NOT NULL REFERENCES products(id),
  batchId INTEGER NOT NULL REFERENCES batches(id),
  unitCode TEXT NOT NULL,
  qty REAL NOT NULL,
  type TEXT NOT NULL,
  cost REAL,
  createdAt TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
  total REAL NOT NULL,
  paid REAL NOT NULL,
  change REAL NOT NULL,
  note TEXT
);

CREATE TABLE IF NOT EXISTS sale_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  saleId INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
  productId INTEGER NOT NULL REFERENCES products(id),
  unitCode TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL
);
'''
# --- Hardware fingerprint (ổn định, không cần quyền admin) ---
def machine_fingerprint() -> str:
    import uuid, platform, hashlib, subprocess, os
    parts = [
        platform.node() or '',
        platform.system() or '',
        platform.machine() or '',
        hex(uuid.getnode()) or ''
    ]
    if os.name == 'nt':
        # cố gắng lấy 1 trong 2: BIOS serial / CSProduct UUID
        for cmd in ('wmic bios get serialnumber', 'wmic csproduct get uuid'):
            try:
                out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
                lines = [x.strip() for x in out.decode(errors='ignore').splitlines()
                         if x.strip() and 'serial' not in x.lower() and 'uuid' not in x.lower()]
                if lines:
                    parts.append(lines[-1])
                    break
            except Exception:
                pass
    raw = '|'.join(parts)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]  # 16 hex là đủ

# ---------------- DB ----------------
class DB:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.executescript(SCHEMA_SQL)

        try: self.conn.execute("ALTER TABLE products ADD COLUMN barcode TEXT")
        except sqlite3.OperationalError: pass

        self.migrate_schema()

        self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode) WHERE barcode IS NOT NULL")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sm_product_batch ON stock_movements(productId, batchId)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_batches_product ON batches(productId)")
        self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_units_unique ON product_units(productId, unitCode)")
        self.conn.commit()

    def _has_column(self, table, col):
        return any(r[1] == col for r in self.conn.execute(f"PRAGMA table_info({table})"))

    def migrate_schema(self):
        if not self._has_column('stock_movements', 'cost'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN cost REAL")

        # Thêm các trường mới cho products
        if not self._has_column('products', 'productType'):
            self.conn.execute("ALTER TABLE products ADD COLUMN productType TEXT DEFAULT 'general'")
        if not self._has_column('products', 'registrationNumber'):
            self.conn.execute("ALTER TABLE products ADD COLUMN registrationNumber TEXT")

        self.conn.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        for col, ddl in [
            ('createdAt', "ALTER TABLE sales ADD COLUMN createdAt TEXT DEFAULT CURRENT_TIMESTAMP"),
            ('total',     "ALTER TABLE sales ADD COLUMN total REAL DEFAULT 0"),
            ('paid',      "ALTER TABLE sales ADD COLUMN paid REAL DEFAULT 0"),
            ('change',    "ALTER TABLE sales ADD COLUMN change REAL DEFAULT 0"),
            ('note',      "ALTER TABLE sales ADD COLUMN note TEXT"),
        ]:
            if not self._has_column('sales', col): self.conn.execute(ddl)

        self.conn.execute("CREATE TABLE IF NOT EXISTS sale_items (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        for col, ddl in [
            ('saleId',    "ALTER TABLE sale_items ADD COLUMN saleId INTEGER REFERENCES sales(id) ON DELETE CASCADE"),
            ('productId', "ALTER TABLE sale_items ADD COLUMN productId INTEGER REFERENCES products(id)"),
            ('unitCode',  "ALTER TABLE sale_items ADD COLUMN unitCode TEXT"),
            ('qty',       "ALTER TABLE sale_items ADD COLUMN qty REAL DEFAULT 0"),
            ('price',     "ALTER TABLE sale_items ADD COLUMN price REAL DEFAULT 0"),
        ]:
            if not self._has_column('sale_items', col): self.conn.execute(ddl)

        # đảm bảo có dòng đơn vị cơ sở
        for r in self.conn.execute("SELECT id, defaultUnit FROM products"):
            if not self.conn.execute("SELECT 1 FROM product_units WHERE productId=? AND unitCode=?", (r['id'], r['defaultUnit'])).fetchone():
                self.conn.execute("INSERT INTO product_units(productId, unitCode, toBaseQty, price) VALUES(?,?,1,0)", (r['id'], r['defaultUnit']))
        self.conn.commit()

    # utils
    def q(self, sql, params=()):
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def ex(self, sql, params=()):
        cur = self.conn.execute(sql, params); self.conn.commit(); return cur.lastrowid

    def default_unit_of(self, product_id):
        r = self.q("SELECT defaultUnit FROM products WHERE id=?", (product_id,))
        return r[0]['defaultUnit'] if r else None

    def unit_info(self, product_id, unit_code):
        rs = self.q("SELECT toBaseQty, price FROM product_units WHERE productId=? AND unitCode=?", (product_id, unit_code))
        return (float(rs[0]['toBaseQty']), float(rs[0]['price'])) if rs else (None, None)

    def unit_price(self, product_id, unit_code):
        _, price = self.unit_info(product_id, unit_code); return price or 0.0

    # views
    def stock_view(self):
        sql = '''
        SELECT p.id AS productId, p.name AS productName, sm.batchId, b.lotNo, b.expiryDate,
               ROUND(SUM(sm.qty*1),4) AS qtyBase,
               COALESCE(ROUND((
                    SELECT sm2.cost/1.0 FROM stock_movements sm2
                    WHERE sm2.productId=sm.productId AND sm2.batchId=sm.batchId
                      AND sm2.type='PURCHASE' AND sm2.cost IS NOT NULL
                    ORDER BY sm2.id DESC LIMIT 1
               ),2),0) AS costBase,
               COALESCE(ROUND((
                   (SELECT sm3.cost/1.0 FROM stock_movements sm3
                    WHERE sm3.productId=sm.productId AND sm3.batchId=sm.batchId
                      AND sm3.type='PURCHASE' AND sm3.cost IS NOT NULL
                    ORDER BY sm3.id DESC LIMIT 1) * SUM(sm.qty*1)
               ),2),0) AS valueBase
        FROM stock_movements sm
        JOIN products p ON p.id=sm.productId
        JOIN batches  b ON b.id=sm.batchId
        GROUP BY p.id,p.name,sm.batchId,b.lotNo,b.expiryDate
        HAVING qtyBase<>0
        ORDER BY LOWER(p.name), DATE(b.expiryDate)
        '''
        return self.q(sql)

    def expiring_view(self, days=90):
        sql = '''
        SELECT * FROM (
            SELECT p.id AS productId, p.name AS productName, sm.batchId, b.lotNo, b.expiryDate,
                   ROUND(SUM(sm.qty*1),4) AS qtyBase
            FROM stock_movements sm
            JOIN products p ON p.id=sm.productId
            JOIN batches  b ON b.id=sm.batchId
            GROUP BY sm.productId, sm.batchId, b.lotNo, b.expiryDate
        ) v
        WHERE qtyBase>0 AND DATE(expiryDate) <= DATE('now','+' || ? || ' day')
        ORDER BY LOWER(productName), DATE(expiryDate)
        '''
        return self.q(sql, (days,))

    def stock_summary_by_product(self):
        sql = '''
        SELECT p.id AS productId, p.name AS productName, ROUND(SUM(v.qtyBase),4) AS qtyBaseTotal
        FROM ( SELECT sm.productId, sm.batchId, SUM(sm.qty*1) AS qtyBase
               FROM stock_movements sm GROUP BY sm.productId, sm.batchId ) v
        JOIN products p ON p.id=v.productId
        GROUP BY p.id, p.name HAVING qtyBaseTotal<>0
        ORDER BY LOWER(p.name)
        '''
        return self.q(sql)
    def xnt_report(self, start_date: str, end_date: str):
        """
        Báo cáo Xuất–Nhập–Tồn theo sản phẩm trong khoảng ngày [start_date, end_date].
        - Nhập:  type='PURCHASE'
        - Xuất:  type IN ('SALE','DISCARD')  (DISCARD tính như xuất)
        - Đơn vị cơ sở (toBaseQty = 1)
        """
        sql = r'''
        SELECT
          p.id   AS productId,
          p.name AS productName,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) < DATE(?) THEN sm.qty * 1
            ELSE 0 END), 4), 0) AS opening,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) BETWEEN DATE(?) AND DATE(?) AND sm.type='PURCHASE'
              THEN sm.qty * 1 ELSE 0 END), 4), 0) AS inbound,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) BETWEEN DATE(?) AND DATE(?) AND sm.type IN ('SALE','DISCARD')
              THEN -sm.qty * 1 ELSE 0 END), 4), 0) AS outbound,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) <= DATE(?) THEN sm.qty * 1
            ELSE 0 END), 4), 0) AS closing
        FROM products p
        LEFT JOIN stock_movements sm ON sm.productId = p.id
        GROUP BY p.id, p.name
        HAVING opening <> 0 OR inbound <> 0 OR outbound <> 0 OR closing <> 0
        ORDER BY LOWER(p.name)
        '''
        params = (start_date, start_date, end_date, start_date, end_date, end_date)
        return self.q(sql, params)

    def stock_summary_by_product_range(self, start_date: str, end_date: str):
        """
        Tồn theo sản phẩm trong khoảng thời gian (lọc theo createdAt của stock_movements).
        """
        sql = '''
        SELECT p.id AS productId, p.name AS productName,
               ROUND(SUM(v.qtyBase), 4) AS qtyBaseTotal
        FROM (
          SELECT sm.productId, sm.batchId, SUM(sm.qty * 1) AS qtyBase
          FROM stock_movements sm
          WHERE DATE(sm.createdAt) BETWEEN DATE(?) AND DATE(?)
          GROUP BY sm.productId, sm.batchId
        ) v
        JOIN products p ON p.id = v.productId
        GROUP BY p.id, p.name
        HAVING qtyBaseTotal <> 0
        ORDER BY LOWER(p.name)
        '''
        return self.q(sql, (start_date, end_date))

    def ensure_batch(self, product_id, lot_no, expiry_date):
        r = self.q("SELECT id FROM batches WHERE productId=? AND lotNo=?", (product_id, lot_no))
        return r[0]['id'] if r else self.ex("INSERT INTO batches(productId, lotNo, expiryDate) VALUES(?,?,?)", (product_id, lot_no, expiry_date))

    # purchase
    def add_purchase(self, items):
        try:
            self.conn.execute("BEGIN")
            for it in items:
                bid = self.ensure_batch(it['productId'], it['lotNo'], it['expiryDate'])
                self.conn.execute(
                    "INSERT INTO stock_movements(productId, batchId, unitCode, qty, type, cost) VALUES(?,?,?,?, 'PURCHASE', ?)",
                    (it['productId'], bid, it['unitCode'], it['qty'], float(it.get('cost') or 0))
                )
            self.conn.commit()
        except Exception:
            self.conn.rollback(); raise

    # sell (FEFO)
    def sell(self, items):
        total = 0.0
        for it in items:
            to_base, unit_price = self.unit_info(it['productId'], it['unitCode'])
            if to_base is None: raise Exception('Sản phẩm chưa có giá/đơn vị cơ sở')
            need_base = float(it['qty']) * to_base
            lots = self.q('''
              SELECT v.batchId, v.qtyBase, b.expiryDate FROM (
                SELECT sm.batchId, SUM(sm.qty*1) AS qtyBase
                FROM stock_movements sm WHERE sm.productId=? GROUP BY sm.batchId
              ) v JOIN batches b ON b.id=v.batchId
              WHERE v.qtyBase>0 AND DATE(b.expiryDate) >= DATE('now')
              ORDER BY DATE(b.expiryDate)
            ''', (it['productId'],))
            for lot in lots:
                if need_base <= 0: break
                take_base = min(need_base, float(lot['qtyBase']))
                take_in_unit = take_base / to_base
                self.conn.execute("INSERT INTO stock_movements(productId, batchId, unitCode, qty, type) VALUES(?,?,?,?, 'SALE')",
                                  (it['productId'], lot['batchId'], it['unitCode'], -take_in_unit))
                need_base -= take_base
            if need_base > 0: raise Exception('Không đủ tồn kho')
            total += (unit_price or 0.0) * float(it['qty'])
        return round(total, 2)

    def record_sale(self, items, paid: float, note: str = ''):
        finalized = []
        for it in items:
            price = self.unit_price(it['productId'], it['unitCode'])
            finalized.append({'productId': it['productId'], 'productName': it.get('productName') or f"#{it['productId']}",
                              'unitCode': it['unitCode'], 'qty': float(it['qty']), 'price': float(price)})
        total = round(sum(i['qty']*i['price'] for i in finalized), 2)
        paid = float(paid); change = round(paid - total, 2)
        if paid < total: raise Exception('Tiền khách đưa chưa đủ')
        try:
            self.conn.execute("BEGIN")
            self.sell(finalized)
            cur = self.conn.execute("INSERT INTO sales(total, paid, change, note) VALUES(?,?,?,?)", (total, paid, change, note))
            sale_id = cur.lastrowid
            for it in finalized:
                self.conn.execute("INSERT INTO sale_items(saleId, productId, unitCode, qty, price) VALUES(?,?,?,?,?)",
                                  (sale_id, it['productId'], it['unitCode'], it['qty'], it['price']))
            self.conn.commit()
            return sale_id, finalized, total, change
        except Exception:
            self.conn.rollback(); raise

# ---------------- Backup Manager ----------------
class BackupManager:
    def __init__(self, db_path: str, backup_dir: str):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.auto_backup_enabled = True
        self.backup_interval_hours = 24  # Mặc định 24 giờ
        self.max_backups = 30  # Giữ tối đa 30 file backup
        
    def create_backup(self, custom_name: str = None) -> str:
        """Tạo backup database"""
        try:
            timestamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
            if custom_name:
                backup_name = f"{custom_name}_{timestamp}.db"
            else:
                backup_name = f"backup_{timestamp}.db"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            shutil.copy2(self.db_path, backup_path)
            
            # Tạo file metadata
            metadata = {
                'created_at': dt.datetime.now().isoformat(),
                'db_size': os.path.getsize(self.db_path),
                'backup_size': os.path.getsize(backup_path),
                'version': APP_VERSION
            }
            
            metadata_path = backup_path.replace('.db', '.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self._cleanup_old_backups()
            return backup_path
            
        except Exception as e:
            raise Exception(f"Lỗi tạo backup: {str(e)}")
    
    def restore_backup(self, backup_path: str) -> bool:
        """Khôi phục từ backup"""
        try:
            if not os.path.exists(backup_path):
                raise Exception("File backup không tồn tại")
            
            # Tạo backup hiện tại trước khi restore
            current_backup = self.create_backup("before_restore")
            
            # Restore database
            shutil.copy2(backup_path, self.db_path)
            
            return True
            
        except Exception as e:
            raise Exception(f"Lỗi khôi phục backup: {str(e)}")
    
    def export_data(self, export_path: str) -> bool:
        """Export toàn bộ dữ liệu ra file JSON"""
        try:
            db = DB(self.db_path)
            
            export_data = {
                'export_info': {
                    'created_at': dt.datetime.now().isoformat(),
                    'version': APP_VERSION,
                    'app_name': APP_NAME
                },
                'products': db.q("SELECT * FROM products"),
                'product_units': db.q("SELECT * FROM product_units"),
                'batches': db.q("SELECT * FROM batches"),
                'stock_movements': db.q("SELECT * FROM stock_movements"),
                'sales': db.q("SELECT * FROM sales"),
                'sale_items': db.q("SELECT * FROM sale_items")
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            raise Exception(f"Lỗi export dữ liệu: {str(e)}")
    
    def import_data(self, import_path: str) -> bool:
        """Import dữ liệu từ file JSON"""
        try:
            if not os.path.exists(import_path):
                raise Exception("File import không tồn tại")
            
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Tạo backup trước khi import
            self.create_backup("before_import")
            
            db = DB(self.db_path)
            
            # Xóa dữ liệu cũ (theo thứ tự để tránh lỗi foreign key)
            db.conn.execute("DELETE FROM sale_items")
            db.conn.execute("DELETE FROM sales")
            db.conn.execute("DELETE FROM stock_movements")
            db.conn.execute("DELETE FROM batches")
            db.conn.execute("DELETE FROM product_units")
            db.conn.execute("DELETE FROM products")
            
            # Import dữ liệu mới
            for table, data in import_data.items():
                if table == 'export_info':
                    continue
                    
                if data:
                    columns = list(data[0].keys())
                    placeholders = ','.join(['?' for _ in columns])
                    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                    
                    for row in data:
                        values = [row[col] for col in columns]
                        db.conn.execute(sql, values)
            
            db.conn.commit()
            return True
            
        except Exception as e:
            raise Exception(f"Lỗi import dữ liệu: {str(e)}")
    
    def list_backups(self) -> list:
        """Lấy danh sách các file backup"""
        backups = []
        try:
            for file in os.listdir(self.backup_dir):
                if file.endswith('.db'):
                    backup_path = os.path.join(self.backup_dir, file)
                    metadata_path = backup_path.replace('.db', '.json')
                    
                    backup_info = {
                        'file': file,
                        'path': backup_path,
                        'size': os.path.getsize(backup_path),
                        'created': dt.datetime.fromtimestamp(os.path.getmtime(backup_path))
                    }
                    
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            backup_info.update(metadata)
                        except:
                            pass
                    
                    backups.append(backup_info)
            
            # Sắp xếp theo thời gian tạo (mới nhất trước)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            return []
    
    def _cleanup_old_backups(self):
        """Xóa các backup cũ nếu vượt quá số lượng cho phép"""
        try:
            backups = self.list_backups()
            if len(backups) > self.max_backups:
                for backup in backups[self.max_backups:]:
                    try:
                        os.remove(backup['path'])
                        metadata_path = backup['path'].replace('.db', '.json')
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                    except:
                        pass
        except:
            pass
    
    def start_auto_backup(self):
        """Bắt đầu tự động backup định kỳ"""
        if not self.auto_backup_enabled:
            return
            
        def backup_job():
            try:
                self.create_backup("auto")
                print(f"Auto backup completed at {dt.datetime.now()}")
            except Exception as e:
                print(f"Auto backup failed: {e}")
        
        # Lên lịch backup mỗi ngày lúc 2:00 AM
        schedule.every().day.at("02:00").do(backup_job)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Kiểm tra mỗi phút
        
        # Chạy scheduler trong thread riêng
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

# ---------------- Export Manager ----------------
class ExportManager:
    def __init__(self):
        pass
    
    def export_to_excel(self, data, filename, sheet_name="Báo cáo", headers=None):
        """Xuất dữ liệu ra file Excel"""
        if not PANDAS_AVAILABLE:
            raise Exception("Thư viện pandas chưa được cài đặt. Vui lòng chạy: pip install pandas openpyxl")
        
        try:
            # Tạo DataFrame
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # Dữ liệu từ database (list of dicts)
                    df = pd.DataFrame(data)
                else:
                    # Dữ liệu từ list thông thường
                    if headers:
                        df = pd.DataFrame(data, columns=headers)
                    else:
                        df = pd.DataFrame(data)
            else:
                raise Exception("Dữ liệu không hợp lệ")
            
            # Tạo file Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Lấy worksheet để format
                worksheet = writer.sheets[sheet_name]
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Format header
                from openpyxl.styles import Font, PatternFill
                header_font = Font(bold=True)
                header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
                
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
            
            return True
            
        except Exception as e:
            raise Exception(f"Lỗi xuất Excel: {str(e)}")
    
    def export_to_pdf(self, data, filename, title="Báo cáo", headers=None):
        """Xuất dữ liệu ra file PDF"""
        if not PDF_AVAILABLE:
            raise Exception("Thư viện reportlab chưa được cài đặt. Vui lòng chạy: pip install reportlab")
        
        try:
            # Tạo document
            doc = SimpleDocTemplate(filename, pagesize=A4)
            story = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Center
            )
            
            # Title
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
            # Tạo bảng dữ liệu
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # Dữ liệu từ database
                    if headers:
                        table_data = [headers]
                    else:
                        # Lấy headers từ keys của dict đầu tiên
                        headers = list(data[0].keys())
                        table_data = [headers]
                    
                    # Thêm dữ liệu
                    for row in data:
                        table_data.append([str(row.get(h, '')) for h in headers])
                else:
                    # Dữ liệu từ list thông thường
                    if headers:
                        table_data = [headers] + data
                    else:
                        table_data = data
                
                # Tạo bảng
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(table)
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            raise Exception(f"Lỗi xuất PDF: {str(e)}")

# ---------------- Report Manager ----------------
class ReportManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def get_revenue_report(self, start_date: str, end_date: str, group_by: str = 'day') -> list:
        """Báo cáo doanh thu theo ngày/tháng/năm"""
        try:
            db = DB(self.db_path)
            
            if group_by == 'day':
                date_format = "DATE(createdAt)"
                group_format = "DATE(createdAt)"
            elif group_by == 'month':
                date_format = "strftime('%Y-%m', createdAt)"
                group_format = "strftime('%Y-%m', createdAt)"
            elif group_by == 'year':
                date_format = "strftime('%Y', createdAt)"
                group_format = "strftime('%Y', createdAt)"
            else:
                raise Exception("group_by phải là 'day', 'month', hoặc 'year'")
            
            sql = f'''
            SELECT 
                {date_format} as period,
                COUNT(*) as total_orders,
                SUM(total) as total_revenue,
                SUM(paid) as total_paid,
                AVG(total) as avg_order_value
            FROM sales 
            WHERE DATE(createdAt) BETWEEN DATE(?) AND DATE(?)
            GROUP BY {group_format}
            ORDER BY period
            '''
            
            return db.q(sql, (start_date, end_date))
            
        except Exception as e:
            raise Exception(f"Lỗi tạo báo cáo doanh thu: {str(e)}")
    
    def get_profit_report(self, start_date: str, end_date: str) -> list:
        """Báo cáo lợi nhuận"""
        try:
            db = DB(self.db_path)
            
            sql = '''
            SELECT 
                DATE(s.createdAt) as sale_date,
                p.name as product_name,
                si.qty,
                si.price as sell_price,
                COALESCE(
                    (SELECT sm.cost FROM stock_movements sm 
                     WHERE sm.productId = si.productId 
                       AND sm.type = 'PURCHASE' 
                       AND sm.cost IS NOT NULL
                     ORDER BY sm.createdAt DESC LIMIT 1), 0
                ) as cost_price,
                (si.qty * si.price) as revenue,
                (si.qty * COALESCE(
                    (SELECT sm.cost FROM stock_movements sm 
                     WHERE sm.productId = si.productId 
                       AND sm.type = 'PURCHASE' 
                       AND sm.cost IS NOT NULL
                     ORDER BY sm.createdAt DESC LIMIT 1), 0
                )) as cost,
                (si.qty * si.price) - (si.qty * COALESCE(
                    (SELECT sm.cost FROM stock_movements sm 
                     WHERE sm.productId = si.productId 
                       AND sm.type = 'PURCHASE' 
                       AND sm.cost IS NOT NULL
                     ORDER BY sm.createdAt DESC LIMIT 1), 0
                )) as profit
            FROM sales s
            JOIN sale_items si ON s.id = si.saleId
            JOIN products p ON si.productId = p.id
            WHERE DATE(s.createdAt) BETWEEN DATE(?) AND DATE(?)
            ORDER BY s.createdAt DESC
            '''
            
            return db.q(sql, (start_date, end_date))
            
        except Exception as e:
            raise Exception(f"Lỗi tạo báo cáo lợi nhuận: {str(e)}")
    
    def get_top_products(self, start_date: str, end_date: str, limit: int = 10) -> list:
        """Top sản phẩm bán chạy"""
        try:
            db = DB(self.db_path)
            
            sql = '''
            SELECT 
                p.id as product_id,
                p.name as product_name,
                SUM(si.qty) as total_qty,
                COUNT(DISTINCT s.id) as total_orders,
                SUM(si.qty * si.price) as total_revenue,
                AVG(si.price) as avg_price
            FROM sales s
            JOIN sale_items si ON s.id = si.saleId
            JOIN products p ON si.productId = p.id
            WHERE DATE(s.createdAt) BETWEEN DATE(?) AND DATE(?)
            GROUP BY p.id, p.name
            ORDER BY total_qty DESC
            LIMIT ?
            '''
            
            return db.q(sql, (start_date, end_date, limit))
            
        except Exception as e:
            raise Exception(f"Lỗi tạo báo cáo top sản phẩm: {str(e)}")
    
    def get_daily_sales_summary(self, start_date: str, end_date: str) -> dict:
        """Tóm tắt bán hàng theo ngày"""
        try:
            db = DB(self.db_path)
            
            # Tổng quan
            summary_sql = '''
            SELECT 
                COUNT(*) as total_orders,
                SUM(total) as total_revenue,
                AVG(total) as avg_order_value,
                MIN(total) as min_order,
                MAX(total) as max_order
            FROM sales 
            WHERE DATE(createdAt) BETWEEN DATE(?) AND DATE(?)
            '''
            
            summary_result = db.q(summary_sql, (start_date, end_date))
            summary = summary_result[0] if summary_result else {
                'total_orders': 0,
                'total_revenue': 0,
                'avg_order_value': 0,
                'min_order': 0,
                'max_order': 0
            }
            
            # Doanh thu theo ngày
            daily_sql = '''
            SELECT 
                DATE(createdAt) as sale_date,
                COUNT(*) as orders,
                SUM(total) as revenue
            FROM sales 
            WHERE DATE(createdAt) BETWEEN DATE(?) AND DATE(?)
            GROUP BY DATE(createdAt)
            ORDER BY sale_date
            '''
            
            daily_data = db.q(daily_sql, (start_date, end_date))
            
            return {
                'summary': summary,
                'daily_data': daily_data
            }
            
        except Exception as e:
            raise Exception(f"Lỗi tạo tóm tắt bán hàng: {str(e)}")
    
    def get_category_performance(self, start_date: str, end_date: str) -> list:
        """Hiệu suất theo danh mục (nếu có)"""
        try:
            db = DB(self.db_path)
            
            # Tạm thời sử dụng đơn vị cơ sở làm "danh mục"
            sql = '''
            SELECT 
                p.defaultUnit as category,
                COUNT(DISTINCT si.productId) as product_count,
                SUM(si.qty) as total_qty,
                SUM(si.qty * si.price) as total_revenue,
                AVG(si.price) as avg_price
            FROM sales s
            JOIN sale_items si ON s.id = si.saleId
            JOIN products p ON si.productId = p.id
            WHERE DATE(s.createdAt) BETWEEN DATE(?) AND DATE(?)
            GROUP BY p.defaultUnit
            ORDER BY total_revenue DESC
            '''
            
            return db.q(sql, (start_date, end_date))
            
        except Exception as e:
            raise Exception(f"Lỗi tạo báo cáo danh mục: {str(e)}")

# ---------------- Medicine Catalog Manager ----------------
class MedicineCatalogManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.catalog_data = None
        self.catalog_file_path = None
        
    def load_catalog_from_excel(self, file_path: str) -> bool:
        """Load danh mục thuốc từ file Excel hoặc CSV"""
        if not PANDAS_AVAILABLE:
            raise Exception("Thư viện pandas chưa được cài đặt. Vui lòng chạy: pip install pandas openpyxl")
        
        try:
            # Đọc file Excel hoặc CSV
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path)
            
            # Chuẩn hóa tên cột (loại bỏ khoảng trắng, chuyển thành lowercase)
            df.columns = df.columns.str.strip().str.lower()
            
            # Lưu dữ liệu
            self.catalog_data = df
            self.catalog_file_path = file_path
            
            return True
            
        except Exception as e:
            raise Exception(f"Lỗi đọc file: {str(e)}")
    
    def search_medicine(self, medicine_name: str) -> list:
        """Tìm kiếm thuốc trong danh mục"""
        if self.catalog_data is None:
            return []
        
        try:
            # Tìm kiếm theo tên thuốc (không phân biệt hoa thường)
            medicine_name_lower = medicine_name.lower().strip()
            
            # Tìm kiếm trong các cột có thể chứa tên thuốc
            search_columns = []
            for col in self.catalog_data.columns:
                if any(keyword in col.lower() for keyword in ['ten', 'name', 'thuoc', 'medicine', 'san_pham', 'product']):
                    search_columns.append(col)
            
            if not search_columns:
                # Nếu không tìm thấy cột tên, sử dụng cột đầu tiên
                search_columns = [self.catalog_data.columns[0]]
            
            # Tìm kiếm
            results = []
            for col in search_columns:
                mask = self.catalog_data[col].astype(str).str.lower().str.contains(medicine_name_lower, na=False)
                matches = self.catalog_data[mask]
                
                for _, row in matches.iterrows():
                    result = {
                        'name': str(row.get(col, '')),
                        'registration_number': '',
                        'manufacturer': '',
                        'active_ingredient': '',
                        'dosage_form': '',
                        'strength': '',
                        'pack_size': '',
                        'other_info': {}
                    }
                    
                    # Tìm số đăng ký
                    for reg_col in self.catalog_data.columns:
                        if any(keyword in reg_col.lower() for keyword in ['so_dang_ky', 'registration', 'dang_ky', 'number']):
                            result['registration_number'] = str(row.get(reg_col, ''))
                            break
                    
                    # Tìm nhà sản xuất
                    for manu_col in self.catalog_data.columns:
                        if any(keyword in manu_col.lower() for keyword in ['nha_san_xuat', 'manufacturer', 'cong_ty', 'company']):
                            result['manufacturer'] = str(row.get(manu_col, ''))
                            break
                    
                    # Tìm hoạt chất
                    for active_col in self.catalog_data.columns:
                        if any(keyword in active_col.lower() for keyword in ['hoat_chat', 'active', 'ingredient', 'thanh_phan']):
                            result['active_ingredient'] = str(row.get(active_col, ''))
                            break
                    
                    # Tìm dạng bào chế
                    for form_col in self.catalog_data.columns:
                        if any(keyword in form_col.lower() for keyword in ['dang_bao_che', 'dosage', 'form', 'bao_che']):
                            result['dosage_form'] = str(row.get(form_col, ''))
                            break
                    
                    # Tìm hàm lượng
                    for strength_col in self.catalog_data.columns:
                        if any(keyword in strength_col.lower() for keyword in ['ham_luong', 'strength', 'nong_do', 'concentration']):
                            result['strength'] = str(row.get(strength_col, ''))
                            break
                    
                    # Tìm quy cách đóng gói
                    for pack_col in self.catalog_data.columns:
                        if any(keyword in pack_col.lower() for keyword in ['quy_cach', 'pack', 'size', 'dong_goi']):
                            result['pack_size'] = str(row.get(pack_col, ''))
                            break
                    
                    # Lưu thông tin khác
                    for col_name in self.catalog_data.columns:
                        if col_name not in [col] + [reg_col for reg_col in self.catalog_data.columns if any(keyword in reg_col.lower() for keyword in ['so_dang_ky', 'registration', 'dang_ky', 'number'])]:
                            result['other_info'][col_name] = str(row.get(col_name, ''))
                    
                    results.append(result)
            
            # Loại bỏ trùng lặp
            unique_results = []
            seen_names = set()
            for result in results:
                if result['name'] not in seen_names:
                    unique_results.append(result)
                    seen_names.add(result['name'])
            
            return unique_results[:10]  # Giới hạn 10 kết quả
            
        except Exception as e:
            raise Exception(f"Lỗi tìm kiếm thuốc: {str(e)}")
    
    def get_catalog_info(self) -> dict:
        """Lấy thông tin về danh mục hiện tại"""
        if self.catalog_data is None:
            return {
                'loaded': False,
                'file_path': None,
                'total_records': 0,
                'columns': []
            }
        
        return {
            'loaded': True,
            'file_path': self.catalog_file_path,
            'total_records': len(self.catalog_data),
            'columns': list(self.catalog_data.columns)
        }
    
    def get_medicine_suggestions(self, query: str, limit: int = 10) -> list:
        """Lấy danh sách gợi ý thuốc nhanh cho autocomplete"""
        if self.catalog_data is None or not query.strip():
            return []
        
        try:
            query_lower = query.lower().strip()
            suggestions = []
            
            # Tìm kiếm trong các cột có thể chứa tên thuốc
            search_columns = []
            for col in self.catalog_data.columns:
                if any(keyword in col.lower() for keyword in ['ten', 'name', 'thuoc', 'medicine', 'san_pham', 'product']):
                    search_columns.append(col)
            
            if not search_columns:
                search_columns = [self.catalog_data.columns[0]]
            
            # Tìm kiếm và tạo gợi ý
            for col in search_columns:
                mask = self.catalog_data[col].astype(str).str.lower().str.contains(query_lower, na=False)
                matches = self.catalog_data[mask].head(limit)
                
                for _, row in matches.iterrows():
                    name = str(row.get(col, ''))
                    if name and name.lower() not in [s['name'].lower() for s in suggestions]:
                        # Tìm số đăng ký
                        reg_number = ''
                        for reg_col in self.catalog_data.columns:
                            if any(keyword in reg_col.lower() for keyword in ['so_dang_ky', 'registration', 'dang_ky', 'number']):
                                reg_number = str(row.get(reg_col, ''))
                                break
                        
                        suggestions.append({
                            'name': name,
                            'registration_number': reg_number,
                            'display_text': f"{name} - {reg_number}" if reg_number else name
                        })
            
            return suggestions[:limit]
            
        except Exception as e:
            return []
    
    def clear_catalog(self):
        """Xóa danh mục hiện tại"""
        self.catalog_data = None
        self.catalog_file_path = None

# ---------------- UI ----------------
class App(tb.Window):
    def __init__(self):
        super().__init__(themename='minty')  # tươi sáng; thử 'pulse' hoặc 'cosmo' nếu thích
        self.title(f'{APP_NAME} — v{APP_VERSION}')
        self.geometry('1180x840'); self.minsize(1100, 740)

        self.db = DB(DB_PATH)
        self.backup_manager = BackupManager(DB_PATH, BACKUP_DIR)
        self.report_manager = ReportManager(DB_PATH)
        self.export_manager = ExportManager()
        self.medicine_catalog = MedicineCatalogManager(DB_PATH)
        self.last_sale_items = []; self.cart = []

        self.make_style()
        
        # Tạo UI sau khi window đã sẵn sàng
        self.after(100, self.initialize_ui)
        
        # Bắt đầu auto backup
        self.backup_manager.start_auto_backup()
    
    def initialize_ui(self):
        """Khởi tạo UI sau khi window đã sẵn sàng"""
        try:
            self.make_ui()
            # Load dữ liệu sau khi UI đã được tạo
            self.after(200, self.on_ready)
        except Exception as e:
            print(f"Lỗi khởi tạo UI: {e}")
            # Fallback: tạo UI cơ bản
            self.create_basic_ui()
    
    def create_basic_ui(self):
        """Tạo UI cơ bản nếu có lỗi"""
        self.title(f'{APP_NAME} — v{APP_VERSION} — Lỗi khởi tạo')
        tb.Label(self, text="Có lỗi xảy ra khi khởi tạo giao diện. Vui lòng khởi động lại ứng dụng.", 
                font=('Segoe UI', 12)).pack(expand=True)

    # theme & fonts
    def make_style(self):
        style = tb.Style()
        # Ẩn header Notebook để tránh “trùng thẻ”
        style.layout('TNotebook.Tab', [])
        # Font to hơn
        style.configure('TLabel', font=('Segoe UI', 11))
        style.configure('TButton', font=('Segoe UI', 11))
        style.configure('TEntry',  font=('Segoe UI', 11))
        style.configure('TCombobox', font=('Segoe UI', 11))
        style.configure('Treeview', rowheight=30, font=('Segoe UI', 11))
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'))

    # helpers
    def _numberize(self, entry: tb.Entry):
        entry.config(justify='right')
        entry.bind('<FocusIn>', lambda e: entry.selection_range(0, 'end'))
    def open_combo(self, combo):
        combo.focus_set()
        combo.event_generate('<Alt-Down>')
    def _open_dropdown(self, combo: tb.Combobox):
        combo.focus_set()
        # kích hoạt menu xổ xuống (Alt+Down)
        combo.event_generate('<Alt-Down>')

    def toast(self, text, ms=1600):
        w = tk.Toplevel(self); w.wm_overrideredirect(True); w.configure(bg='#111')
        tk.Label(w, text='  ' + text + '  ', bg='#111', fg='white', font=('Segoe UI', 10)).pack()
        w.update_idletasks()
        x = self.winfo_x() + self.winfo_width() - w.winfo_width() - 20
        y = self.winfo_y() + self.winfo_height() - w.winfo_height() - 20
        w.geometry(f'+{x}+{y}'); w.after(ms, w.destroy)

    # layout
    def make_ui(self):
        menubar = tk.Menu(self); self.config(menu=menubar)
        helpm = tk.Menu(menubar, tearoff=0); helpm.add_command(label='Phím tắt', command=self.show_shortcuts)
        helpm.add_separator()
        helpm.add_command(label='Mở thư mục dữ liệu', command=self.open_data_folder)
        helpm.add_command(label='Giới thiệu (About)…', command=self.show_about)
        menubar.add_cascade(label='Trợ giúp', menu=helpm)
        
        self.nb = tb.Notebook(self); self.nb.pack(fill=BOTH, expand=True, padx=8, pady=(0,8))
        
        # Tạo các tab frames
        self.tab_products = tb.Frame(self.nb)
        self.tab_purchase = tb.Frame(self.nb)
        self.tab_pos = tb.Frame(self.nb)
        self.tab_stock = tb.Frame(self.nb)
        self.tab_alerts = tb.Frame(self.nb)
        self.tab_report = tb.Frame(self.nb)
        self.tab_backup = tb.Frame(self.nb)
        self.tab_advanced_reports = tb.Frame(self.nb)
        
        # Thêm tabs với labels đẹp hơn
        tabs_config = [
            (self.tab_products, "🏷️ Sản phẩm"),
            (self.tab_purchase, "📦 Nhập hàng"),
            (self.tab_pos, "🧾 POS"),
            (self.tab_stock, "📊 Tồn kho"),
            (self.tab_alerts, "⏰ Hết hạn"),
            (self.tab_report, "📄 Báo cáo"),
            (self.tab_backup, "💾 Backup"),
            (self.tab_advanced_reports, "📈 Báo cáo nâng cao")
        ]
        
        for tab, label in tabs_config:
            self.nb.add(tab, text=label)
        
        # Tạo toolbar sau khi đã có các tabs
        self.create_toolbar()
        
        self.build_products_tab(); self.build_purchase_tab(); self.build_pos_tab()
        self.build_stock_tab(); self.build_alerts_tab(); self.build_report_tab()
        self.build_backup_tab(); self.build_advanced_reports_tab()
        # Status bar với thông tin chi tiết hơn
        status_frame = tb.Frame(self)
        status_frame.pack(fill='x', side='bottom', padx=8, pady=4)
        
        # Status chính
        self.status = tb.Label(status_frame, anchor='w', font=('Segoe UI', 9),
            text='Sẵn sàng • F1-F8: Chuyển tab • F9: In hóa đơn • Ctrl+F: Tìm kiếm')
        self.status.pack(side='left')
        
        # Thông tin database
        self.db_status = tb.Label(status_frame, anchor='e', font=('Segoe UI', 9),
            text='Database: Đang kết nối...')
        self.db_status.pack(side='right')
        
        # Cập nhật status database
        self.update_db_status()
        
    def update_db_status(self):
        """Cập nhật trạng thái database"""
        try:
            # Đếm số sản phẩm
            product_count = self.db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            # Đếm số batch
            batch_count = self.db.conn.execute("SELECT COUNT(*) FROM batches").fetchone()[0]
            # Đếm số đơn hàng
            sale_count = self.db.conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
            
            self.db_status.config(text=f"Database: {product_count} sản phẩm • {batch_count} lô • {sale_count} đơn hàng")
        except Exception as e:
            self.db_status.config(text=f"Database: Lỗi - {str(e)}")
        
        # Hotkeys
        self.bind('<F1>', lambda e: self.nb.select(self.tab_products))
        self.bind('<F2>', lambda e: self.nb.select(self.tab_purchase))
        self.bind('<F3>', lambda e: (self.nb.select(self.tab_pos), self.search_pos.focus_set()))
        self.bind('<F4>', lambda e: self.nb.select(self.tab_stock))
        self.bind('<F5>', lambda e: self.nb.select(self.tab_alerts))
        self.bind('<F6>', lambda e: self.nb.select(self.tab_report))
        self.bind('<F7>', lambda e: self.nb.select(self.tab_backup))
        self.bind('<F8>', lambda e: self.nb.select(self.tab_advanced_reports))
        self.bind('<Control-f>', lambda e: self.focus_search())
        self.bind('<F9>', lambda e: self.print_invoice())
        self.bind('<Control-Return>', lambda e: self.checkout_cart())

    def create_toolbar(self):
        tbbar = tb.Frame(self); tbbar.pack(fill='x', padx=8, pady=(8,8))
        
        # Tạo frame chứa các nút chính
        main_buttons = tb.Frame(tbbar)
        main_buttons.pack(side='left')
        
        # Các nút chính với style cải thiện
        buttons_config = [
            ('🏷️ Sản phẩm', 'primary', self.tab_products, 'F1'),
            ('📦 Nhập hàng', 'success', self.tab_purchase, 'F2'),
            ('🧾 POS', 'warning', self.tab_pos, 'F3'),
            ('📊 Tồn kho', 'info', self.tab_stock, 'F4'),
            ('⏰ Hết hạn', 'danger', self.tab_alerts, 'F5'),
            ('📄 Báo cáo', 'secondary', self.tab_report, 'F6'),
            ('💾 Backup', 'dark', self.tab_backup, 'F7'),
            ('📈 Báo cáo nâng cao', 'primary', self.tab_advanced_reports, 'F8')
        ]
        
        for text, style, tab, shortcut in buttons_config:
            btn = tb.Button(main_buttons, text=text, bootstyle=style,
                          command=lambda t=tab: self.nb.select(t))
            btn.pack(side='left', padx=2)
            # Thêm tooltip với phím tắt
            self.create_tooltip(btn, f"{text} ({shortcut})")
        
        # Spacer
        tb.Label(tbbar, text='').pack(side='left', expand=True)
        
        # Nút in hóa đơn
        print_btn = tb.Button(tbbar, text='🖨️ In hóa đơn', bootstyle='outline-primary',
                             command=self.print_invoice)
        print_btn.pack(side='right', padx=4)
        self.create_tooltip(print_btn, "In hóa đơn (F9)")
        
        # Nút backup nhanh
        backup_btn = tb.Button(tbbar, text='💾 Backup nhanh', bootstyle='outline-success',
                              command=self.create_manual_backup)
        backup_btn.pack(side='right', padx=4)
        self.create_tooltip(backup_btn, "Tạo backup ngay lập tức")

    def create_tooltip(self, widget, text):
        """Tạo tooltip cho widget"""
        def show_tooltip(event):
            tooltip = tb.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tb.Label(tooltip, text=text, background='#ffffe0', 
                           relief='solid', borderwidth=1, font=('Segoe UI', 9))
            label.pack()
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def show_shortcuts(self):
        messagebox.showinfo('Phím tắt',
            'F1: Tạo sản phẩm\nF2: Nhập hàng (Ctrl+F tìm)\nF3: POS (Ctrl+F tìm, Enter=Thêm vào giỏ, Ctrl+Enter=Thanh toán, F9=In)\nF4: Tồn theo lô\nF5: Sắp hết hạn\nF6: Báo cáo tồn kho')

    def focus_search(self):
        idx = self.nb.index(self.nb.select())
        if idx == 1 and hasattr(self, 'search_purchase'): self.search_purchase.focus_set()
        elif idx == 2 and hasattr(self, 'search_pos'): self.search_pos.focus_set()
    def open_data_folder(self):
        import sys, subprocess, os
        path = APP_DIR  # đã có sẵn từ phần cấu hình đường dẫn
        try:
            if sys.platform.startswith('win'):
                os.startfile(path)  # type: ignore
            elif sys.platform == 'darwin':
                subprocess.call(['open', path])
            else:
                subprocess.call(['xdg-open', path])
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def show_about(self):
        # Lấy trạng thái license (nếu có LicenseManager)
        lic_text = 'Chưa kích hoạt'
        try:
            data = LicenseManager().load()
            lic_text = f"Khách hàng: {data.get('customer','(n/a)')}"
        except Exception:
            pass

        fp = None
        try:
            fp = machine_fingerprint()
        except Exception:
            fp = '(không có)'

        info = (
            f"{APP_NAME} v{APP_VERSION}\n"
            f"Tác giả: {AUTHOR_NAME}\n"
            f"Điện thoại: {AUTHOR_PHONE}\n"
            f"Email: {AUTHOR_EMAIL}\n"
            f"Website: {AUTHOR_SITE}\n\n"
            f"Fingerprint máy: {fp}\n"
            f"License: {lic_text}\n"
            f"Thư mục dữ liệu: {APP_DIR}"
        )
        if messagebox.askyesno("Giới thiệu", info + "\n\nMở website tác giả?"):
            try:
                import webbrowser
                webbrowser.open(AUTHOR_SITE)
            except Exception:
                pass

    # -------- Products --------
    def build_products_tab(self):
        frm = self.tab_products
        
        # Khung quản lý danh mục thuốc với style cải thiện
        catalog_frame = tb.Labelframe(frm, text='📚 Quản lý danh mục thuốc', bootstyle='info')
        catalog_frame.pack(fill='x', padx=8, pady=8)
        
        catalog_btn_frame = tb.Frame(catalog_frame)
        catalog_btn_frame.pack(fill='x', padx=8, pady=8)
        
        tb.Button(catalog_btn_frame, text='📁 Load danh mục CSV/Excel', bootstyle='info',
                  command=self.load_medicine_catalog).pack(side='left', padx=4)
        tb.Button(catalog_btn_frame, text='📄 Load thuoc.csv', bootstyle='primary',
                  command=self.load_default_csv).pack(side='left', padx=4)
        tb.Button(catalog_btn_frame, text='🔍 Tra cứu thuốc', bootstyle='success',
                  command=self.search_medicine_dialog).pack(side='left', padx=4)
        tb.Button(catalog_btn_frame, text='ℹ️ Thông tin danh mục', bootstyle='secondary',
                  command=self.show_catalog_info).pack(side='left', padx=4)
        
        # Hiển thị thông tin danh mục hiện tại
        self.catalog_info_label = tb.Label(catalog_frame, text='Chưa load danh mục thuốc', 
                                          font=('Segoe UI', 9), bootstyle='secondary')
        self.catalog_info_label.pack(anchor='w', padx=8, pady=(0,4))
        
        # Hướng dẫn sử dụng
        help_label = tb.Label(catalog_frame, 
                             text='💡 Gợi ý: Load danh mục thuốc, sau đó gõ tên thuốc để xem gợi ý tự động', 
                             font=('Segoe UI', 8), bootstyle='info')
        help_label.pack(anchor='w', padx=8, pady=(0,8))
        
        # Khung thông tin sản phẩm với style cải thiện
        f1 = tb.Labelframe(frm, text='📝 Thông tin sản phẩm', bootstyle='light')
        f1.pack(fill='x', padx=8, pady=8)
        
        # Hàng 1: Tên sản phẩm và loại
        tb.Label(f1, text='Tên sản phẩm:').grid(row=0, column=0, sticky='w', padx=6, pady=6)
        self.p_name = tb.Entry(f1, width=35)
        self.p_name.grid(row=0, column=1, padx=6, pady=6)
        self.p_name.bind('<KeyRelease>', self.on_product_name_change)
        self.p_name.bind('<FocusOut>', self.on_product_name_focus_out)
        
        # Tạo frame chứa dropdown gợi ý
        self.suggestions_frame = tb.Frame(f1)
        self.suggestions_frame.grid(row=1, column=1, sticky='ew', padx=6, pady=(0,6))
        self.suggestions_frame.grid_remove()  # Ẩn ban đầu
        
        # Tạo Listbox cho gợi ý
        self.suggestions_listbox = tk.Listbox(self.suggestions_frame, height=6, width=35)
        self.suggestions_listbox.pack(fill='both', expand=True)
        self.suggestions_listbox.bind('<Double-Button-1>', self.on_suggestion_selected)
        self.suggestions_listbox.bind('<Button-1>', self.on_suggestion_click)
        self.suggestions_listbox.bind('<ButtonRelease-1>', self.on_suggestion_click)
        self.suggestions_listbox.bind('<Return>', self.on_suggestion_selected)
        self.suggestions_listbox.bind('<Escape>', self.hide_suggestions)
        
        # Bind keyboard navigation
        self.p_name.bind('<Down>', self.on_arrow_down)
        self.p_name.bind('<Up>', self.on_arrow_up)
        self.suggestions_listbox.bind('<Up>', self.on_suggestion_up)
        self.suggestions_listbox.bind('<Down>', self.on_suggestion_down)
        
        tb.Label(f1, text='Loại sản phẩm:').grid(row=0, column=2, sticky='w', padx=6, pady=6)
        self.p_type = tb.Combobox(f1, values=['general', 'medicine'], state='readonly', width=12)
        self.p_type.set('general')
        self.p_type.grid(row=0, column=3, padx=6, pady=6)
        self.p_type.bind('<<ComboboxSelected>>', self.on_product_type_change)
        
        # Hàng 2: Đơn vị và Barcode
        tb.Label(f1, text='Đơn vị cơ sở:').grid(row=1, column=0, sticky='w', padx=6, pady=6)
        self.p_base = tb.Entry(f1, width=12)
        self.p_base.insert(0, 'vien')
        self.p_base.grid(row=1, column=1, padx=6, pady=6)
        
        tb.Label(f1, text='Barcode:').grid(row=1, column=2, sticky='w', padx=6, pady=6)
        barcode_frame = tb.Frame(f1)
        barcode_frame.grid(row=1, column=3, padx=6, pady=6, sticky='ew')
        
        self.p_barcode = tb.Entry(barcode_frame, width=16)
        self.p_barcode.pack(side='left')
        
        # Nút quét barcode cho sản phẩm mới
        if BARCODE_AVAILABLE:
            tb.Button(barcode_frame, text='📷', command=self.scan_barcode_for_product, 
                     bootstyle='info', width=3).pack(side='left', padx=(5, 0))
        else:
            tb.Button(barcode_frame, text='📷', command=self.show_barcode_install_info, 
                     bootstyle='secondary', width=3).pack(side='left', padx=(5, 0))
        
        # Hàng 3: Số đăng ký (chỉ hiển thị khi chọn loại thuốc)
        self.p_reg_label = tb.Label(f1, text='Số đăng ký:')
        self.p_reg_label.grid(row=2, column=0, sticky='w', padx=6, pady=6)
        self.p_reg_label.grid_remove()  # Ẩn ban đầu
        
        self.p_reg_number = tb.Entry(f1, width=35)
        self.p_reg_number.grid(row=2, column=1, columnspan=2, padx=6, pady=6)
        self.p_reg_number.grid_remove()  # Ẩn ban đầu
        
        # Nút lưu
        btns = tb.Frame(frm)
        btns.pack(fill='x', padx=8, pady=8)
        tb.Button(btns, text='💾 Lưu sản phẩm', bootstyle='primary', command=self.save_product).pack(side='right')

    def save_product(self):
        name = self.p_name.get().strip()
        base = self.p_base.get().strip() or 'vien'
        bc = self.p_barcode.get().strip() or None
        product_type = self.p_type.get()
        reg_number = self.p_reg_number.get().strip() or None if product_type == 'medicine' else None
        
        if not name: 
            messagebox.showerror('Lỗi','Nhập tên sản phẩm')
            return
        
        pid = self.db.ex("INSERT INTO products(name, defaultUnit, barcode, productType, registrationNumber) VALUES(?,?,?,?,?)", 
                        (name, base, bc, product_type, reg_number))
        
        # bảo đảm product_units base tồn tại
        try:
            self.db.ex("INSERT INTO product_units(productId, unitCode, toBaseQty, price) VALUES(?,?,1,0)", (pid, base))
        except sqlite3.IntegrityError:
            pass
        
        self.toast(f'Đã tạo sản phẩm #{pid}')
        self.refresh_products()
        
        # Clear form
        self.p_name.delete(0, tk.END)
        self.p_barcode.delete(0, tk.END)
        self.p_reg_number.delete(0, tk.END)
        self.p_type.set('general')
        self.on_product_type_change()
        self.hide_suggestions()

    def on_product_type_change(self, event=None):
        """Xử lý khi thay đổi loại sản phẩm"""
        product_type = self.p_type.get()
        if product_type == 'medicine':
            self.p_reg_label.grid()
            self.p_reg_number.grid()
        else:
            self.p_reg_label.grid_remove()
            self.p_reg_number.grid_remove()

    def on_product_name_change(self, event=None):
        """Xử lý khi thay đổi tên sản phẩm - hiển thị autocomplete"""
        if self.medicine_catalog.catalog_data is None:
            return
        
        query = self.p_name.get().strip()
        
        if len(query) >= 2:  # Chỉ tìm kiếm khi có ít nhất 2 ký tự
            try:
                suggestions = self.medicine_catalog.get_medicine_suggestions(query, 8)
                
                if suggestions:
                    # Hiển thị listbox với gợi ý
                    self.suggestions_listbox.delete(0, tk.END)
                    for suggestion in suggestions:
                        self.suggestions_listbox.insert(tk.END, suggestion['display_text'])
                    
                    # Lưu suggestions để sử dụng sau
                    self.current_suggestions = suggestions
                    
                    # Hiển thị frame gợi ý
                    self.suggestions_frame.grid()
                else:
                    # Không có gợi ý, ẩn frame
                    self.hide_suggestions()
            except Exception as e:
                # Lỗi trong autocomplete, ẩn gợi ý
                self.hide_suggestions()
        else:
            # Ẩn gợi ý khi ít hơn 2 ký tự
            self.hide_suggestions()

    def hide_suggestions(self, event=None):
        """Ẩn danh sách gợi ý"""
        self.suggestions_frame.grid_remove()
        self.current_suggestions = []

    def on_suggestion_click(self, event=None):
        """Xử lý khi click vào gợi ý từ listbox"""
        try:
            print(f"DEBUG: Click vào listbox, event.y = {event.y}")
            # Lấy index của item được click
            index = self.suggestions_listbox.nearest(event.y)
            print(f"DEBUG: Index được chọn = {index}")
            
            self.suggestions_listbox.selection_clear(0, tk.END)
            self.suggestions_listbox.selection_set(index)
            self.suggestions_listbox.activate(index)
            
            # Chọn ngay lập tức
            self.on_suggestion_selected()
            
        except Exception as e:
            print(f"Lỗi khi click gợi ý: {e}")
            import traceback
            traceback.print_exc()

    def on_suggestion_selected(self, event=None):
        """Xử lý khi chọn gợi ý từ listbox"""
        try:
            selection = self.suggestions_listbox.curselection()
            if not selection:
                return
            
            selected_index = selection[0]
            if hasattr(self, 'current_suggestions') and selected_index < len(self.current_suggestions):
                medicine = self.current_suggestions[selected_index]
                
                print(f"DEBUG: Chọn thuốc: {medicine['name']}")
                
                # Điền thông tin vào form
                self.p_name.delete(0, tk.END)
                self.p_name.insert(0, medicine['name'])
                self.p_type.set('medicine')
                self.on_product_type_change()
                
                # Điền số đăng ký
                if medicine['registration_number']:
                    self.p_reg_number.delete(0, tk.END)
                    self.p_reg_number.insert(0, medicine['registration_number'])
                
                # Tự động điền đơn vị cơ sở cho thuốc
                self.p_base.delete(0, tk.END)
                self.p_base.insert(0, 'vien')  # Đơn vị mặc định cho thuốc
                
                # Ẩn gợi ý và chuyển focus
                self.hide_suggestions()
                self.p_barcode.focus_set()  # Chuyển focus sang barcode
                
        except Exception as e:
            print(f"Lỗi khi chọn gợi ý: {e}")
            import traceback
            traceback.print_exc()

    def on_product_name_focus_out(self, event=None):
        """Xử lý khi mất focus khỏi ô tên sản phẩm"""
        # Delay một chút để cho phép click vào listbox
        self.after(500, self.hide_suggestions)

    def on_arrow_down(self, event=None):
        """Xử lý phím mũi tên xuống"""
        if self.suggestions_frame.winfo_viewable():
            self.suggestions_listbox.focus_set()
            self.suggestions_listbox.selection_set(0)
            return "break"
        return None

    def on_arrow_up(self, event=None):
        """Xử lý phím mũi tên lên"""
        if self.suggestions_frame.winfo_viewable():
            self.suggestions_listbox.focus_set()
            self.suggestions_listbox.selection_set(tk.END)
            return "break"
        return None

    def on_suggestion_up(self, event=None):
        """Xử lý phím mũi tên lên trong listbox"""
        current = self.suggestions_listbox.curselection()
        if current and current[0] > 0:
            self.suggestions_listbox.selection_clear(current[0])
            self.suggestions_listbox.selection_set(current[0] - 1)
        return "break"

    def on_suggestion_down(self, event=None):
        """Xử lý phím mũi tên xuống trong listbox"""
        current = self.suggestions_listbox.curselection()
        if current and current[0] < self.suggestions_listbox.size() - 1:
            self.suggestions_listbox.selection_clear(current[0])
            self.suggestions_listbox.selection_set(current[0] + 1)
        return "break"

    def load_medicine_catalog(self):
        """Load danh mục thuốc từ file Excel hoặc CSV"""
        try:
            file_path = filedialog.askopenfilename(
                title="Chọn file danh mục thuốc",
                filetypes=[
                    ('CSV files', '*.csv'),
                    ('Excel files', '*.xlsx *.xls'),
                    ('All files', '*.*')
                ]
            )
            
            if file_path:
                self.medicine_catalog.load_catalog_from_excel(file_path)
                self.update_catalog_info()
                self.toast('Đã load danh mục thuốc thành công')
                
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def load_default_csv(self):
        """Load file thuoc.csv mặc định"""
        try:
            # Tìm file thuoc.csv trong thư mục hiện tại
            csv_path = os.path.join(os.getcwd(), 'thuoc.csv')
            
            if os.path.exists(csv_path):
                self.medicine_catalog.load_catalog_from_excel(csv_path)
                self.update_catalog_info()
                self.toast('Đã load file thuoc.csv thành công')
            else:
                # Nếu không tìm thấy, mở dialog chọn file
                messagebox.showinfo('Thông báo', 
                    f'Không tìm thấy file thuoc.csv trong thư mục:\n{csv_path}\n\nVui lòng chọn file khác.')
                self.load_medicine_catalog()
                
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def search_medicine_dialog(self):
        """Hiển thị dialog tra cứu thuốc"""
        if self.medicine_catalog.catalog_data is None:
            messagebox.showwarning('Cảnh báo', 'Vui lòng load danh mục thuốc trước')
            return
        
        # Tạo dialog tra cứu
        dialog = tb.Toplevel(self)
        dialog.title("Tra cứu thuốc")
        dialog.geometry("800x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (800 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (600 // 2)
        dialog.geometry(f"800x600+{x}+{y}")
        
        main_frame = tb.Frame(dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        tb.Label(main_frame, text="TRA CỨU THUỐC TRONG DANH MỤC", 
                font=('Segoe UI', 14, 'bold'), bootstyle='primary').pack(pady=(0, 15))
        
        # Search frame
        search_frame = tb.Frame(main_frame)
        search_frame.pack(fill='x', pady=(0, 10))
        
        tb.Label(search_frame, text="Tên thuốc:").pack(side='left', padx=(0, 10))
        search_entry = tb.Entry(search_frame, width=40)
        search_entry.pack(side='left', padx=(0, 10))
        search_entry.focus_set()
        
        def search_medicines():
            try:
                query = search_entry.get().strip()
                if not query:
                    messagebox.showwarning('Cảnh báo', 'Nhập tên thuốc cần tìm')
                    return
                
                results = self.medicine_catalog.search_medicine(query)
                display_results(results)
                
            except Exception as e:
                messagebox.showerror('Lỗi', str(e))
        
        tb.Button(search_frame, text="🔍 Tìm kiếm", bootstyle='success',
                  command=search_medicines).pack(side='left')
        
        # Results frame
        results_frame = tb.Labelframe(main_frame, text="Kết quả tìm kiếm", bootstyle='light')
        results_frame.pack(fill='both', expand=True)
        
        # Results tree
        cols = ('name', 'reg_number', 'manufacturer', 'active_ingredient', 'dosage_form')
        results_tree = tb.Treeview(results_frame, columns=cols, show='headings', height=15)
        
        for c, w, t, anchor in [
            ('name', 200, 'Tên thuốc', 'w'),
            ('reg_number', 120, 'Số đăng ký', 'center'),
            ('manufacturer', 150, 'Nhà SX', 'w'),
            ('active_ingredient', 150, 'Hoạt chất', 'w'),
            ('dosage_form', 100, 'Dạng bào chế', 'w')
        ]:
            results_tree.heading(c, text=t)
            results_tree.column(c, width=w, anchor=anchor)
        
        results_tree.tag_configure('odd', background='#f6f8fa')
        results_tree.pack(fill='both', expand=True, padx=8, pady=8)
        
        def display_results(results):
            # Clear tree
            for item in results_tree.get_children():
                results_tree.delete(item)
            
            for idx, result in enumerate(results):
                results_tree.insert('', 'end', values=(
                    result['name'],
                    result['registration_number'],
                    result['manufacturer'],
                    result['active_ingredient'],
                    result['dosage_form']
                ), tags=('odd',) if idx % 2 else ())
        
        def select_medicine():
            selection = results_tree.selection()
            if not selection:
                messagebox.showwarning('Cảnh báo', 'Chọn thuốc từ danh sách')
                return
            
            item = results_tree.item(selection[0])
            medicine_name = item['values'][0]
            reg_number = item['values'][1]
            
            # Điền vào form sản phẩm
            self.p_name.delete(0, tk.END)
            self.p_name.insert(0, medicine_name)
            self.p_type.set('medicine')
            self.on_product_type_change()
            self.p_reg_number.delete(0, tk.END)
            self.p_reg_number.insert(0, reg_number)
            
            dialog.destroy()
            self.nb.select(self.tab_products)
            self.p_base.focus_set()
        
        # Buttons
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        tb.Button(btn_frame, text="✅ Chọn thuốc này", bootstyle='success',
                  command=select_medicine).pack(side='left', padx=(0, 10))
        tb.Button(btn_frame, text="❌ Đóng", bootstyle='secondary',
                  command=dialog.destroy).pack(side='left')
        
        # Bind Enter key
        search_entry.bind('<Return>', lambda e: search_medicines())

    def show_catalog_info(self):
        """Hiển thị thông tin danh mục"""
        info = self.medicine_catalog.get_catalog_info()
        
        if not info['loaded']:
            messagebox.showinfo('Thông tin danh mục', 'Chưa load danh mục thuốc')
            return
        
        info_text = f"""Thông tin danh mục thuốc:

📁 File: {info['file_path']}
📊 Tổng số bản ghi: {info['total_records']:,}
📋 Các cột dữ liệu:
"""
        
        for i, col in enumerate(info['columns'], 1):
            info_text += f"  {i}. {col}\n"
        
        messagebox.showinfo('Thông tin danh mục', info_text)

    def update_catalog_info(self):
        """Cập nhật thông tin danh mục hiển thị"""
        info = self.medicine_catalog.get_catalog_info()
        
        if info['loaded']:
            file_name = os.path.basename(info['file_path'])
            self.catalog_info_label.config(
                text=f"📁 {file_name} - {info['total_records']:,} bản ghi",
                bootstyle='success'
            )
        else:
            self.catalog_info_label.config(
                text='Chưa load danh mục thuốc',
                bootstyle='secondary'
            )

    def scan_and_add(self):
        ok = self.fill_product_by_barcode(only_select=True)  # sửa hàm dưới để trả bool
        if ok:
            self.ent_qty_pos.delete(0, tk.END)
            self.ent_qty_pos.insert(0, '1')
            self.add_to_cart()
            self.ent_barcode.delete(0, tk.END)
        # luôn trả focus về ô barcode để quét tiếp
        self.after(50, lambda: self.ent_barcode.focus_set())
    
    def open_barcode_scanner(self):
        """Mở barcode scanner"""
        if not BARCODE_AVAILABLE:
            self.show_barcode_install_info()
            return
            
        try:
            # Tạo callback để xử lý kết quả quét
            def on_barcode_scanned(barcode_data):
                # Điền barcode vào ô input
                self.ent_barcode.delete(0, tk.END)
                self.ent_barcode.insert(0, barcode_data)
                
                # Tự động thêm vào giỏ hàng
                self.after(100, self.scan_and_add)
                
            # Tạo và mở scanner
            self.barcode_scanner = BarcodeScanner(self, callback=on_barcode_scanned)
            self.barcode_scanner.start_scan()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở barcode scanner: {e}")
    
    def show_barcode_install_info(self):
        """Hiển thị thông tin cài đặt thư viện barcode"""
        info = """
📷 Tính năng quét barcode cần cài đặt thêm thư viện:

pip install opencv-python pyzbar Pillow

Sau khi cài đặt, khởi động lại phần mềm để sử dụng tính năng quét barcode bằng camera.

Hiện tại bạn vẫn có thể:
• Nhập barcode thủ công
• Tìm sản phẩm theo tên
        """
        messagebox.showinfo("Cài đặt thư viện barcode", info)
    
    def scan_barcode_for_product(self):
        """Quét barcode cho sản phẩm mới"""
        if not BARCODE_AVAILABLE:
            self.show_barcode_install_info()
            return
            
        try:
            # Tạo callback để xử lý kết quả quét
            def on_barcode_scanned(barcode_data):
                # Điền barcode vào ô input
                self.p_barcode.delete(0, tk.END)
                self.p_barcode.insert(0, barcode_data)
                
                # Chuyển focus sang ô tên sản phẩm
                self.p_name.focus_set()
                
            # Tạo và mở scanner
            self.barcode_scanner = BarcodeScanner(self, callback=on_barcode_scanned)
            self.barcode_scanner.start_scan()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở barcode scanner: {e}")

    # -------- Purchase --------
    def build_purchase_tab(self):
        frm = self.tab_purchase

        # Header với title đẹp
        header_frame = tb.Frame(frm)
        header_frame.pack(fill='x', padx=8, pady=(8,4))
        
        title_label = tb.Label(header_frame, text='📦 Nhập hàng vào kho', 
                              font=('Segoe UI', 14, 'bold'), bootstyle='primary')
        title_label.pack(anchor='w')
        
        subtitle_label = tb.Label(header_frame, text='Nhập thông tin sản phẩm và batch để thêm vào kho', 
                                 font=('Segoe UI', 9), bootstyle='secondary')
        subtitle_label.pack(anchor='w')

        # Khung nhập liệu 2–3 hàng, co giãn theo chiều ngang
        box = tb.Labelframe(frm, text='📝 Nhập hàng & Giá bán (đơn vị cơ sở)', bootstyle='light')
        box.pack(fill='x', padx=8, pady=8)

        # Cho các cột có thể giãn đều khi thay đổi kích thước cửa sổ
        for i in range(12):
            box.grid_columnconfigure(i, weight=1)

        # ── Hàng 0: Tìm kiếm + Combobox chọn sản phẩm
        tb.Label(box, text='Tìm sản phẩm:').grid(row=0, column=0, sticky='w', padx=6, pady=6)
        self.search_purchase = tb.Entry(box)
        self.search_purchase.grid(row=0, column=1, columnspan=4, sticky='ew', padx=6, pady=6)
        self.search_purchase.bind('<KeyRelease>', lambda e: self.filter_product_list())
        self.search_purchase.bind('<Down>', lambda e: self.open_combo(self.cmb_prod)) 

        tb.Label(box, text='Chọn:').grid(row=0, column=5, sticky='e', padx=6, pady=6)
        self.cmb_prod = tb.Combobox(box, state='readonly')
        self.cmb_prod.grid(row=0, column=6, columnspan=5, sticky='ew', padx=6, pady=6)
        self.cmb_prod.bind('<<ComboboxSelected>>', lambda e: self.update_purchase_unit_and_price())
        self.cmb_prod.bind('<Escape>', lambda e: self.search_purchase.focus_set())  # ESC quay lại ô tìm
        self.cmb_prod.bind('<Return>', lambda e: self.ent_qty.focus_set())

        # ── Hàng 1: Đơn vị, Số lượng, Số lô, HSD
        tb.Label(box, text='Đơn vị (base):').grid(row=1, column=0, sticky='w', padx=6, pady=6)
        self.lbl_unit_purchase = tb.Label(box, text='-')
        self.lbl_unit_purchase.grid(row=1, column=1, sticky='w', padx=6, pady=6)

        tb.Label(box, text='Số lượng:').grid(row=1, column=2, sticky='e', padx=6, pady=6)
        self.ent_qty = tb.Entry(box, width=10)
        self.ent_qty.insert(0, '1')
        self.ent_qty.grid(row=1, column=3, sticky='w', padx=6, pady=6)
        self._numberize(self.ent_qty)

        tb.Label(box, text='Số lô:').grid(row=1, column=4, sticky='e', padx=6, pady=6)
        self.ent_lot = tb.Entry(box, width=14)
        self.ent_lot.insert(0, 'LOT001')
        self.ent_lot.grid(row=1, column=5, sticky='w', padx=6, pady=6)

        tb.Label(box, text='HSD (YYYY-MM-DD):').grid(row=1, column=6, sticky='e', padx=6, pady=6)
        self.ent_exp = DateEntry(
            box,
            dateformat="%Y-%m-%d",
            firstweekday=0,     # Monday
            bootstyle='info'
        )
        self.ent_exp.grid(row=1, column=7, sticky='w', padx=6, pady=6)

        # ── Hàng 2: Đơn giá nhập, Giá bán (base), Nút Nhập
        tb.Label(box, text='Đơn giá nhập:').grid(row=2, column=0, sticky='e', padx=6, pady=(6,8))
        self.ent_cost = tb.Entry(box, width=12)
        self.ent_cost.insert(0, '0')
        self.ent_cost.grid(row=2, column=1, sticky='w', padx=6, pady=(6,8))
        self._numberize(self.ent_cost)

        tb.Label(box, text='Giá bán (base):').grid(row=2, column=2, sticky='e', padx=6, pady=(6,8))
        self.ent_sell_price = tb.Entry(box, width=12)
        self.ent_sell_price.insert(0, '0')
        self.ent_sell_price.grid(row=2, column=3, sticky='w', padx=6, pady=(6,8))
        self._numberize(self.ent_sell_price)

        tb.Button(box, text='Nhập', bootstyle='success', command=self.handle_purchase)\
          .grid(row=2, column=10, columnspan=2, sticky='e', padx=6, pady=(6,8))

        # ── Bảng tồn theo lô ngay bên dưới
        cols = ('product','productName','batch','lot','exp','qty','cost','value')
        self.tree_stock = tb.Treeview(frm, columns=cols, show='headings')
        for c, w, t, anchor in [
            ('product',70,'PID','center'),('productName',300,'Tên thuốc','w'),('batch',70,'Batch','center'),
            ('lot',130,'Lot','w'),('exp',100,'HSD','center'),('qty',120,'SL (base)','e'),
            ('cost',130,'Giá nhập/base','e'), ('value',140,'Giá trị tồn','e')
        ]:
            self.tree_stock.heading(c, text=t, command=(lambda col=c: self.sort_tree(self.tree_stock, col)))
            self.tree_stock.column(c, width=w, anchor=anchor)
        self.tree_stock.tag_configure('odd', background='#f6f8fa')
        self.tree_stock.pack(fill='both', expand=True, padx=8, pady=8)

    def update_purchase_unit_and_price(self):
        sel = self.cmb_prod.get()
        if not sel: self.lbl_unit_purchase.config(text='-'); return
        pid = int(sel.split(' — ')[0])
        du = self.db.default_unit_of(pid) or '-'
        self.lbl_unit_purchase.config(text=du)
        # điền giá bán hiện tại
        price = self.db.unit_price(pid, du)
        self.ent_sell_price.delete(0, tk.END); self.ent_sell_price.insert(0, f'{price:g}')

    def filter_product_list(self):  # bỏ tham số auto_open
        kw = (self.search_purchase.get() or '').strip().lower()
        opts = [f"{p['id']} — {p['name']}" for p in self._products if kw in p['name'].lower()]
        self.cmb_prod['values'] = opts
        if opts:
            self.cmb_prod.current(0)
            self.update_purchase_unit_and_price()

    def handle_purchase(self):
        sel = self.cmb_prod.get()
        if not sel: messagebox.showerror('Lỗi','Chọn sản phẩm'); return
        pid = int(sel.split(' — ')[0])

        try: qty = float(self.ent_qty.get())
        except: qty = 0
        if qty <= 0: messagebox.showerror('Lỗi','Số lượng > 0'); return

        unit = self.db.default_unit_of(pid) or 'vien'
        lot = self.ent_lot.get().strip(); exp = (self.ent_exp.entry.get() or '').strip()
        try: dt.datetime.strptime(exp, '%Y-%m-%d')
        except: messagebox.showerror('Lỗi','Ngày HSD dạng YYYY-MM-DD'); return

        try: cost = float((self.ent_cost.get() or '0').replace(',', ''))
        except: messagebox.showerror('Lỗi','Đơn giá nhập không hợp lệ'); return
        try: sell_price = float((self.ent_sell_price.get() or '0').replace(',', ''))
        except: messagebox.showerror('Lỗi','Giá bán không hợp lệ'); return

        try:
            # nhập kho
            self.db.add_purchase([{ 'productId': pid, 'unitCode': unit, 'qty': qty,
                                    'lotNo': lot, 'expiryDate': exp, 'cost': cost }])
            # cập nhật giá bán base
            self.db.ex("UPDATE product_units SET price=? WHERE productId=? AND unitCode=?", (sell_price, pid, unit))
            self.toast('Đã nhập hàng & cập nhật giá bán'); self.refresh_stock()
        except Exception as e: messagebox.showerror('Lỗi', str(e))

    # -------- POS --------
    def build_pos_tab(self):
        frm = self.tab_pos

        # Header với title đẹp
        header_frame = tb.Frame(frm)
        header_frame.pack(fill='x', padx=8, pady=(8,4))
        
        title_label = tb.Label(header_frame, text='🧾 Bán hàng POS', 
                              font=('Segoe UI', 14, 'bold'), bootstyle='warning')
        title_label.pack(anchor='w')
        
        subtitle_label = tb.Label(header_frame, text='Quét barcode hoặc tìm sản phẩm để bán', 
                                 font=('Segoe UI', 9), bootstyle='secondary')
        subtitle_label.pack(anchor='w')

        # --- Hàng điều khiển trên cùng
        top = tb.Frame(frm); top.pack(fill='x', padx=8, pady=8)

        tb.Label(top, text='Barcode:').pack(side='left')
        self.ent_barcode = tb.Entry(top, width=18); self.ent_barcode.pack(side='left', padx=6)
        self.ent_barcode.bind('<Return>', lambda e: self.scan_and_add())
        self.ent_barcode.bind('<KP_Enter>', lambda e: self.scan_and_add())
        
        # Nút quét barcode bằng camera
        if BARCODE_AVAILABLE:
            tb.Button(top, text='📷 Quét', command=self.open_barcode_scanner, 
                     bootstyle='info', width=8).pack(side='left', padx=6)
        else:
            tb.Button(top, text='📷 Quét', command=self.show_barcode_install_info, 
                     bootstyle='secondary', width=8).pack(side='left', padx=6)

        tb.Label(top, text='Tìm tên:').pack(side='left')
        self.search_pos = tb.Entry(top, width=30); self.search_pos.pack(side='left', padx=6)

        tb.Label(top, text='Chọn:').pack(side='left')
        self.cmb_prod_pos = tb.Combobox(top, state='readonly', width=50); self.cmb_prod_pos.pack(side='left', padx=6)

        tb.Label(top, text='SL:').pack(side='left')
        self.ent_qty_pos = tb.Entry(top, width=8); self.ent_qty_pos.insert(0, '1'); self.ent_qty_pos.pack(side='left', padx=6)
        self._numberize(self.ent_qty_pos)

        # --- Bind sau khi đã tạo ĐỦ widget
        self.search_pos.bind('<KeyRelease>', lambda e: self.filter_product_list_pos())
        # Bấm mũi tên xuống để mở dropdown và chuyển focus sang combobox
        self.search_pos.bind('<Down>', lambda e: (self.cmb_prod_pos.focus_set(),
                                                  self.cmb_prod_pos.event_generate('<Alt-Down>')))

        self.cmb_prod_pos.bind('<<ComboboxSelected>>', lambda e: self.update_pos_price_and_unit())
        self.cmb_prod_pos.bind('<Escape>', lambda e: self.search_pos.focus_set())   # quay lại ô tìm
        self.cmb_prod_pos.bind('<Return>', lambda e: self.ent_qty_pos.focus_set())  # sang ô SL

        # --- Nút tác vụ
        btns = tb.Frame(frm); btns.pack(fill='x', padx=8, pady=(0, 8))
        tb.Button(btns, text='+ Thêm vào giỏ', bootstyle='secondary', command=self.add_to_cart).pack(side='left', padx=4)
        tb.Button(btns, text='Xóa dòng', bootstyle='warning', command=self.remove_selected_cart_item).pack(side='left', padx=4)
        tb.Button(btns, text='Xóa giỏ', bootstyle='danger', command=self.clear_cart).pack(side='left', padx=4)
        tb.Button(btns, text='Thanh toán', bootstyle='success', command=self.checkout_cart).pack(side='left', padx=8)
        tb.Button(btns, text='In hoá đơn', bootstyle='info', command=self.print_invoice).pack(side='left', padx=8)

        # --- Info tổng
        info = tb.Labelframe(frm, text='Tổng kết', bootstyle='light'); info.pack(fill='x', padx=8, pady=(0, 8))
        self.lbl_unit_pos = tb.Label(info, text='Đơn vị: -'); self.lbl_unit_pos.pack(side='left', padx=(8, 12))
        self.lbl_price = tb.Label(info, text='Đơn giá: 0', font=('Segoe UI', 12)); self.lbl_price.pack(side='left', padx=(0, 12))
        self.lbl_total = tb.Label(info, text='Tổng tiền: 0', font=('Segoe UI', 15, 'bold')); self.lbl_total.pack(side='left', padx=12)

        # --- Bảng giỏ
        cols = ('productId', 'productName', 'unitCode', 'qty', 'price', 'amount')
        self.tree_cart = tb.Treeview(frm, columns=cols, show='headings', height=10)
        for c, w, t, anchor in [
            ('productId', 70, 'PID', 'center'),
            ('productName', 320, 'Tên hàng', 'w'),
            ('unitCode', 80, 'ĐV', 'center'),
            ('qty', 80, 'SL', 'e'),
            ('price', 120, 'Đơn giá', 'e'),
            ('amount', 120, 'Thành tiền', 'e')
        ]:
            self.tree_cart.heading(c, text=t, command=(lambda col=c: self.sort_tree(self.tree_cart, col)))
            self.tree_cart.column(c, width=w, anchor=anchor)
        self.tree_cart.tag_configure('odd', background='#f6f8fa')
        self.tree_cart.pack(fill='both', expand=True, padx=8, pady=8)

        self.ent_qty_pos.bind('<Return>', lambda e: self.add_to_cart())

    def update_pos_price_and_unit(self):
        sel = self.cmb_prod_pos.get()
        if not sel:
            self.lbl_unit_pos.config(text='Đơn vị: -'); self.lbl_price.config(text='Đơn giá: 0'); return
        pid = int(sel.split(' — ')[0])
        du = self.db.default_unit_of(pid) or '-'
        price = self.db.unit_price(pid, du)
        self.lbl_unit_pos.config(text=f'Đơn vị: {du}')
        self.lbl_price.config(text=f'Đơn giá: {price:,.0f}')

    def fill_product_by_barcode(self, only_select=False):
        bc = self.ent_barcode.get().strip()
        if not bc:
            return False
        row = self.db.q("SELECT id, name FROM products WHERE barcode=?", (bc,))
        if not row:
            if not only_select:
                messagebox.showwarning('Không tìm thấy', 'Barcode không khớp sản phẩm nào')
            return False
        target = f"{row[0]['id']} — {row[0]['name']}"
        if target not in self.cmb_prod_pos['values']:
            self.cmb_prod_pos['values'] = list(self.cmb_prod_pos['values']) + [target]
        self.cmb_prod_pos.set(target)
        self.update_pos_price_and_unit()
        return True


    def filter_product_list_pos(self):
        kw = (self.search_pos.get() or '').strip().lower()
        opts = [f"{p['id']} — {p['name']}" for p in self._products if kw in p['name'].lower()]
        self.cmb_prod_pos['values'] = opts
        if opts:
            self.cmb_prod_pos.current(0)
            self.update_pos_price_and_unit()


    # -------- Cart --------
    def add_to_cart(self):
        sel = self.cmb_prod_pos.get()
        if not sel: messagebox.showerror('Lỗi', 'Chọn sản phẩm'); return
        pid = int(sel.split(' — ')[0])
        unit = self.db.default_unit_of(pid) or 'vien'
        try: qty = float(self.ent_qty_pos.get())
        except: qty = 0
        if qty <= 0: messagebox.showerror('Lỗi', 'Số lượng > 0'); return
        name = self.name_by_id(pid)
        price = self.db.unit_price(pid, unit)

        merged = False
        for it in self.cart:
            if it['productId']==pid and it['unitCode']==unit and abs(it['price']-price) < 1e-6:
                it['qty'] = round(it['qty']+qty, 4); merged=True; break
        if not merged:
            self.cart.append({'productId': pid, 'productName': name, 'unitCode': unit, 'qty': qty, 'price': price})

        self.refresh_cart_view()
        self.ent_qty_pos.delete(0, tk.END); self.ent_qty_pos.insert(0, '1'); self.ent_qty_pos.focus_set()

    def remove_selected_cart_item(self):
        sel = self.tree_cart.selection()
        if not sel: return
        idx = self.tree_cart.index(sel[0])
        if 0 <= idx < len(self.cart): self.cart.pop(idx); self.refresh_cart_view()

    def clear_cart(self):
        if self.cart and messagebox.askyesno('Xác nhận','Xóa toàn bộ giỏ hàng?'):
            self.cart = []; self.refresh_cart_view()

    def refresh_cart_view(self):
        for i in self.tree_cart.get_children(): self.tree_cart.delete(i)
        total = 0.0
        for idx, it in enumerate(self.cart):
            amount = round(it['qty']*it['price'], 2); total += amount
            self.tree_cart.insert('', 'end',
                values=(it['productId'], it['productName'], it['unitCode'], it['qty'], f"{it['price']:,.0f}", f"{amount:,.0f}"),
                tags=('odd',) if idx%2 else ())
        self.lbl_total.config(text=f'Tổng tiền: {total:,.0f}')

    def checkout_cart(self):
        if not self.cart: messagebox.showwarning('Chưa có dữ liệu','Giỏ hàng trống'); return
        total = round(sum(it['qty']*it['price'] for it in self.cart), 2)
        paid_str = simpledialog.askstring('Thanh toán', f'Tổng cộng: {total:,.0f}\nKhách đưa (đ):', initialvalue=f'{int(total):d}')
        if paid_str is None: return
        try: paid = float(paid_str.replace(',', '').strip())
        except: messagebox.showerror('Lỗi','Số tiền không hợp lệ'); return
        try:
            sale_id, finalized, total_, change_ = self.db.record_sale(self.cart, paid, '')
            self.last_sale_items = finalized; self.cart = []; self.refresh_cart_view(); self.refresh_stock()
            messagebox.showinfo('Thành công', f'Đã thanh toán hóa đơn #{sale_id}\nTiền thối: {change_:,.0f} đ')
        except Exception as e: messagebox.showerror('Lỗi', str(e))

    def name_by_id(self, pid):
        for p in self._products:
            if p['id']==pid: return p['name']
        return f'#{pid}'

    def print_invoice(self):
        if not self.last_sale_items:
            messagebox.showwarning('Chưa có dữ liệu','Hãy bán hàng trước khi in'); return
        now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total = sum(i['qty']*i['price'] for i in self.last_sale_items)
        rows_html = ''.join([f"<tr><td>{i['productName']}</td><td style='text-align:center'>{i['unitCode']}</td>"
                             f"<td style='text-align:right'>{i['qty']}</td><td style='text-align:right'>{i['price']:,.0f}</td>"
                             f"<td style='text-align:right'>{i['qty']*i['price']:,.0f}</td></tr>" for i in self.last_sale_items])
        html = f"""
        <html><head><meta charset='utf-8'><style>
        body{{font-family:Arial;}} table{{width:100%;border-collapse:collapse}}
        td,th{{border:1px solid #999;padding:6px;font-size:12px}}
        h2{{margin:0 0 6px 0}} .right{{text-align:right}}
        @media print{{ @page{{ size: A5; margin:10mm }} }}
        </style></head><body>
        <h2>HÓA ĐƠN BÁN HÀNG</h2>
        <div>Thời gian: {now}</div>
        <table><thead><tr><th>Tên hàng</th><th>ĐV</th><th>SL</th><th>Đơn giá</th><th>Thành tiền</th></tr></thead>
        <tbody>{rows_html}</tbody>
        <tfoot><tr><td colspan='4' class='right'><b>Tổng cộng</b></td><td class='right'><b>{total:,.0f}</b></td></tr></tfoot>
        </table>
        <p>Cảm ơn quý khách!</p>
        <script>window.onload=()=>window.print()</script>
        </body></html>"""
        tmp = os.path.join(tempfile.gettempdir(), f"invoice_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(tmp, 'w', encoding='utf-8') as f: f.write(html)
        webbrowser.open('file://' + tmp)

    # -------- Stock --------
    def build_stock_tab(self):
        frm = self.tab_stock
        cols = ('product','productName','batch','lot','exp','qty')
        self.tree_stock2 = tb.Treeview(frm, columns=cols, show='headings')
        for c, w, t, anchor in [
            ('product',70,'PID','center'),('productName',300,'Tên thuốc','w'),('batch',70,'Batch','center'),
            ('lot',130,'Lot','w'),('exp',100,'HSD','center'),('qty',120,'SL (base)','e')
        ]:
            self.tree_stock2.heading(c, text=t, command=(lambda col=c: self.sort_tree(self.tree_stock2, col)))
            self.tree_stock2.column(c, width=w, anchor=anchor)
        self.tree_stock2.tag_configure('odd', background='#f6f8fa')
        self.tree_stock2.pack(fill='both', expand=True, padx=8, pady=8)

    # -------- Alerts --------
    def build_alerts_tab(self):
        frm = self.tab_alerts
        top = tb.Frame(frm); top.pack(fill='x', padx=8, pady=8)
        tb.Label(top, text='Cảnh báo trong (ngày):').pack(side='left')
        self.ent_warn_days = tb.Entry(top, width=6); self.ent_warn_days.insert(0, '90'); self.ent_warn_days.pack(side='left', padx=6)
        self._numberize(self.ent_warn_days)
        tb.Button(top, text='Làm mới', bootstyle='secondary', command=self.refresh_alerts).pack(side='left', padx=8)

        cols = ('product','productName','batch','lot','exp','qty')
        self.tree_alerts = tb.Treeview(frm, columns=cols, show='headings')
        for c, w, t, anchor in [
            ('product',70,'PID','center'),('productName',300,'Tên thuốc','w'),('batch',70,'Batch','center'),
            ('lot',130,'Lot','w'),('exp',100,'HSD','center'),('qty',120,'SL (base)','e')
        ]:
            self.tree_alerts.heading(c, text=t, command=(lambda col=c: self.sort_tree(self.tree_alerts, col)))
            self.tree_alerts.column(c, width=w, anchor=anchor)
        self.tree_alerts.tag_configure('odd', background='#f6f8fa')
        self.tree_alerts.pack(fill='both', expand=True, padx=8, pady=8)

    # -------- Report --------
    def build_report_tab(self):
        frm = self.tab_report

        # Thanh điều kiện: từ ngày / đến ngày
        top = tb.Frame(frm); top.pack(fill='x', padx=8, pady=8)

        tb.Label(top, text='Từ ngày:').pack(side='left', padx=(0,6))
        # DateEntry đã được bạn thêm trước đó; nếu chưa có, nhớ: from ttkbootstrap.widgets import DateEntry
        self.de_from = DateEntry(top, dateformat="%Y-%m-%d", firstweekday=0, bootstyle='secondary')
        self.de_from.entry.delete(0, 'end')
        self.de_from.entry.insert(0, dt.date.today().replace(day=1).strftime("%Y-%m-%d"))  # đầu tháng
        self.de_from.pack(side='left', padx=(0,12))

        tb.Label(top, text='Đến ngày:').pack(side='left', padx=(0,6))
        self.de_to = DateEntry(top, dateformat="%Y-%m-%d", firstweekday=0, bootstyle='secondary')
        self.de_to.entry.delete(0, 'end')
        self.de_to.entry.insert(0, dt.datetime.now().strftime("%Y-%m-%d"))      # hôm nay
        self.de_to.pack(side='left', padx=(0,12))

        tb.Button(top, text='Làm mới', bootstyle='primary', command=self.refresh_report).pack(side='left', padx=6)
        tb.Button(top, text='Xuất CSV…', bootstyle='info', command=self.export_report_csv).pack(side='left', padx=6)

        # Bảng Xuất–Nhập–Tồn
        cols = ('product','productName','opening','inbound','outbound','closing')
        self.tree_report = tb.Treeview(frm, columns=cols, show='headings')
        for c, w, t, anchor in [
            ('product',80,'PID','center'),
            ('productName',500,'Tên thuốc','w'),
            ('opening',120,'Tồn đầu kỳ','e'),
            ('inbound',120,'Nhập','e'),
            ('outbound',120,'Xuất','e'),
            ('closing',120,'Tồn cuối kỳ','e'),
        ]:
            self.tree_report.heading(c, text=t, command=(lambda col=c: self.sort_tree(self.tree_report, col)))
            self.tree_report.column(c, width=w, anchor=anchor)

        self.tree_report.tag_configure('odd', background='#f6f8fa')
        self.tree_report.tag_configure('total', background='#e8f5e9')  # dòng tổng
        self.tree_report.pack(fill='both', expand=True, padx=8, pady=8)

    # -------- Backup --------
    def build_backup_tab(self):
        frm = self.tab_backup
        
        # Khung tạo backup
        backup_frame = tb.Labelframe(frm, text='Tạo Backup', bootstyle='light')
        backup_frame.pack(fill='x', padx=8, pady=8)
        
        btn_frame = tb.Frame(backup_frame)
        btn_frame.pack(fill='x', padx=8, pady=8)
        
        tb.Button(btn_frame, text='💾 Tạo Backup Ngay', bootstyle='success',
                  command=self.create_manual_backup).pack(side='left', padx=4)
        tb.Button(btn_frame, text='📤 Export Dữ Liệu', bootstyle='info',
                  command=self.export_data).pack(side='left', padx=4)
        tb.Button(btn_frame, text='📥 Import Dữ Liệu', bootstyle='warning',
                  command=self.import_data).pack(side='left', padx=4)
        
        # Khung khôi phục backup
        restore_frame = tb.Labelframe(frm, text='Khôi Phục Backup', bootstyle='light')
        restore_frame.pack(fill='x', padx=8, pady=8)
        
        tb.Label(restore_frame, text='Chọn backup để khôi phục:').pack(anchor='w', padx=8, pady=(8,4))
        
        # Bảng danh sách backup
        cols = ('file', 'created', 'size', 'version')
        self.tree_backups = tb.Treeview(restore_frame, columns=cols, show='headings', height=8)
        for c, w, t, anchor in [
            ('file', 300, 'Tên File', 'w'),
            ('created', 150, 'Ngày Tạo', 'center'),
            ('size', 100, 'Kích Thước', 'e'),
            ('version', 80, 'Phiên Bản', 'center')
        ]:
            self.tree_backups.heading(c, text=t, command=(lambda col=c: self.sort_tree(self.tree_backups, col)))
            self.tree_backups.column(c, width=w, anchor=anchor)
        self.tree_backups.tag_configure('odd', background='#f6f8fa')
        self.tree_backups.pack(fill='x', padx=8, pady=8)
        
        # Nút khôi phục
        restore_btn_frame = tb.Frame(restore_frame)
        restore_btn_frame.pack(fill='x', padx=8, pady=(0,8))
        
        tb.Button(restore_btn_frame, text='🔄 Khôi Phục Backup', bootstyle='danger',
                  command=self.restore_selected_backup).pack(side='left', padx=4)
        tb.Button(restore_btn_frame, text='🗑️ Xóa Backup', bootstyle='outline-danger',
                  command=self.delete_selected_backup).pack(side='left', padx=4)
        tb.Button(restore_btn_frame, text='🔄 Làm Mới', bootstyle='secondary',
                  command=self.refresh_backup_list).pack(side='left', padx=4)
        
        # Thông tin auto backup
        info_frame = tb.Labelframe(frm, text='Tự Động Backup', bootstyle='info')
        info_frame.pack(fill='x', padx=8, pady=8)
        
        info_text = tb.Text(info_frame, height=4, wrap='word')
        info_text.pack(fill='x', padx=8, pady=8)
        info_text.insert('1.0', 
            "• Tự động backup mỗi ngày lúc 2:00 AM\n"
            "• Giữ tối đa 30 file backup\n"
            "• Backup được lưu trong thư mục: " + BACKUP_DIR + "\n"
            "• Trước khi khôi phục, hệ thống sẽ tự động tạo backup hiện tại")
        info_text.config(state='disabled')
        
        # Load danh sách backup
        self.refresh_backup_list()

    def create_manual_backup(self):
        """Tạo backup thủ công"""
        try:
            backup_path = self.backup_manager.create_backup("manual")
            self.toast(f'Đã tạo backup: {os.path.basename(backup_path)}')
            self.refresh_backup_list()
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def export_data(self):
        """Export dữ liệu ra file JSON"""
        try:
            path = filedialog.asksaveasfilename(
                defaultextension='.json',
                filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
                initialfile=f'export_data_{dt.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            if path:
                self.backup_manager.export_data(path)
                self.toast('Đã export dữ liệu thành công')
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def import_data(self):
        """Import dữ liệu từ file JSON"""
        try:
            path = filedialog.askopenfilename(
                filetypes=[('JSON files', '*.json'), ('All files', '*.*')]
            )
            if path:
                if messagebox.askyesno('Xác nhận', 
                    'Import sẽ thay thế toàn bộ dữ liệu hiện tại!\n'
                    'Hệ thống sẽ tự động tạo backup trước khi import.\n'
                    'Bạn có chắc chắn muốn tiếp tục?'):
                    
                    self.backup_manager.import_data(path)
                    self.toast('Đã import dữ liệu thành công')
                    # Refresh tất cả dữ liệu
                    self.refresh_products()
                    self.refresh_stock()
                    self.refresh_alerts()
                    self.refresh_report()
                    self.refresh_backup_list()
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def restore_selected_backup(self):
        """Khôi phục backup được chọn"""
        selection = self.tree_backups.selection()
        if not selection:
            messagebox.showwarning('Cảnh báo', 'Chọn backup để khôi phục')
            return
        
        item = self.tree_backups.item(selection[0])
        backup_file = item['values'][0]
        backup_path = os.path.join(BACKUP_DIR, backup_file)
        
        if messagebox.askyesno('Xác nhận', 
            f'Khôi phục backup: {backup_file}\n'
            'Hệ thống sẽ tự động tạo backup hiện tại trước khi khôi phục.\n'
            'Bạn có chắc chắn muốn tiếp tục?'):
            
            try:
                self.backup_manager.restore_backup(backup_path)
                self.toast('Đã khôi phục backup thành công')
                # Refresh tất cả dữ liệu
                self.refresh_products()
                self.refresh_stock()
                self.refresh_alerts()
                self.refresh_report()
                self.refresh_backup_list()
            except Exception as e:
                messagebox.showerror('Lỗi', str(e))

    def delete_selected_backup(self):
        """Xóa backup được chọn"""
        selection = self.tree_backups.selection()
        if not selection:
            messagebox.showwarning('Cảnh báo', 'Chọn backup để xóa')
            return
        
        item = self.tree_backups.item(selection[0])
        backup_file = item['values'][0]
        
        if messagebox.askyesno('Xác nhận', f'Xóa backup: {backup_file}?'):
            try:
                backup_path = os.path.join(BACKUP_DIR, backup_file)
                os.remove(backup_path)
                metadata_path = backup_path.replace('.db', '.json')
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                self.toast('Đã xóa backup')
                self.refresh_backup_list()
            except Exception as e:
                messagebox.showerror('Lỗi', str(e))

    def refresh_backup_list(self):
        """Làm mới danh sách backup"""
        try:
            # Clear tree
            for item in self.tree_backups.get_children():
                self.tree_backups.delete(item)
            
            backups = self.backup_manager.list_backups()
            for idx, backup in enumerate(backups):
                size_mb = backup['size'] / (1024 * 1024)
                created_str = backup['created'].strftime('%Y-%m-%d %H:%M')
                version = backup.get('version', 'N/A')
                
                self.tree_backups.insert('', 'end',
                    values=(backup['file'], created_str, f'{size_mb:.1f} MB', version),
                    tags=('odd',) if idx % 2 else ())
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể load danh sách backup: {str(e)}')

    # -------- Advanced Reports --------
    def build_advanced_reports_tab(self):
        frm = self.tab_advanced_reports
        
        # Khung điều khiển
        control_frame = tb.Labelframe(frm, text='Điều kiện báo cáo', bootstyle='light')
        control_frame.pack(fill='x', padx=8, pady=8)
        
        # Hàng 1: Ngày tháng
        date_frame = tb.Frame(control_frame)
        date_frame.pack(fill='x', padx=8, pady=8)
        
        tb.Label(date_frame, text='Từ ngày:').pack(side='left', padx=(0,6))
        self.adv_de_from = DateEntry(date_frame, dateformat="%Y-%m-%d", firstweekday=0, bootstyle='secondary')
        self.adv_de_from.entry.delete(0, 'end')
        self.adv_de_from.entry.insert(0, dt.date.today().replace(day=1).strftime("%Y-%m-%d"))
        self.adv_de_from.pack(side='left', padx=(0,12))
        
        tb.Label(date_frame, text='Đến ngày:').pack(side='left', padx=(0,6))
        self.adv_de_to = DateEntry(date_frame, dateformat="%Y-%m-%d", firstweekday=0, bootstyle='secondary')
        self.adv_de_to.entry.delete(0, 'end')
        self.adv_de_to.entry.insert(0, dt.datetime.now().strftime("%Y-%m-%d"))
        self.adv_de_to.pack(side='left', padx=(0,12))
        
        # Hàng 2: Nút báo cáo
        btn_frame = tb.Frame(control_frame)
        btn_frame.pack(fill='x', padx=8, pady=(0,8))
        
        tb.Button(btn_frame, text='💰 Báo cáo doanh thu', bootstyle='success',
                  command=self.show_revenue_report).pack(side='left', padx=4)
        tb.Button(btn_frame, text='📊 Báo cáo lợi nhuận', bootstyle='info',
                  command=self.show_profit_report).pack(side='left', padx=4)
        tb.Button(btn_frame, text='🏆 Top sản phẩm', bootstyle='warning',
                  command=self.show_top_products_report).pack(side='left', padx=4)
        tb.Button(btn_frame, text='📈 Biểu đồ doanh thu', bootstyle='primary',
                  command=self.show_revenue_chart).pack(side='left', padx=4)
        
        # Hàng 3: Nút xuất báo cáo
        export_frame = tb.Frame(control_frame)
        export_frame.pack(fill='x', padx=8, pady=(0,8))
        
        tb.Label(export_frame, text='Xuất báo cáo:', font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(0,8))
        tb.Button(export_frame, text='📊 Excel', bootstyle='success',
                  command=self.export_current_report_excel).pack(side='left', padx=4)
        tb.Button(export_frame, text='📄 PDF', bootstyle='danger',
                  command=self.export_current_report_pdf).pack(side='left', padx=4)
        tb.Button(export_frame, text='📋 CSV', bootstyle='secondary',
                  command=self.export_current_report_csv).pack(side='left', padx=4)
        
        # Khung hiển thị báo cáo
        self.report_display_frame = tb.Frame(frm)
        self.report_display_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Tạo notebook cho các loại báo cáo
        self.adv_report_nb = tb.Notebook(self.report_display_frame)
        self.adv_report_nb.pack(fill='both', expand=True)
        
        # Tab tóm tắt
        self.adv_summary_tab = tb.Frame(self.adv_report_nb)
        self.adv_report_nb.add(self.adv_summary_tab, text='📋 Tóm tắt')
        
        # Tab báo cáo chi tiết
        self.adv_detail_tab = tb.Frame(self.adv_report_nb)
        self.adv_report_nb.add(self.adv_detail_tab, text='📊 Chi tiết')
        
        # Tab biểu đồ
        self.adv_chart_tab = tb.Frame(self.adv_report_nb)
        self.adv_report_nb.add(self.adv_chart_tab, text='📈 Biểu đồ')
        
        # Load tóm tắt ban đầu
        self.load_advanced_summary()

    def load_advanced_summary(self):
        """Load tóm tắt báo cáo nâng cao"""
        try:
            # Clear summary tab
            for widget in self.adv_summary_tab.winfo_children():
                widget.destroy()
            
            start_date = self.adv_de_from.entry.get().strip()
            end_date = self.adv_de_to.entry.get().strip()
            
            if not start_date or not end_date:
                return
            
            # Lấy dữ liệu tóm tắt
            summary_data = self.report_manager.get_daily_sales_summary(start_date, end_date)
            summary = summary_data['summary']
            
            # Tạo layout tóm tắt
            main_frame = tb.Frame(self.adv_summary_tab)
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Title
            title_label = tb.Label(main_frame, text="TÓM TẮT BÁO CÁO", 
                                  font=('Segoe UI', 16, 'bold'), bootstyle='primary')
            title_label.pack(pady=(0, 20))
            
            # KPI Cards
            kpi_frame = tb.Frame(main_frame)
            kpi_frame.pack(fill='x', pady=(0, 20))
            
            # Card 1: Tổng đơn hàng
            card1 = tb.Labelframe(kpi_frame, text='Tổng đơn hàng', bootstyle='info')
            card1.pack(side='left', fill='both', expand=True, padx=(0, 10))
            total_orders = summary.get('total_orders', 0) or 0
            tb.Label(card1, text=f"{total_orders:,}", 
                    font=('Segoe UI', 24, 'bold'), bootstyle='info').pack(pady=10)
            
            # Card 2: Tổng doanh thu
            card2 = tb.Labelframe(kpi_frame, text='Tổng doanh thu', bootstyle='success')
            card2.pack(side='left', fill='both', expand=True, padx=(0, 10))
            total_revenue = summary.get('total_revenue', 0) or 0
            tb.Label(card2, text=f"{total_revenue:,.0f} đ", 
                    font=('Segoe UI', 24, 'bold'), bootstyle='success').pack(pady=10)
            
            # Card 3: Giá trị đơn hàng TB
            card3 = tb.Labelframe(kpi_frame, text='Đơn hàng TB', bootstyle='warning')
            card3.pack(side='left', fill='both', expand=True, padx=(0, 10))
            avg_order = summary.get('avg_order_value', 0) or 0
            tb.Label(card3, text=f"{avg_order:,.0f} đ", 
                    font=('Segoe UI', 24, 'bold'), bootstyle='warning').pack(pady=10)
            
            # Card 4: Đơn hàng lớn nhất
            card4 = tb.Labelframe(kpi_frame, text='Đơn hàng lớn nhất', bootstyle='danger')
            card4.pack(side='left', fill='both', expand=True)
            max_order = summary.get('max_order', 0) or 0
            tb.Label(card4, text=f"{max_order:,.0f} đ", 
                    font=('Segoe UI', 24, 'bold'), bootstyle='danger').pack(pady=10)
            
            # Bảng doanh thu theo ngày
            daily_frame = tb.Labelframe(main_frame, text='Doanh thu theo ngày', bootstyle='light')
            daily_frame.pack(fill='both', expand=True)
            
            cols = ('date', 'orders', 'revenue')
            daily_tree = tb.Treeview(daily_frame, columns=cols, show='headings', height=8)
            for c, w, t, anchor in [
                ('date', 120, 'Ngày', 'center'),
                ('orders', 100, 'Số đơn', 'e'),
                ('revenue', 150, 'Doanh thu', 'e')
            ]:
                daily_tree.heading(c, text=t)
                daily_tree.column(c, width=w, anchor=anchor)
            
            daily_tree.tag_configure('odd', background='#f6f8fa')
            daily_tree.pack(fill='both', expand=True, padx=8, pady=8)
            
            # Load dữ liệu
            daily_data = summary_data.get('daily_data', [])
            for idx, row in enumerate(daily_data):
                orders = row.get('orders', 0) or 0
                revenue = row.get('revenue', 0) or 0
                daily_tree.insert('', 'end', values=(
                    row.get('sale_date', ''),
                    f"{orders:,}",
                    f"{revenue:,.0f} đ"
                ), tags=('odd',) if idx % 2 else ())
                
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể load tóm tắt: {str(e)}')

    def show_revenue_report(self):
        """Hiển thị báo cáo doanh thu"""
        try:
            start_date = self.adv_de_from.entry.get().strip()
            end_date = self.adv_de_to.entry.get().strip()
            
            if not start_date or not end_date:
                messagebox.showwarning('Thiếu thông tin', 'Vui lòng chọn đầy đủ ngày bắt đầu và kết thúc')
                return
            
            # Tạo dialog chọn loại báo cáo
            dialog = tb.Toplevel(self)
            dialog.title("Báo cáo doanh thu")
            dialog.geometry("300x200")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center dialog
            dialog.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() // 2) - (300 // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (200 // 2)
            dialog.geometry(f"300x200+{x}+{y}")
            
            main_frame = tb.Frame(dialog)
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            tb.Label(main_frame, text="Chọn loại báo cáo:", 
                    font=('Segoe UI', 12, 'bold')).pack(pady=(0, 15))
            
            group_var = tk.StringVar(value='day')
            tb.Radiobutton(main_frame, text="Theo ngày", variable=group_var, value='day').pack(anchor='w', pady=5)
            tb.Radiobutton(main_frame, text="Theo tháng", variable=group_var, value='month').pack(anchor='w', pady=5)
            tb.Radiobutton(main_frame, text="Theo năm", variable=group_var, value='year').pack(anchor='w', pady=5)
            
            def generate_report():
                try:
                    group_by = group_var.get()
                    data = self.report_manager.get_revenue_report(start_date, end_date, group_by)
                    self.display_revenue_report(data, group_by)
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror('Lỗi', str(e))
            
            btn_frame = tb.Frame(main_frame)
            btn_frame.pack(fill='x', pady=(20, 0))
            
            tb.Button(btn_frame, text="Tạo báo cáo", bootstyle='success',
                      command=generate_report).pack(side='left', padx=(0, 10))
            tb.Button(btn_frame, text="Hủy", bootstyle='secondary',
                      command=dialog.destroy).pack(side='left')
            
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def display_revenue_report(self, data, group_by):
        """Hiển thị báo cáo doanh thu"""
        try:
            # Clear detail tab
            for widget in self.adv_detail_tab.winfo_children():
                widget.destroy()
            
            main_frame = tb.Frame(self.adv_detail_tab)
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Title
            period_text = {'day': 'ngày', 'month': 'tháng', 'year': 'năm'}
            title = f"BÁO CÁO DOANH THU THEO {period_text[group_by].upper()}"
            tb.Label(main_frame, text=title, 
                    font=('Segoe UI', 14, 'bold'), bootstyle='primary').pack(pady=(0, 15))
            
            # Bảng dữ liệu
            cols = ('period', 'orders', 'revenue', 'paid', 'avg_order')
            tree = tb.Treeview(main_frame, columns=cols, show='headings', height=15)
            
            for c, w, t, anchor in [
                ('period', 120, 'Thời gian', 'center'),
                ('orders', 100, 'Số đơn', 'e'),
                ('revenue', 150, 'Doanh thu', 'e'),
                ('paid', 150, 'Đã thu', 'e'),
                ('avg_order', 150, 'Đơn TB', 'e')
            ]:
                tree.heading(c, text=t)
                tree.column(c, width=w, anchor=anchor)
            
            tree.tag_configure('odd', background='#f6f8fa')
            tree.tag_configure('total', background='#e8f5e9', font=('Segoe UI', 10, 'bold'))
            tree.pack(fill='both', expand=True)
            
            # Load dữ liệu
            total_orders = total_revenue = total_paid = 0
            for idx, row in enumerate(data):
                orders = row.get('total_orders', 0) or 0
                revenue = row.get('total_revenue', 0) or 0
                paid = row.get('total_paid', 0) or 0
                avg_order = row.get('avg_order_value', 0) or 0
                
                total_orders += orders
                total_revenue += revenue
                total_paid += paid
                
                tree.insert('', 'end', values=(
                    row.get('period', ''),
                    f"{orders:,}",
                    f"{revenue:,.0f} đ",
                    f"{paid:,.0f} đ",
                    f"{avg_order:,.0f} đ"
                ), tags=('odd',) if idx % 2 else ())
            
            # Dòng tổng
            if data:
                tree.insert('', 'end', values=(
                    'TỔNG',
                    f"{total_orders:,}",
                    f"{total_revenue:,.0f} đ",
                    f"{total_paid:,.0f} đ",
                    f"{total_revenue/total_orders:,.0f} đ" if total_orders > 0 else "0 đ"
                ), tags=('total',))
            
            # Chuyển sang tab chi tiết
            self.adv_report_nb.select(self.adv_detail_tab)
            
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def show_profit_report(self):
        """Hiển thị báo cáo lợi nhuận"""
        try:
            start_date = self.adv_de_from.entry.get().strip()
            end_date = self.adv_de_to.entry.get().strip()
            
            if not start_date or not end_date:
                messagebox.showwarning('Thiếu thông tin', 'Vui lòng chọn đầy đủ ngày bắt đầu và kết thúc')
                return
            
            data = self.report_manager.get_profit_report(start_date, end_date)
            self.display_profit_report(data)
            
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def display_profit_report(self, data):
        """Hiển thị báo cáo lợi nhuận"""
        try:
            # Clear detail tab
            for widget in self.adv_detail_tab.winfo_children():
                widget.destroy()
            
            main_frame = tb.Frame(self.adv_detail_tab)
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Title
            tb.Label(main_frame, text="BÁO CÁO LỢI NHUẬN", 
                    font=('Segoe UI', 14, 'bold'), bootstyle='primary').pack(pady=(0, 15))
            
            # Bảng dữ liệu
            cols = ('date', 'product', 'qty', 'sell_price', 'cost_price', 'revenue', 'cost', 'profit')
            tree = tb.Treeview(main_frame, columns=cols, show='headings', height=15)
            
            for c, w, t, anchor in [
                ('date', 100, 'Ngày', 'center'),
                ('product', 200, 'Sản phẩm', 'w'),
                ('qty', 80, 'SL', 'e'),
                ('sell_price', 100, 'Giá bán', 'e'),
                ('cost_price', 100, 'Giá nhập', 'e'),
                ('revenue', 120, 'Doanh thu', 'e'),
                ('cost', 120, 'Chi phí', 'e'),
                ('profit', 120, 'Lợi nhuận', 'e')
            ]:
                tree.heading(c, text=t)
                tree.column(c, width=w, anchor=anchor)
            
            tree.tag_configure('odd', background='#f6f8fa')
            tree.tag_configure('profit_positive', foreground='#2e7d32')
            tree.tag_configure('profit_negative', foreground='#d32f2f')
            tree.tag_configure('total', background='#e8f5e9', font=('Segoe UI', 10, 'bold'))
            tree.pack(fill='both', expand=True)
            
            # Load dữ liệu
            total_revenue = total_cost = total_profit = 0
            for idx, row in enumerate(data):
                revenue = row.get('revenue', 0) or 0
                cost = row.get('cost', 0) or 0
                profit = row.get('profit', 0) or 0
                qty = row.get('qty', 0) or 0
                sell_price = row.get('sell_price', 0) or 0
                cost_price = row.get('cost_price', 0) or 0
                product_name = row.get('product_name', '') or ''
                
                total_revenue += revenue
                total_cost += cost
                total_profit += profit
                
                tags = ['odd'] if idx % 2 else []
                if profit > 0:
                    tags.append('profit_positive')
                elif profit < 0:
                    tags.append('profit_negative')
                
                tree.insert('', 'end', values=(
                    row.get('sale_date', ''),
                    product_name[:30] + '...' if len(product_name) > 30 else product_name,
                    f"{qty:,.0f}",
                    f"{sell_price:,.0f} đ",
                    f"{cost_price:,.0f} đ",
                    f"{revenue:,.0f} đ",
                    f"{cost:,.0f} đ",
                    f"{profit:,.0f} đ"
                ), tags=tags)
            
            # Dòng tổng
            if data:
                tree.insert('', 'end', values=(
                    'TỔNG', '', '', '', '',
                    f"{total_revenue:,.0f} đ",
                    f"{total_cost:,.0f} đ",
                    f"{total_profit:,.0f} đ"
                ), tags=('total',))
            
            # Chuyển sang tab chi tiết
            self.adv_report_nb.select(self.adv_detail_tab)
            
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def show_top_products_report(self):
        """Hiển thị báo cáo top sản phẩm"""
        try:
            start_date = self.adv_de_from.entry.get().strip()
            end_date = self.adv_de_to.entry.get().strip()
            
            if not start_date or not end_date:
                messagebox.showwarning('Thiếu thông tin', 'Vui lòng chọn đầy đủ ngày bắt đầu và kết thúc')
                return
            
            data = self.report_manager.get_top_products(start_date, end_date, 20)
            self.display_top_products_report(data)
            
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def display_top_products_report(self, data):
        """Hiển thị báo cáo top sản phẩm"""
        try:
            # Clear detail tab
            for widget in self.adv_detail_tab.winfo_children():
                widget.destroy()
            
            main_frame = tb.Frame(self.adv_detail_tab)
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Title
            tb.Label(main_frame, text="TOP SẢN PHẨM BÁN CHẠY", 
                    font=('Segoe UI', 14, 'bold'), bootstyle='primary').pack(pady=(0, 15))
            
            # Bảng dữ liệu
            cols = ('rank', 'product', 'qty', 'orders', 'revenue', 'avg_price')
            tree = tb.Treeview(main_frame, columns=cols, show='headings', height=15)
            
            for c, w, t, anchor in [
                ('rank', 60, 'Hạng', 'center'),
                ('product', 300, 'Sản phẩm', 'w'),
                ('qty', 100, 'Tổng SL', 'e'),
                ('orders', 100, 'Số đơn', 'e'),
                ('revenue', 150, 'Doanh thu', 'e'),
                ('avg_price', 120, 'Giá TB', 'e')
            ]:
                tree.heading(c, text=t)
                tree.column(c, width=w, anchor=anchor)
            
            tree.tag_configure('odd', background='#f6f8fa')
            tree.tag_configure('top3', background='#fff3e0')
            tree.pack(fill='both', expand=True)
            
            # Load dữ liệu
            for idx, row in enumerate(data):
                rank = idx + 1
                tags = ['odd'] if idx % 2 else []
                if rank <= 3:
                    tags.append('top3')
                
                product_name = row.get('product_name', '') or ''
                total_qty = row.get('total_qty', 0) or 0
                total_orders = row.get('total_orders', 0) or 0
                total_revenue = row.get('total_revenue', 0) or 0
                avg_price = row.get('avg_price', 0) or 0
                
                tree.insert('', 'end', values=(
                    f"#{rank}",
                    product_name,
                    f"{total_qty:,.0f}",
                    f"{total_orders:,}",
                    f"{total_revenue:,.0f} đ",
                    f"{avg_price:,.0f} đ"
                ), tags=tags)
            
            # Chuyển sang tab chi tiết
            self.adv_report_nb.select(self.adv_detail_tab)
            
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def show_revenue_chart(self):
        """Hiển thị biểu đồ doanh thu"""
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror('Lỗi', 'Thư viện matplotlib chưa được cài đặt. Vui lòng chạy: pip install matplotlib')
            return
        
        try:
            start_date = self.adv_de_from.entry.get().strip()
            end_date = self.adv_de_to.entry.get().strip()
            
            if not start_date or not end_date:
                messagebox.showwarning('Thiếu thông tin', 'Vui lòng chọn đầy đủ ngày bắt đầu và kết thúc')
                return
            
            # Clear chart tab
            for widget in self.adv_chart_tab.winfo_children():
                widget.destroy()
            
            # Lấy dữ liệu
            data = self.report_manager.get_revenue_report(start_date, end_date, 'day')
            
            if not data:
                messagebox.showinfo('Thông báo', 'Không có dữ liệu để hiển thị biểu đồ')
                return
            
            # Tạo biểu đồ
            fig = Figure(figsize=(12, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Chuẩn bị dữ liệu
            dates = []
            revenues = []
            orders = []
            
            for row in data:
                try:
                    period = row.get('period', '')
                    if period:
                        dates.append(dt.datetime.strptime(period, '%Y-%m-%d'))
                        revenues.append(row.get('total_revenue', 0) or 0)
                        orders.append(row.get('total_orders', 0) or 0)
                except ValueError:
                    continue  # Bỏ qua ngày không hợp lệ
            
            if not dates:
                # Không có dữ liệu để vẽ
                ax.text(0.5, 0.5, 'Không có dữ liệu để hiển thị biểu đồ', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
                ax.set_title('Biểu đồ doanh thu theo ngày')
            else:
                # Vẽ biểu đồ doanh thu
                ax.plot(dates, revenues, marker='o', linewidth=2, markersize=6, color='#2e7d32', label='Doanh thu')
                ax.set_xlabel('Ngày')
                ax.set_ylabel('Doanh thu (VNĐ)')
                ax.set_title('Biểu đồ doanh thu theo ngày')
                ax.grid(True, alpha=0.3)
                ax.legend()
            
            # Format trục Y
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            # Format trục X (chỉ khi có dữ liệu)
            if dates:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Tạo canvas
            canvas = FigureCanvasTkAgg(fig, self.adv_chart_tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
            
            # Chuyển sang tab biểu đồ
            self.adv_report_nb.select(self.adv_chart_tab)
            
        except Exception as e:
            messagebox.showerror('Lỗi', str(e))

    def export_report_csv(self):
        start_s = self.de_from.entry.get().strip() if hasattr(self, 'de_from') else ''
        end_s   = self.de_to.entry.get().strip() if hasattr(self, 'de_to') else ''
        if not start_s or not end_s:
            messagebox.showwarning('Thiếu ngày', 'Chọn đủ Từ ngày và Đến ngày'); return

        rows = self.db.xnt_report(start_s, end_s)
        if not rows:
            messagebox.showinfo('Thông báo','Không có dữ liệu'); return

        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV','*.csv')],
            initialfile=f'bao_cao_xuat_nhap_ton_{start_s}_to_{end_s}.csv'
        )
        if not path: return

        import csv
        tot_open = tot_in = tot_out = tot_close = 0.0
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['productId','productName','opening','inbound','outbound','closing'])
            for r in rows:
                w.writerow([r['productId'], r['productName'], r['opening'], r['inbound'], r['outbound'], r['closing']])
                tot_open  += float(r['opening']); tot_in += float(r['inbound'])
                tot_out   += float(r['outbound']); tot_close += float(r['closing'])
            w.writerow([])
            w.writerow(['', 'TOTAL', round(tot_open,4), round(tot_in,4), round(tot_out,4), round(tot_close,4)])

        self.toast('Đã lưu báo cáo X–N–T')

    def export_current_report_excel(self):
        """Xuất báo cáo hiện tại ra Excel"""
        try:
            # Lấy dữ liệu báo cáo hiện tại
            report_data = self.get_current_report_data()
            if not report_data:
                messagebox.showwarning('Cảnh báo', 'Không có dữ liệu báo cáo để xuất')
                return
            
            # Chọn file để lưu
            start_date = self.adv_de_from.entry.get().strip()
            end_date = self.adv_de_to.entry.get().strip()
            filename = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel files', '*.xlsx'), ('All files', '*.*')],
                initialfile=f'bao_cao_{start_date}_to_{end_date}.xlsx'
            )
            
            if filename:
                # Xuất ra Excel
                self.export_manager.export_to_excel(
                    data=report_data['data'],
                    filename=filename,
                    sheet_name=report_data['title'],
                    headers=report_data.get('headers')
                )
                messagebox.showinfo('Thành công', f'Đã xuất báo cáo ra Excel:\n{filename}')
                
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể xuất Excel: {str(e)}')
    
    def export_current_report_pdf(self):
        """Xuất báo cáo hiện tại ra PDF"""
        try:
            # Lấy dữ liệu báo cáo hiện tại
            report_data = self.get_current_report_data()
            if not report_data:
                messagebox.showwarning('Cảnh báo', 'Không có dữ liệu báo cáo để xuất')
                return
            
            # Chọn file để lưu
            start_date = self.adv_de_from.entry.get().strip()
            end_date = self.adv_de_to.entry.get().strip()
            filename = filedialog.asksaveasfilename(
                defaultextension='.pdf',
                filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')],
                initialfile=f'bao_cao_{start_date}_to_{end_date}.pdf'
            )
            
            if filename:
                # Xuất ra PDF
                self.export_manager.export_to_pdf(
                    data=report_data['data'],
                    filename=filename,
                    title=report_data['title'],
                    headers=report_data.get('headers')
                )
                messagebox.showinfo('Thành công', f'Đã xuất báo cáo ra PDF:\n{filename}')
                
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể xuất PDF: {str(e)}')
    
    def export_current_report_csv(self):
        """Xuất báo cáo hiện tại ra CSV"""
        try:
            # Lấy dữ liệu báo cáo hiện tại
            report_data = self.get_current_report_data()
            if not report_data:
                messagebox.showwarning('Cảnh báo', 'Không có dữ liệu báo cáo để xuất')
                return
            
            # Chọn file để lưu
            start_date = self.adv_de_from.entry.get().strip()
            end_date = self.adv_de_to.entry.get().strip()
            filename = filedialog.asksaveasfilename(
                defaultextension='.csv',
                filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
                initialfile=f'bao_cao_{start_date}_to_{end_date}.csv'
            )
            
            if filename:
                # Xuất ra CSV
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    if report_data.get('headers'):
                        writer = csv.writer(f)
                        writer.writerow(report_data['headers'])
                        
                        for row in report_data['data']:
                            if isinstance(row, dict):
                                writer.writerow([row.get(h, '') for h in report_data['headers']])
                            else:
                                writer.writerow(row)
                    else:
                        # Sử dụng pandas nếu có
                        if PANDAS_AVAILABLE:
                            df = pd.DataFrame(report_data['data'])
                            df.to_csv(filename, index=False, encoding='utf-8')
                        else:
                            # Fallback manual CSV
                            writer = csv.writer(f)
                            for row in report_data['data']:
                                if isinstance(row, dict):
                                    writer.writerow(list(row.values()))
                                else:
                                    writer.writerow(row)
                
                messagebox.showinfo('Thành công', f'Đã xuất báo cáo ra CSV:\n{filename}')
                
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể xuất CSV: {str(e)}')
    
    def get_current_report_data(self):
        """Lấy dữ liệu báo cáo hiện tại đang hiển thị"""
        try:
            # Lấy thông tin từ tab hiện tại
            current_tab = self.adv_report_nb.select()
            tab_text = self.adv_report_nb.tab(current_tab, 'text')
            
            start_date = self.adv_de_from.entry.get().strip()
            end_date = self.adv_de_to.entry.get().strip()
            
            if not start_date or not end_date:
                return None
            
            # Xác định loại báo cáo dựa trên tab hiện tại
            if 'Tóm tắt' in tab_text:
                # Báo cáo tóm tắt
                summary = self.report_manager.get_daily_sales_summary(start_date, end_date)
                return {
                    'title': f'Báo cáo tóm tắt từ {start_date} đến {end_date}',
                    'data': [summary],
                    'headers': ['Chỉ số', 'Giá trị']
                }
            elif 'Chi tiết' in tab_text:
                # Báo cáo chi tiết - lấy báo cáo doanh thu
                data = self.report_manager.get_revenue_report(start_date, end_date, 'day')
                return {
                    'title': f'Báo cáo doanh thu chi tiết từ {start_date} đến {end_date}',
                    'data': data,
                    'headers': ['Ngày', 'Số đơn hàng', 'Tổng doanh thu', 'Tổng thanh toán', 'Giá trị TB/đơn']
                }
            else:
                # Mặc định là báo cáo doanh thu
                data = self.report_manager.get_revenue_report(start_date, end_date, 'day')
                return {
                    'title': f'Báo cáo doanh thu từ {start_date} đến {end_date}',
                    'data': data,
                    'headers': ['Ngày', 'Số đơn hàng', 'Tổng doanh thu', 'Tổng thanh toán', 'Giá trị TB/đơn']
                }
                
        except Exception as e:
            print(f"Lỗi lấy dữ liệu báo cáo: {e}")
            return None

    # helpers chung
    def sort_tree(self, tree: tb.Treeview, col: str):
        data = [(tree.set(k, col), k) for k in tree.get_children('')]
        def to_num(x):
            try:
                if isinstance(x, str): x = x.replace(',', '')
                return float(x)
            except:
                return x.lower() if isinstance(x, str) else x
        data.sort(key=lambda t: to_num(t[0]))
        for i, (_, k) in enumerate(data): tree.move(k, '', i)

    def refresh_products(self):
        self._products = self.db.q('SELECT id, name FROM products ORDER BY name')
        opts = [f"{p['id']} — {p['name']}" for p in self._products]
        self.cmb_prod['values'] = opts; self.cmb_prod_pos['values'] = opts
        if opts:
            self.cmb_prod.current(0); self.cmb_prod_pos.current(0)
            self.update_purchase_unit_and_price()
            self.update_pos_price_and_unit()

    def _fill_tree(self, tree: tb.Treeview, rows):
        for i in tree.get_children(): tree.delete(i)
        keymap = {'product':'productId','productName':'productName','batch':'batchId','lot':'lotNo','exp':'expiryDate',
                  'qty':'qtyBase','cost':'costBase','value':'valueBase'}
        for idx, r in enumerate(rows):
            tree.insert('', 'end', values=[r.get(keymap.get(c, c), '') for c in tree['columns']],
                        tags=('odd',) if idx%2 else ())

    def refresh_stock(self):
        rows = self.db.stock_view()
        self._fill_tree(self.tree_stock, rows)
        self._fill_tree(self.tree_stock2, rows)

    def refresh_alerts(self):
        try: days = int(self.ent_warn_days.get())
        except: days = 90
        self._fill_tree(self.tree_alerts, self.db.expiring_view(days))

    def refresh_report(self):
        start_s = self.de_from.entry.get().strip() if hasattr(self, 'de_from') else ''
        end_s   = self.de_to.entry.get().strip() if hasattr(self, 'de_to') else ''

        # Clear
        for i in self.tree_report.get_children():
            self.tree_report.delete(i)

        if not start_s or not end_s:
            messagebox.showwarning('Thiếu ngày', 'Chọn đủ Từ ngày và Đến ngày'); return

        rows = self.db.xnt_report(start_s, end_s)

        tot_open = tot_in = tot_out = tot_close = 0.0
        for idx, r in enumerate(rows):
            tag = 'odd' if idx % 2 else ''
            tot_open  += float(r['opening'])
            tot_in    += float(r['inbound'])
            tot_out   += float(r['outbound'])
            tot_close += float(r['closing'])
            self.tree_report.insert(
                '',
                'end',
                values=(
                    r['productId'], r['productName'],
                    r['opening'], r['inbound'], r['outbound'], r['closing']
                ),
                tags=(tag,)
            )

        # Dòng tổng
        if rows:
            self.tree_report.insert(
                '', 'end',
                values=('', 'TỔNG', round(tot_open,4), round(tot_in,4), round(tot_out,4), round(tot_close,4)),
                tags=('total',)
            )


    def on_ready(self):
        self.refresh_products(); self.refresh_stock(); self.refresh_alerts(); self.refresh_report()
        self.refresh_backup_list()
        # Load advanced reports summary
        if hasattr(self, 'load_advanced_summary'):
            self.load_advanced_summary()
        # Update catalog info
        if hasattr(self, 'update_catalog_info'):
            self.update_catalog_info()
        # Tự động load thuoc.csv nếu có
        self.auto_load_medicine_catalog()
        # Cập nhật status database
        self.update_db_status()

    def auto_load_medicine_catalog(self):
        """Tự động load file thuoc.csv khi khởi động"""
        try:
            # Tìm file thuoc.csv trong thư mục hiện tại
            csv_path = os.path.join(os.getcwd(), 'thuoc.csv')
            
            if os.path.exists(csv_path):
                self.medicine_catalog.load_catalog_from_excel(csv_path)
                self.update_catalog_info()
                print(f"Đã tự động load danh mục thuốc: {os.path.basename(csv_path)}")
            else:
                print("Không tìm thấy file thuoc.csv để tự động load")
                
        except Exception as e:
            print(f"Lỗi khi tự động load danh mục thuốc: {e}")

# --- LicenseManager: xác minh license offline (Ed25519, không cần PyNaCl) ---
import os, json, base64
from tkinter import simpledialog, messagebox
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

try:
    LIC_PATH
except NameError:
    APP_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'Nhathuoc')
    os.makedirs(APP_DIR, exist_ok=True)
    LIC_PATH = os.path.join(APP_DIR, 'license.lic')

PUBLIC_B64 = "cfCth+TwUKiTYPS0gjUoSmwEBBPM6ElQo82e8RdtWl8="  # Public key từ dist/private_key.pem

class LicenseError(Exception): pass

class LicenseManager:
    def __init__(self):
        self.data = None

    def _verify(self, lic_str: str):
        try:
            pack = json.loads(base64.b64decode(lic_str).decode('utf-8'))
            payload = pack["payload"]; sig_b64 = pack["sig"]
        except Exception as e:
            raise LicenseError("Định dạng license không hợp lệ") from e

        blob = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        sig  = base64.b64decode(sig_b64)
        pub  = base64.b64decode(PUBLIC_B64)

        try:
            Ed25519PublicKey.from_public_bytes(pub).verify(sig, blob)
        except InvalidSignature:
            raise LicenseError("License không hợp lệ hoặc bị chỉnh sửa")

        if payload.get("product") != "nhathuoc":
            raise LicenseError("License sai sản phẩm")

        # Khớp fingerprint (nếu cấp theo máy)
        try:
            hw_now = machine_fingerprint()
        except Exception:
            hw_now = None
        if payload.get("hw") and hw_now and payload["hw"] != hw_now:
            raise LicenseError("License không thuộc máy này")

        self.data = payload
        return payload

    def load(self):
        if not os.path.exists(LIC_PATH):
            raise LicenseError("Chưa kích hoạt")
        lic_str = open(LIC_PATH, 'r', encoding='utf-8').read().strip()
        return self._verify(lic_str)

    def prompt_and_save(self, tkroot=None):
        lic = simpledialog.askstring("Kích hoạt", "Dán license vĩnh viễn cho máy này:")
        if not lic:
            raise LicenseError("Không có license")
        self._verify(lic)
        with open(LIC_PATH, 'w', encoding='utf-8') as f:
            f.write(lic.strip())
        messagebox.showinfo("Kích hoạt", "Kích hoạt thành công! Khởi chạy đầy đủ tính năng.")
        return self.data
# --- /LicenseManager ---

# --- Barcode Scanner ---
class BarcodeScanner:
    def __init__(self, parent_window, callback=None):
        self.parent = parent_window
        self.callback = callback
        self.cap = None
        self.scanning = False
        self.window = None
        
    def start_scan(self):
        """Bắt đầu quét barcode"""
        if not BARCODE_AVAILABLE:
            messagebox.showerror("Lỗi", 
                "Thư viện quét barcode chưa được cài đặt.\n"
                "Vui lòng chạy: pip install opencv-python pyzbar Pillow")
            return
            
        try:
            # Tạo window mới cho camera
            self.window = tk.Toplevel(self.parent)
            self.window.title("📷 Quét Barcode")
            self.window.geometry("640x480")
            self.window.resizable(False, False)
            
            # Tạo frame chính
            main_frame = tb.Frame(self.window)
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Header
            header_frame = tb.Frame(main_frame)
            header_frame.pack(fill='x', pady=(0, 10))
            
            title_label = tb.Label(header_frame, text="📷 Quét Barcode", 
                                  font=('Segoe UI', 14, 'bold'), bootstyle='primary')
            title_label.pack()
            
            subtitle_label = tb.Label(header_frame, text="Đưa barcode vào khung hình để quét", 
                                     font=('Segoe UI', 10), bootstyle='secondary')
            subtitle_label.pack()
            
            # Video frame
            self.video_frame = tb.Frame(main_frame, relief='sunken', borderwidth=2)
            self.video_frame.pack(fill='both', expand=True, pady=(0, 10))
            
            self.video_label = tb.Label(self.video_frame, text="Đang khởi động camera...", 
                                       font=('Segoe UI', 12), bootstyle='info')
            self.video_label.pack(expand=True)
            
            # Control buttons
            button_frame = tb.Frame(main_frame)
            button_frame.pack(fill='x')
            
            self.start_btn = tb.Button(button_frame, text="▶️ Bắt đầu quét", 
                                      command=self.toggle_scan, bootstyle='success')
            self.start_btn.pack(side='left', padx=(0, 10))
            
            self.stop_btn = tb.Button(button_frame, text="⏹️ Dừng", 
                                     command=self.stop_scan, bootstyle='danger')
            self.stop_btn.pack(side='left', padx=(0, 10))
            
            tb.Button(button_frame, text="❌ Đóng", 
                     command=self.close_scanner, bootstyle='secondary').pack(side='right')
            
            # Status label
            self.status_label = tb.Label(main_frame, text="Sẵn sàng", 
                                        font=('Segoe UI', 10), bootstyle='info')
            self.status_label.pack(pady=(10, 0))
            
            # Khởi tạo camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Lỗi", "Không thể mở camera. Vui lòng kiểm tra kết nối.")
                self.close_scanner()
                return
                
            # Cấu hình camera
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Bắt đầu quét
            self.toggle_scan()
            
            # Bind close event
            self.window.protocol("WM_DELETE_WINDOW", self.close_scanner)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể khởi động camera: {e}")
            
    def toggle_scan(self):
        """Bật/tắt quét"""
        if not self.scanning:
            self.start_scanning()
        else:
            self.stop_scanning()
            
    def start_scanning(self):
        """Bắt đầu quét"""
        self.scanning = True
        self.start_btn.config(text="⏸️ Tạm dừng", bootstyle='warning')
        self.status_label.config(text="Đang quét...", bootstyle='success')
        self.update_frame()
        
    def stop_scanning(self):
        """Tạm dừng quét"""
        self.scanning = False
        self.start_btn.config(text="▶️ Tiếp tục", bootstyle='success')
        self.status_label.config(text="Đã tạm dừng", bootstyle='warning')
        
    def update_frame(self):
        """Cập nhật frame camera"""
        if not self.scanning or not self.cap:
            return
            
        try:
            ret, frame = self.cap.read()
            if ret:
                # Lật frame để hiển thị đúng
                frame = cv2.flip(frame, 1)
                
                # Quét barcode nếu đang quét
                if self.scanning:
                    barcodes = pyzbar.decode(frame)
                    for barcode in barcodes:
                        # Lấy dữ liệu barcode
                        barcode_data = barcode.data.decode('utf-8')
                        barcode_type = barcode.type
                        
                        # Vẽ khung quanh barcode
                        (x, y, w, h) = barcode.rect
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        
                        # Hiển thị thông tin
                        text = f"{barcode_type}: {barcode_data}"
                        cv2.putText(frame, text, (x, y - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        # Gọi callback với dữ liệu barcode
                        if self.callback:
                            self.callback(barcode_data)
                            
                        # Dừng quét sau khi tìm thấy
                        self.stop_scanning()
                        self.status_label.config(text=f"Đã quét: {barcode_data}", bootstyle='success')
                        break
                
                # Chuyển đổi frame để hiển thị trong Tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_pil = Image.fromarray(frame_rgb)
                frame_tk = ImageTk.PhotoImage(frame_pil)
                
                # Cập nhật label
                self.video_label.config(image=frame_tk, text="")
                self.video_label.image = frame_tk
                
            # Lên lịch cập nhật tiếp theo
            if self.scanning:
                self.window.after(30, self.update_frame)
                
        except Exception as e:
            print(f"Lỗi cập nhật frame: {e}")
            self.stop_scanning()
            
    def stop_scan(self):
        """Dừng quét"""
        self.stop_scanning()
        
    def close_scanner(self):
        """Đóng scanner"""
        self.scanning = False
        if self.cap:
            self.cap.release()
        if self.window:
            self.window.destroy()
        self.window = None
        self.cap = None

# --- /Barcode Scanner ---

if __name__ == '__main__':
    import tkinter as tk
    tkroot = tk.Tk(); tkroot.withdraw()

    lm = LicenseManager()
    try:
        lm.load()
    except Exception:
        fp = machine_fingerprint()
        # copy fingerprint vào clipboard cho tiện
        try:
            tkroot.clipboard_clear(); tkroot.clipboard_append(fp)
        except Exception:
            pass
        messagebox.showinfo("Kích hoạt bản quyền",
                            f"Fingerprint máy: {fp}\n(đã copy vào clipboard)\n\nGửi mã này cho người bán để nhận license vĩnh viễn.")
        try:
            lm.prompt_and_save(tkroot)  # cho nhập license ngay nếu đã có
        except Exception as e2:
            messagebox.showerror("License", str(e2))
            raise SystemExit(1)

    tkroot.destroy()
    app = App()
    app.mainloop()

