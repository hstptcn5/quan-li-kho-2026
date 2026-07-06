import os

nhathuoc_path = r"d:\Bot2025\Quanlikho2026\quan-li-kho-2026\nhathuoc2.py"
ui_path = r"d:\Bot2025\Quanlikho2026\quan-li-kho-2026\ui.py"

with open(nhathuoc_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extract lines from 1421 to 6282 (1-indexed)
# 1421 is index 1420
# 6282 is index 6281, so slice is 1420:6282
class_lines = lines[1420:6282]

imports = """# -*- coding: utf-8 -*-
# ui.py — Giao diện Desktop chính (Tkinter / ttkbootstrap)
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

# Import config, database, managers, scanner, server
from config import (
    APP_NAME, APP_VERSION, AUTHOR_NAME, AUTHOR_EMAIL, AUTHOR_PHONE, AUTHOR_SITE,
    DB_PATH, LOG_PATH, BACKUP_DIR,
    BARCODE_AVAILABLE, MATPLOTLIB_AVAILABLE, PANDAS_AVAILABLE, PDF_AVAILABLE
)
from database import DB
from managers import BackupManager, ExportManager, ReportManager, MedicineCatalogManager
from scanner import BarcodeScanner
from server import MobileInventoryServer, get_local_ip

"""

with open(ui_path, 'w', encoding='utf-8') as f:
    f.write(imports)
    f.writelines(class_lines)

print("Successfully extracted ui.py!")
