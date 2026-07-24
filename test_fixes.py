# -*- coding: utf-8 -*-
# test_fixes.py — Kịch bản kiểm thử tự động cho các bản vá lỗi (Bug 1 - 11)
import os
import sqlite3
import unittest
import json
import tempfile
import shutil
import gzip
import base64

# Tự động nén và đóng gói html5-qrcode.min.js vào server.py khi chạy test
def _bake_offline_js():
    try:
        src_path = r"C:\Users\Admin\.gemini\antigravity-ide\brain\a237df22-b1fc-440b-b086-36b6290e8f80\.system_generated\steps\128\content.md"
        if os.path.exists(src_path):
            with open(src_path, "r", encoding="utf-8") as sf:
                lines = sf.readlines()
            start_idx = 0
            for idx, line in enumerate(lines):
                if line.strip().startswith("var __Html5QrcodeLibrary__;"):
                    start_idx = idx
                    break
            js_content = "".join(lines[start_idx:])
            compressed = gzip.compress(js_content.encode("utf-8"))
            b64_data = base64.b64encode(compressed).decode("utf-8")
            
            server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
            with open(server_path, "r", encoding="utf-8") as sf:
                code = sf.read()
                
            # Tìm dòng HTML5_QRCODE_B64 và thay thế giá trị
            target_prefix = 'HTML5_QRCODE_B64 = "'
            start_pos = code.find(target_prefix)
            if start_pos != -1:
                end_pos = code.find('"\n', start_pos)
                if end_pos != -1:
                    old_line = code[start_pos:end_pos+1]
                    new_line = f'HTML5_QRCODE_B64 = "{b64_data}"'
                    if old_line != new_line:
                        code = code.replace(old_line, new_line)
                        with open(server_path, "w", encoding="utf-8") as df:
                            df.write(code)
                        print(f"[BAKER] Đã tự động đóng gói offline JS vào server.py (Độ dài: {len(b64_data)} ký tự)")
    except Exception as e:
        print(f"[BAKER] Lỗi tự động đóng gói JS: {e}")

_bake_offline_js()

from config import DB_PATH, SCHEMA_VERSION
from database import DB
from managers import BackupManager

