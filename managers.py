# managers.py — Các lớp quản lý phụ trợ (Backup, Export, Báo cáo, Catalog)
import os
import shutil
import json
import datetime as dt
import threading
import schedule
import time

from config import (
    APP_VERSION, APP_NAME, SCHEMA_VERSION,
    PANDAS_AVAILABLE, PDF_AVAILABLE
)
from database import DB
import sqlite3

# Import conditional libraries
if PANDAS_AVAILABLE:
    import pandas as pd
if PDF_AVAILABLE:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch


# ---------------- Backup Manager ----------------
class BackupManager:
    def __init__(self, db_path: str, backup_dir: str):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.auto_backup_enabled = True
        self.backup_interval_hours = 24  # Mặc định 24 giờ
        self.max_backups = 30  # Giữ tối đa 30 file backup
        
    def create_backup(self, custom_name: str = None) -> str:
        """Tạo backup database (Lỗi 4: Sử dụng Backup API an toàn)"""
        try:
            timestamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
            if custom_name:
                backup_name = f"{custom_name}_{timestamp}.db"
            else:
                backup_name = f"backup_{timestamp}.db"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Sử dụng sqlite3 backup API để backup an toàn
            src = sqlite3.connect(self.db_path)
            dst = sqlite3.connect(backup_path)
            with dst:
                src.backup(dst)
            dst.close()
            src.close()
            
            # Tạo file metadata
            metadata = {
                'created_at': dt.datetime.now().isoformat(),
                'db_size': os.path.getsize(self.db_path),
                'backup_size': os.path.getsize(backup_path),
                'version': APP_VERSION,
                'schema_version': SCHEMA_VERSION
            }
            
            metadata_path = backup_path.replace('.db', '.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self._cleanup_old_backups()
            return backup_path
            
        except Exception as e:
            raise Exception(f"Lỗi tạo backup: {str(e)}")
    
    def restore_backup(self, backup_path: str) -> bool:
        """Khôi phục từ backup (Lỗi 4: Sử dụng Backup API an toàn + Integrity check)"""
        try:
            if not os.path.exists(backup_path):
                raise Exception("File backup không tồn tại")
            
            # Tạo backup hiện tại trước khi restore
            current_backup = self.create_backup("before_restore")
            
            # Restore database bằng backup API
            src = sqlite3.connect(backup_path)
            dst = sqlite3.connect(self.db_path)
            with dst:
                src.backup(dst)
            dst.close()
            src.close()
            
            # Kiểm tra tính toàn vẹn của dữ liệu sau restore
            conn = sqlite3.connect(self.db_path)
            try:
                integrity = conn.execute("PRAGMA integrity_check").fetchone()
                if not integrity or integrity[0] != 'ok':
                    raise Exception("Integrity check database thất bại sau restore")
                fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
                if fk_check:
                    raise Exception(f"Foreign key check thất bại: {fk_check}")
            finally:
                conn.close()
            
            return True
            
        except Exception as e:
            raise Exception(f"Lỗi khôi phục backup: {str(e)}")
    
    def export_data(self, export_path: str) -> bool:
        """Export toàn bộ dữ liệu ra file JSON (Lỗi 5: Thêm schemaVersion, audit_logs)"""
        try:
            db = DB(self.db_path)
            
            export_data = {
                'export_info': {
                    'created_at': dt.datetime.now().isoformat(),
                    'version': APP_VERSION,
                    'app_name': APP_NAME,
                    'schema_version': SCHEMA_VERSION
                },
                'products': db.q("SELECT * FROM products"),
                'product_units': db.q("SELECT * FROM product_units"),
                'batches': db.q("SELECT * FROM batches"),
                'stock_movements': db.q("SELECT * FROM stock_movements"),
                'sales': db.q("SELECT * FROM sales"),
                'sale_items': db.q("SELECT * FROM sale_items"),
                'dispatch_notes': db.q("SELECT * FROM dispatch_notes"),
                'dispatch_items': db.q("SELECT * FROM dispatch_items"),
                'purchase_notes': db.q("SELECT * FROM purchase_notes"),
                'purchase_items': db.q("SELECT * FROM purchase_items"),
                'receiving_units': db.q("SELECT * FROM receiving_units"),
                'temperature_logs': db.q("SELECT * FROM temperature_logs"),
                'audit_logs': db.q("SELECT * FROM audit_logs")
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            raise Exception(f"Lỗi export dữ liệu: {str(e)}")
    
    def import_data(self, import_path: str) -> bool:
        """Import dữ liệu từ file JSON (Lỗi 5: Transaction, Whitelist, Correct Order & FK check)"""
        db = None
        try:
            if not os.path.exists(import_path):
                raise Exception("File import không tồn tại")
            
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Tạo backup trước khi import
            self.create_backup("before_import")
            
            db = DB(self.db_path)
            
            # Tập hợp whitelist bảng hợp lệ
            allowed_tables = {
                'products', 'product_units', 'batches', 'stock_movements',
                'sales', 'sale_items', 'dispatch_notes', 'dispatch_items',
                'purchase_notes', 'purchase_items', 'receiving_units',
                'temperature_logs', 'audit_logs'
            }
            
            # Bắt đầu transaction
            db.conn.execute("BEGIN TRANSACTION")
            
            # Xóa dữ liệu cũ (thứ tự child trước, parent sau)
            db.conn.execute("DELETE FROM temperature_logs")
            db.conn.execute("DELETE FROM audit_logs")
            db.conn.execute("DELETE FROM dispatch_items")
            db.conn.execute("DELETE FROM dispatch_notes")
            db.conn.execute("DELETE FROM purchase_items")
            db.conn.execute("DELETE FROM purchase_notes")
            db.conn.execute("DELETE FROM receiving_units")
            db.conn.execute("DELETE FROM sale_items")
            db.conn.execute("DELETE FROM sales")
            db.conn.execute("DELETE FROM stock_movements")
            db.conn.execute("DELETE FROM batches")
            db.conn.execute("DELETE FROM product_units")
            db.conn.execute("DELETE FROM products")
            
            # Thứ tự import an toàn (parent trước, child sau)
            table_order = [
                'products', 'product_units', 'batches', 'receiving_units',
                'sales', 'sale_items', 'purchase_notes', 'purchase_items',
                'dispatch_notes', 'dispatch_items', 'stock_movements',
                'temperature_logs', 'audit_logs'
            ]
            
            for table in table_order:
                if table not in allowed_tables or table not in import_data:
                    continue
                data = import_data[table]
                if not data:
                    continue
                
                # Lấy thông tin các cột thực tế của bảng để whitelist cột
                db_cols = {r[1] for r in db.conn.execute(f"PRAGMA table_info({table})")}
                first_row_cols = list(data[0].keys())
                valid_columns = [col for col in first_row_cols if col in db_cols]
                
                if not valid_columns:
                    continue
                
                placeholders = ','.join(['?' for _ in valid_columns])
                sql = f"INSERT INTO {table} ({','.join(valid_columns)}) VALUES ({placeholders})"
                
                for row in data:
                    values = [row.get(col) for col in valid_columns]
                    db.conn.execute(sql, values)
            
            # Foreign key check trước khi commit
            fk_check = db.conn.execute("PRAGMA foreign_key_check").fetchall()
            if fk_check:
                raise Exception(f"Foreign key check thất bại: {fk_check}")
            
            db.conn.commit()
            return True
        except Exception as ex:
            if db:
                try:
                    db.conn.rollback()
                except:
                    pass
            raise Exception(f"Lỗi import dữ liệu: {str(ex)}")
    
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
        """Thống kê phiếu xuất kho theo ngày/tháng/năm (Thay cho báo cáo doanh thu cũ)"""
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
                COUNT(DISTINCT dn.id) as total_orders, -- Số lượng phiếu xuất
                SUM(di.qty) as total_revenue,          -- Tổng số lượng sản phẩm xuất
                COUNT(di.id) as total_paid,            -- Số lượng danh mục mặt hàng xuất
                AVG(di.qty) as avg_order_value         -- Số lượng TB trên mỗi dòng
            FROM dispatch_notes dn
            LEFT JOIN dispatch_items di ON dn.id = di.dispatchId
            WHERE DATE(dn.createdAt) BETWEEN DATE(?) AND DATE(?)
            GROUP BY {group_format}
            ORDER BY period
            '''
            
            return db.q(sql, (start_date, end_date))
            
        except Exception as e:
            raise Exception(f"Lỗi thống kê xuất kho: {str(e)}")
    
    def get_profit_report(self, start_date: str, end_date: str) -> list:
        """Thống kê cấp phát theo đơn vị nhận (Thay cho báo cáo lợi nhuận cũ)"""
        try:
            db = DB(self.db_path)
            
            sql = '''
            SELECT 
                DATE(dn.createdAt) as sale_date,       -- Ngày xuất
                dn.receivingUnit as product_name,       -- Tên đơn vị nhận (hiển thị ở cột sản phẩm)
                COUNT(DISTINCT dn.id) as qty,          -- Số lượng phiếu nhận
                0 as sell_price,
                0 as cost_price,
                SUM(di.qty) as revenue,                -- Tổng số lượng sản phẩm nhận
                COUNT(di.id) as cost,                  -- Số lượng loại sản phẩm nhận
                SUM(di.qty) as profit                  -- Tổng số lượng
            FROM dispatch_notes dn
            LEFT JOIN dispatch_items di ON dn.id = di.dispatchId
            WHERE DATE(dn.createdAt) BETWEEN DATE(?) AND DATE(?)
            GROUP BY DATE(dn.createdAt), dn.receivingUnit
            ORDER BY dn.createdAt DESC
            '''
            
            return db.q(sql, (start_date, end_date))
            
        except Exception as e:
            raise Exception(f"Lỗi thống kê theo đơn vị nhận: {str(e)}")
    
    def get_top_products(self, start_date: str, end_date: str, limit: int = 10) -> list:
        """Top sản phẩm cấp phát nhiều nhất (Thay cho top sản phẩm bán chạy)"""
        try:
            db = DB(self.db_path)
            
            sql = '''
            SELECT 
                p.id as product_id,
                p.name as product_name,
                SUM(di.qty) as total_qty,              -- Tổng số lượng cấp
                COUNT(DISTINCT dn.id) as total_orders, -- Số lượng phiếu xuất chứa sản phẩm này
                SUM(di.qty) as total_revenue,          -- Tổng số lượng (để hiển thị)
                0 as avg_price
            FROM dispatch_notes dn
            JOIN dispatch_items di ON dn.id = di.dispatchId
            JOIN products p ON di.productId = p.id
            WHERE DATE(dn.createdAt) BETWEEN DATE(?) AND DATE(?)
            GROUP BY p.id, p.name
            ORDER BY total_qty DESC
            LIMIT ?
            '''
            
            return db.q(sql, (start_date, end_date, limit))
            
        except Exception as e:
            raise Exception(f"Lỗi thống kê top sản phẩm: {str(e)}")
    
    def get_daily_sales_summary(self, start_date: str, end_date: str) -> dict:
        """Tóm tắt cấp phát theo ngày (Thay cho tóm tắt bán hàng cũ)"""
        try:
            db = DB(self.db_path)
            
            # Tổng quan
            summary_sql = '''
            SELECT 
                COUNT(DISTINCT dn.id) as total_orders, -- Tổng số phiếu
                SUM(di.qty) as total_revenue,          -- Tổng số lượng xuất
                AVG(di.qty) as avg_order_value,
                MIN(di.qty) as min_order,
                MAX(di.qty) as max_order
            FROM dispatch_notes dn
            LEFT JOIN dispatch_items di ON dn.id = di.dispatchId
            WHERE DATE(dn.createdAt) BETWEEN DATE(?) AND DATE(?)
            '''
            
            summary_result = db.q(summary_sql, (start_date, end_date))
            summary = summary_result[0] if summary_result else {
                'total_orders': 0,
                'total_revenue': 0,
                'avg_order_value': 0,
                'min_order': 0,
                'max_order': 0
            }
            
            # Số phiếu và số lượng theo ngày
            daily_sql = '''
            SELECT 
                DATE(dn.createdAt) as sale_date,
                COUNT(DISTINCT dn.id) as orders,
                SUM(di.qty) as revenue
            FROM dispatch_notes dn
            LEFT JOIN dispatch_items di ON dn.id = di.dispatchId
            WHERE DATE(dn.createdAt) BETWEEN DATE(?) AND DATE(?)
            GROUP BY DATE(dn.createdAt)
            ORDER BY sale_date
            '''
            
            daily_data = db.q(daily_sql, (start_date, end_date))
            
            return {
                'summary': summary,
                'daily_data': daily_data
            }
            
        except Exception as e:
            raise Exception(f"Lỗi tạo tóm tắt cấp phát: {str(e)}")
    
    def get_category_performance(self, start_date: str, end_date: str) -> list:
        """Hiệu suất cấp phát theo phân loại sản phẩm (thuoc, vaccine, vtyt, khac)"""
        try:
            db = DB(self.db_path)
            
            sql = '''
            SELECT 
                p.productType as category,             -- Phân loại sản phẩm
                COUNT(DISTINCT di.productId) as product_count,
                SUM(di.qty) as total_qty,
                SUM(di.qty) as total_revenue,
                0 as avg_price
            FROM dispatch_notes dn
            JOIN dispatch_items di ON dn.id = di.dispatchId
            JOIN products p ON di.productId = p.id
            WHERE DATE(dn.createdAt) BETWEEN DATE(?) AND DATE(?)
            GROUP BY p.productType
            ORDER BY total_qty DESC
            '''
            return db.q(sql, (start_date, end_date))
        except Exception as e:
            raise Exception(f"Lỗi thống kê hiệu suất theo phân loại: {str(e)}")


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
                    reg_col = None
                    for r_col in self.catalog_data.columns:
                        if any(keyword in r_col.lower() for keyword in ['so_dang_ky', 'registration', 'dang_ky', 'number']):
                            result['registration_number'] = str(row.get(r_col, ''))
                            reg_col = r_col
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
                        if col_name != col and col_name != reg_col:
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
