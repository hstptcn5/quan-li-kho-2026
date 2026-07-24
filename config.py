# config.py — Cấu hình toàn cục cho phần mềm Quản lý XNT thuốc, vaccine và VTYT.
import os
import shutil

# ==== App info ====
APP_NAME     = "Quản lý XNT thuốc, vaccine và VTYT"
SCHEMA_VERSION = 3  # Tăng khi thay đổi schema DB
APP_VERSION  = "2.0.0"
AUTHOR_NAME  = "Hồ Sỷ Thoảng"
AUTHOR_EMAIL = "hstptcn5@gmail.com"
AUTHOR_PHONE = "0329381189"
AUTHOR_SITE  = "x/yoshinokuna"

# ==== App data paths (per-user, có quyền ghi) ====
if os.name == 'nt':
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    APP_DIR = os.path.join(base, 'QuanLyXNT')
else:
    base = os.environ.get('XDG_DATA_HOME', os.path.join(os.path.expanduser('~'), '.local', 'share'))
    APP_DIR = os.path.join(base, 'quanlyxnt')

os.makedirs(APP_DIR, exist_ok=True)

DB_PATH  = os.path.join(APP_DIR, 'pharm.db')
LOG_PATH = os.path.join(APP_DIR, 'app.log')

BACKUP_DIR = os.path.join(APP_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# Di trú DB cũ (nếu tồn tại cạnh file .py/.exe) sang APP_DIR lần đầu
for _old_name in ('pharm.db',):
    _old_db = os.path.join(os.path.dirname(__file__), _old_name)
    if not os.path.exists(DB_PATH) and os.path.exists(_old_db):
        try:
            shutil.copy2(_old_db, DB_PATH)
        except Exception:
            pass
        break

# Cũng migrate từ thư mục Nhathuoc cũ nếu có
_old_app_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Nhathuoc')
_old_db_path = os.path.join(_old_app_dir, 'pharm.db')
if not os.path.exists(DB_PATH) and os.path.exists(_old_db_path):
    try:
        shutil.copy2(_old_db_path, DB_PATH)
    except Exception:
        pass

# Thư mục chứa tài liệu báo cáo tạm thời
TEMP_DIR = os.path.join(APP_DIR, 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# Check library availabilities
try:
    import cv2
    from pyzbar import pyzbar
    from PIL import Image, ImageTk
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


SCHEMA_SQL = r'''
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  defaultUnit TEXT NOT NULL,
  barcode TEXT,
  productType TEXT DEFAULT 'thuoc',
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
  qtyBase REAL,
  originalQty REAL,
  originalUnit TEXT,
  type TEXT NOT NULL,
  cost REAL,
  receivingUnit TEXT,
  reason TEXT,
  fundSource TEXT,
  referenceType TEXT,
  referenceId INTEGER,
  referenceItemId INTEGER,
  createdAt TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
  ip TEXT,
  action TEXT NOT NULL,
  noteId INTEGER,
  details TEXT
);

-- Bảng đơn vị nhận (cấp phát cho ai)
CREATE TABLE IF NOT EXISTS receiving_units (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  address TEXT,
  note TEXT,
  createdAt TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Bảng phiếu xuất kho
CREATE TABLE IF NOT EXISTS dispatch_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  noteNumber TEXT,
  receivingUnit TEXT NOT NULL,
  reason TEXT DEFAULT 'Cấp phát',
  note TEXT,
  createdAt TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dispatch_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dispatchId INTEGER NOT NULL REFERENCES dispatch_notes(id) ON DELETE CASCADE,
  productId INTEGER NOT NULL REFERENCES products(id),
  batchId INTEGER,
  unitCode TEXT NOT NULL,
  qty REAL NOT NULL,
  lotNo TEXT,
  expiryDate TEXT,
  cost REAL DEFAULT 0
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

CREATE TABLE IF NOT EXISTS purchase_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  noteNumber TEXT,
  supplier TEXT NOT NULL,
  reason TEXT DEFAULT 'Nhập kho',
  note TEXT,
  createdAt TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchase_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  purchaseId INTEGER NOT NULL REFERENCES purchase_notes(id) ON DELETE CASCADE,
  productId INTEGER NOT NULL REFERENCES products(id),
  batchId INTEGER,
  unitCode TEXT NOT NULL,
  qty REAL NOT NULL,
  lotNo TEXT,
  expiryDate TEXT,
  cost REAL NOT NULL,
  fundSource TEXT
);

CREATE TABLE IF NOT EXISTS temperature_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  logDate TEXT NOT NULL,
  session TEXT NOT NULL,
  locationName TEXT NOT NULL,
  temperature REAL NOT NULL,
  humidity REAL,
  recordedBy TEXT,
  createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(logDate, session, locationName)
);
'''