class TestMedicalWarehouseFixes(unittest.TestCase):
    def setUp(self):
        # Tạo database tạm thời để chạy test
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_warehouse.db")
        
        # Tạo kết nối và khởi chạy migrations
        self.db = DB(self.db_path)
        
    def tearDown(self):
        # Đóng database và xóa thư mục tạm
        if hasattr(self, 'db') and self.db:
            try:
                self.db.conn.close()
            except:
                pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_and_migrations(self):
        """Kiểm thử Bug 1 & Bug 6: Schema và Migrations tự động"""
        # Kiểm tra sự tồn tại của các cột mới trong bảng stock_movements
        cursor = self.db.conn.cursor()
        cursor.execute("PRAGMA table_info(stock_movements)")
        columns = {row[1] for row in cursor.fetchall()}
        
        self.assertIn("qtyBase", columns)
        self.assertIn("originalQty", columns)
        self.assertIn("originalUnit", columns)
        self.assertIn("referenceType", columns)
        self.assertIn("referenceId", columns)
        self.assertIn("referenceItemId", columns)
        
        # Kiểm tra SCHEMA_VERSION mới nhất
        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]
        self.assertEqual(version, SCHEMA_VERSION)

    def test_qty_base_and_unit_conversion(self):
        """Kiểm thử Bug 1: Quy đổi đơn vị và qtyBase chính xác"""
        # 1. Thêm sản phẩm mẫu
        self.db.conn.execute(
            "INSERT INTO products (id, name, defaultUnit) VALUES (101, 'Thuốc A', 'Hộp')"
        )
        # Quy đổi đơn vị: 1 Thùng = 10 Hộp, 1 Vỉ = 0.1 Hộp
        self.db.conn.execute(
            "INSERT INTO product_units (productId, unitCode, toBaseQty, price) VALUES (101, 'Thùng', 10, 1000)"
        )
        self.db.conn.execute(
            "INSERT INTO product_units (productId, unitCode, toBaseQty, price) VALUES (101, 'Vỉ', 0.1, 10)"
        )
        self.db.conn.commit()
        
        # 2. Ghi nhận phiếu nhập: 5 Thùng thuốc A
        items = [{
            "productId": 101,
            "qty": 5.0,
            "unitCode": "Thùng",
            "lotNo": "LOT001",
            "expiryDate": "2028-12-31",
            "cost": 1000.0,
            "fundSource": "Nguồn A"
        }]
        purchase_id, note_num, _ = self.db.record_purchase(items, "NCC Test", "Nhập kiểm thử", "Không")
        
        # Kiểm tra stock_movements có qtyBase = 5 * 10 = 50.0
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT qtyBase, qty, originalUnit FROM stock_movements WHERE referenceId=? AND referenceType='PURCHASE'", (purchase_id,))
        move = cursor.fetchone()
        self.assertIsNotNone(move)
        self.assertEqual(move[0], 50.0) # qtyBase = 50
        self.assertEqual(move[1], 5.0)  # qty = 5 (nhập 5 Thùng)
        
        # Kiểm tra tồn kho quy đổi từ stock_view()
        stock = self.db.stock_view()
        self.assertEqual(len(stock), 1)
        self.assertEqual(stock[0]['qtyBase'], 50.0)

    def test_fund_source_isolation_and_no_fallback(self):
        """Kiểm thử Bug 2: Cách ly nguồn kinh phí và không tự động fallback sang nguồn trống"""
        self.db.conn.execute("INSERT INTO products (id, name, defaultUnit) VALUES (102, 'Thuốc B', 'Viên')")
        self.db.conn.commit()
        # Đăng ký đơn vị cơ sở cho sản phẩm 102
        self.db.conn.execute("INSERT INTO product_units (productId, unitCode, toBaseQty, price) VALUES (102, 'Viên', 1.0, 0.0)")
        self.db.conn.commit()
        
        # Nhập 100 Viên nguồn "Chương trình A"
        self.db.record_purchase([{
            "productId": 102,
            "qty": 100.0,
            "unitCode": "Viên",
            "lotNo": "LOT002",
            "expiryDate": "2028-12-31",
            "cost": 500.0,
            "fundSource": "Chương trình A"
        }], "NCC Test", "Nhập", "Ghi chú")
        
        # Nhập 50 Viên nguồn "Chương trình B"
        self.db.record_purchase([{
            "productId": 102,
            "qty": 50.0,
            "unitCode": "Viên",
            "lotNo": "LOT002",
            "expiryDate": "2028-12-31",
            "cost": 500.0,
            "fundSource": "Chương trình B"
        }], "NCC Test", "Nhập", "Ghi chú")
        
        # Thử xuất 120 viên từ nguồn "Chương trình A" (Phải lỗi vì chỉ có 100 viên nguồn này)
        with self.assertRaises(Exception) as ctx:
            self.db.dispatch([{
                "productId": 102,
                "qty": 120.0,
                "unitCode": "Viên",
                "lotNo": "LOT002",
                "fundSource": "Chương trình A"
            }], "Đơn vị Test", "Xuất", "Ghi chú")
        self.assertIn("không đủ", str(ctx.exception).lower())
        
        # Thử xuất 80 viên từ nguồn rỗng/None (Phải lỗi vì không tự động fallback)
        with self.assertRaises(Exception) as ctx:
            self.db.dispatch([{
                "productId": 102,
                "qty": 10.0,
                "unitCode": "Viên",
                "lotNo": "LOT002",
                "fundSource": ""  # Hoặc None
            }], "Đơn vị Test", "Xuất", "Ghi chú")
        self.assertIn("không còn tồn kho", str(ctx.exception).lower())

    def test_batch_validation_same_lot_different_expiry(self):
        """Kiểm thử Bug 8: Validation lô hàng cùng số lô nhưng khác HSD"""
        self.db.conn.execute("INSERT INTO products (id, name, defaultUnit) VALUES (103, 'Thuốc C', 'Lọ')")
        self.db.conn.execute("INSERT INTO product_units (productId, unitCode, toBaseQty, price) VALUES (103, 'Lọ', 1.0, 0.0)")
        self.db.conn.commit()
        
        # Nhập lô LOT003, HSD 2027-12-31
        self.db.record_purchase([{
            "productId": 103,
            "qty": 10.0,
            "unitCode": "Lọ",
            "lotNo": "LOT003",
            "expiryDate": "2027-12-31",
            "cost": 100.0,
            "fundSource": "Nguồn A"
        }], "NCC Test", "Nhập", "")
        
        # Nhập tiếp cùng LOT003 nhưng HSD 2028-06-30 (Phải ném ra ngoại lệ ngăn chặn)
        with self.assertRaises(Exception) as ctx:
            self.db.record_purchase([{
                "productId": 103,
                "qty": 5.0,
                "unitCode": "Lọ",
                "lotNo": "LOT003",
                "expiryDate": "2028-06-30", # Khác HSD
                "cost": 100.0,
                "fundSource": "Nguồn A"
            }], "NCC Test", "Nhập", "")
        self.assertIn("không khớp HSD mới", str(ctx.exception))

    def test_unique_sequential_note_numbers(self):
        """Kiểm thử Bug 9: Số phiếu tăng dần tuần tự và duy nhất"""
        self.db.conn.execute("INSERT INTO products (id, name, defaultUnit) VALUES (104, 'Thuốc D', 'Hộp')")
        self.db.conn.execute("INSERT INTO product_units (productId, unitCode, toBaseQty, price) VALUES (104, 'Hộp', 1.0, 0.0)")
        self.db.conn.commit()
        
        # Nhập 2 phiếu khác nhau
        _, note_num1, _ = self.db.record_purchase([{
            "productId": 104, "qty": 1.0, "unitCode": "Hộp", "lotNo": "L1", "expiryDate": "2027-12-31", "cost": 1.0, "fundSource": "N"
        }], "NCC", "Nhập", "")
        
        _, note_num2, _ = self.db.record_purchase([{
            "productId": 104, "qty": 1.0, "unitCode": "Hộp", "lotNo": "L2", "expiryDate": "2027-12-31", "cost": 1.0, "fundSource": "N"
        }], "NCC", "Nhập", "")
        
        # Kiểm tra hai số phiếu khác nhau và có dạng PNxxx
        self.assertNotEqual(note_num1, note_num2)
        self.assertTrue(note_num1.startswith("PN"))
        self.assertTrue(note_num2.startswith("PN"))
        
        # Kiểm tra số thứ hai lớn hơn số thứ nhất
        num1 = int(note_num1.split("-")[-1])
        num2 = int(note_num2.split("-")[-1])
        self.assertEqual(num2, num1 + 1)

    def test_safe_backup_manager(self):
        """Kiểm thử Bug 4: Backup và restore SQLite an toàn"""
        backup_dir = os.path.join(self.temp_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        mgr = BackupManager(self.db_path, backup_dir)
        
        # 1. Viết dữ liệu mẫu
        self.db.conn.execute("INSERT INTO products (id, name, defaultUnit) VALUES (105, 'Thuốc E', 'Hộp')")
        self.db.conn.execute("INSERT INTO product_units (productId, unitCode, toBaseQty, price) VALUES (105, 'Hộp', 1.0, 0.0)")
        self.db.conn.commit()
        
        # 2. Tạo backup
        backup_path = mgr.create_backup("test")
        self.assertTrue(os.path.exists(backup_path))
        self.assertTrue(os.path.exists(backup_path.replace(".db", ".json"))) # Metadata file
        
        # 3. Sửa dữ liệu hiện tại
        self.db.conn.execute("DELETE FROM products WHERE id=105")
        self.db.conn.commit()
        
        # Kiểm tra dữ liệu đã mất
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE id=105")
        self.assertEqual(cursor.fetchone()[0], 0)
        
        # 4. Khôi phục từ backup
        # Trước tiên đóng kết nối hiện tại để tránh lock
        self.db.conn.close()
        
        success = mgr.restore_backup(backup_path)
        self.assertTrue(success)
        
        # Mở lại kết nối và kiểm tra dữ liệu đã được khôi phục
        self.db = DB(self.db_path)
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE id=105")
        self.assertEqual(cursor.fetchone()[0], 1)

    def test_export_import_json(self):
        """Kiểm thử Bug 5: Export/Import JSON Whitelisted, Transactional & FK check"""
        backup_dir = os.path.join(self.temp_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        mgr = BackupManager(self.db_path, backup_dir)
        
        # Tạo dữ liệu mẫu
        self.db.conn.execute("INSERT INTO products (id, name, defaultUnit) VALUES (106, 'Thuốc F', 'Hộp')")
        self.db.conn.execute("INSERT INTO product_units (productId, unitCode, toBaseQty, price) VALUES (106, 'Hộp', 1.0, 0.0)")
        self.db.conn.commit()
        
        # Export dữ liệu
        export_path = os.path.join(self.temp_dir, "export.json")
        mgr.export_data(export_path)
        self.assertTrue(os.path.exists(export_path))
        
        # Đọc file export kiểm tra có audit_logs và schema_version
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("export_info", data)
        self.assertIn("schema_version", data["export_info"])
        self.assertIn("audit_logs", data)
        
        # Import lại vào database khác hoặc dọn sạch rồi import
        self.db.conn.execute("DELETE FROM products")
        self.db.conn.commit()
        
        success = mgr.import_data(export_path)
        self.assertTrue(success)
        
        # Kiểm tra xem dữ liệu đã phục hồi
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM products WHERE id=106")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Thuốc F")

    def test_advanced_fefo_fund_source(self):
        """Kiểm thử Bug 2 nâng cao: FEFO bỏ qua lô không chứa nguồn kinh phí được chọn"""
        # Sản phẩm 201
        self.db.conn.execute("INSERT INTO products (id, name, defaultUnit) VALUES (201, 'Thuốc FEFO', 'Viên')")
        self.db.conn.execute("INSERT INTO product_units (productId, unitCode, toBaseQty, price) VALUES (201, 'Viên', 1.0, 0.0)")
        self.db.conn.commit()
        
        # Nhập lô 1 (Hết hạn sớm: 2027-12-31), nguồn B
        self.db.record_purchase([{
            "productId": 201,
            "qty": 50.0,
            "unitCode": "Viên",
            "lotNo": "LOT_FEFO_1",
            "expiryDate": "2027-12-31",
            "cost": 10.0,
            "fundSource": "Nguồn B"
        }], "NCC", "Nhập", "")
        
        # Nhập lô 2 (Hết hạn muộn: 2028-12-31), nguồn A
        self.db.record_purchase([{
            "productId": 201,
            "qty": 100.0,
            "unitCode": "Viên",
            "lotNo": "LOT_FEFO_2",
            "expiryDate": "2028-12-31",
            "cost": 10.0,
            "fundSource": "Nguồn A"
        }], "NCC", "Nhập", "")
        
        # Thử xuất 40 viên từ Nguồn A.
        # Lô 1 (hạn sớm) chỉ chứa Nguồn B. Lô 2 (hạn muộn) chứa Nguồn A.
        # FEFO phải bỏ qua Lô 1 và xuất thành công từ Lô 2 (Nguồn A).
        dispatch_id, note_num, details = self.db.dispatch([{
            "productId": 201,
            "qty": 40.0,
            "unitCode": "Viên",
            "fundSource": "Nguồn A"
        }], "Đơn vị nhận", "Xuất", "")
        
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]['lotNo'], 'LOT_FEFO_2')
        self.assertEqual(details[0]['qty'], 40.0)
        self.assertEqual(details[0]['fundSource'], 'Nguồn A')

    def test_restore_integrity_rollback(self):
        """Kiểm thử Bug 4 nâng cao: Khôi phục database lỗi tự động rollback về bản cũ"""
        backup_dir = os.path.join(self.temp_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        mgr = BackupManager(self.db_path, backup_dir)
        
        # 1. Ghi dữ liệu ban đầu
        self.db.conn.execute("INSERT INTO products (id, name, defaultUnit) VALUES (202, 'Thuốc R', 'Lọ')")
        self.db.conn.execute("INSERT INTO product_units (productId, unitCode, toBaseQty, price) VALUES (202, 'Lọ', 1.0, 0.0)")
        self.db.conn.commit()
        
        # 2. Tạo một file backup bị lỗi (file văn bản rác)
        corrupted_backup_path = os.path.join(backup_dir, "corrupted.db")
        with open(corrupted_backup_path, "w", encoding="utf-8") as f:
            f.write("Đây không phải là file SQLite hợp lệ!")
            
        # 3. Khôi phục từ file lỗi (Phải ném ra ngoại lệ và rollback về trạng thái ban đầu)
        with self.assertRaises(Exception):
            mgr.restore_backup(corrupted_backup_path)
            
        # 4. Mở lại DB, kiểm tra sản phẩm 202 vẫn tồn tại (khôi phục thành công trạng thái cũ)
        self.db = DB(self.db_path)
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE id=202")
        self.assertEqual(cursor.fetchone()[0], 1)

if __name__ == '__main__':
    unittest.main()
