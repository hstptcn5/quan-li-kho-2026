# database.py — Lớp cơ sở dữ liệu cho phần mềm Quản lý XNT
import sqlite3
import datetime as dt
from config import SCHEMA_SQL

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

        # Thêm các trường mới cho stock_movements (v2.0)
        if not self._has_column('stock_movements', 'receivingUnit'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN receivingUnit TEXT")
        if not self._has_column('stock_movements', 'reason'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN reason TEXT")

        # Thêm các trường mới cho products
        if not self._has_column('products', 'productType'):
            self.conn.execute("ALTER TABLE products ADD COLUMN productType TEXT DEFAULT 'thuoc'")
        if not self._has_column('products', 'registrationNumber'):
            self.conn.execute("ALTER TABLE products ADD COLUMN registrationNumber TEXT")

        # Migrate productType cũ: 'general' → 'thuoc', 'medicine' → 'thuoc'
        self.conn.execute("UPDATE products SET productType='thuoc' WHERE productType IN ('general', 'medicine')")

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

        if not self._has_column('dispatch_items', 'cost'):
            self.conn.execute("ALTER TABLE dispatch_items ADD COLUMN cost REAL DEFAULT 0")

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

    def expiring_view(self, days=180):
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
        - Xuất:  type IN ('SALE','DISCARD','DISPATCH')  (DISCARD và DISPATCH tính như xuất)
        - Đơn vị cơ sở (toBaseQty = 1)
        """
        sql = r'''
        SELECT
          p.id   AS productId,
          p.name AS productName,
          p.defaultUnit AS unit,
          b.lotNo AS lotNo,
          b.expiryDate AS expiryDate,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) < DATE(?) THEN sm.qty * 1
            ELSE 0 END), 4), 0) AS opening,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) BETWEEN DATE(?) AND DATE(?) AND sm.type='PURCHASE'
              THEN sm.qty * 1 ELSE 0 END), 4), 0) AS inbound,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) BETWEEN DATE(?) AND DATE(?) AND sm.type IN ('SALE','DISCARD','DISPATCH')
              THEN -sm.qty * 1 ELSE 0 END), 4), 0) AS outbound,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) <= DATE(?) THEN sm.qty * 1
            ELSE 0 END), 4), 0) AS closing
        FROM products p
        LEFT JOIN stock_movements sm ON sm.productId = p.id
        LEFT JOIN batches b ON sm.batchId = b.id
        GROUP BY p.id, p.name, b.id, b.lotNo, b.expiryDate
        HAVING opening <> 0 OR inbound <> 0 OR outbound <> 0 OR closing <> 0
        ORDER BY LOWER(p.name), b.expiryDate ASC
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

    # dispatch (Xuất kho / Cấp phát — FEFO)
    def dispatch(self, items, receiving_unit: str, reason: str = 'Cấp phát', note: str = '', date_str: str = None):
        """
        Xuất kho / cấp phát hàng theo FEFO.
        items: list of {'productId', 'unitCode', 'qty'}
        receiving_unit: tên đơn vị nhận (VD: TYT Phường X)
        reason: Cấp phát / Hủy / Chuyển kho
        date_str: Ngày xuất tùy chọn (dạng YYYY-MM-DD), nếu None thì lấy thời gian hiện tại
        """
        dispatch_details = []
        try:
            self.conn.execute("BEGIN")

            # Thời gian tạo phiếu xuất
            if date_str:
                created_at = f"{date_str} {dt.datetime.now().strftime('%H:%M:%S')}"
            else:
                created_at = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Tạo phiếu xuất kho
            note_number = f"PX-{dt.datetime.now().strftime('%y%m%d%H%M%S')}"
            cur = self.conn.execute(
                "INSERT INTO dispatch_notes(noteNumber, receivingUnit, reason, note, createdAt) VALUES(?,?,?,?,?)",
                (note_number, receiving_unit, reason, note, created_at)
            )
            dispatch_id = cur.lastrowid

            for it in items:
                to_base, _ = self.unit_info(it['productId'], it['unitCode'])
                if to_base is None:
                    raise Exception(f"Sản phẩm #{it['productId']} chưa có đơn vị cơ sở")
                need_base = float(it['qty']) * to_base

                # Lấy lô hàng: thủ công nếu chọn trước, hoặc FEFO nếu để tự động
                if it.get('lotNo'):
                    lots = self.q('''
                      SELECT v.batchId, v.qtyBase, b.expiryDate, b.lotNo,
                             COALESCE((
                                 SELECT sm2.cost FROM stock_movements sm2
                                 WHERE sm2.productId=v.productId AND sm2.batchId=v.batchId
                                   AND sm2.type='PURCHASE' AND sm2.cost IS NOT NULL
                                 ORDER BY sm2.id DESC LIMIT 1
                             ), 0) AS costBase
                      FROM (
                        SELECT sm.productId, sm.batchId, SUM(sm.qty*1) AS qtyBase
                        FROM stock_movements sm 
                        WHERE sm.productId=? AND sm.batchId=(
                            SELECT id FROM batches WHERE productId=? AND lotNo=? LIMIT 1
                        )
                        GROUP BY sm.batchId
                      ) v JOIN batches b ON b.id=v.batchId
                    ''', (it['productId'], it['productId'], it['lotNo']))
                else:
                    lots = self.q('''
                      SELECT v.batchId, v.qtyBase, b.expiryDate, b.lotNo,
                             COALESCE((
                                 SELECT sm2.cost FROM stock_movements sm2
                                 WHERE sm2.productId=v.productId AND sm2.batchId=v.batchId
                                   AND sm2.type='PURCHASE' AND sm2.cost IS NOT NULL
                                 ORDER BY sm2.id DESC LIMIT 1
                             ), 0) AS costBase
                      FROM (
                        SELECT sm.productId, sm.batchId, SUM(sm.qty*1) AS qtyBase
                        FROM stock_movements sm WHERE sm.productId=? GROUP BY sm.batchId
                      ) v JOIN batches b ON b.id=v.batchId
                      WHERE v.qtyBase>0 AND DATE(b.expiryDate) >= DATE('now')
                      ORDER BY DATE(b.expiryDate)
                    ''', (it['productId'],))

                for lot in lots:
                    if need_base <= 0:
                        break
                    take_base = min(need_base, float(lot['qtyBase']))
                    take_in_unit = take_base / to_base
                    cost_in_unit = float(lot['costBase']) * to_base
                    self.conn.execute(
                        "INSERT INTO stock_movements(productId, batchId, unitCode, qty, type, cost, receivingUnit, reason, createdAt) VALUES(?,?,?,?, 'DISPATCH', ?,?,?,?)",
                        (it['productId'], lot['batchId'], it['unitCode'], -take_in_unit, cost_in_unit, receiving_unit, reason, created_at)
                    )
                    # Ghi chi tiết phiếu xuất
                    self.conn.execute(
                        "INSERT INTO dispatch_items(dispatchId, productId, batchId, unitCode, qty, lotNo, expiryDate, cost) VALUES(?,?,?,?,?,?,?,?)",
                        (dispatch_id, it['productId'], lot['batchId'], it['unitCode'], take_in_unit, lot['lotNo'], lot['expiryDate'], cost_in_unit)
                    )
                    dispatch_details.append({
                        'productId': it['productId'],
                        'productName': it.get('productName', f"#{it['productId']}"),
                        'unitCode': it['unitCode'],
                        'qty': take_in_unit,
                        'lotNo': lot['lotNo'],
                        'expiryDate': lot['expiryDate'],
                        'batchId': lot['batchId'],
                        'cost': cost_in_unit
                    })
                    need_base -= take_base

                if need_base > 0:
                    raise Exception(f"Không đủ tồn kho cho sản phẩm #{it['productId']}")

            # Lưu đơn vị nhận vào bảng receiving_units (nếu chưa có)
            self._save_receiving_unit(receiving_unit)

            self.conn.commit()
            return dispatch_id, note_number, dispatch_details

        except Exception:
            self.conn.rollback()
            raise

    def _save_receiving_unit(self, name: str):
        """Lưu đơn vị nhận mới (nếu chưa có) để autocomplete lần sau"""
        if not name or not name.strip():
            return
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO receiving_units(name) VALUES(?)",
                (name.strip(),)
            )
        except Exception:
            pass

    def get_receiving_units(self):
        """Lấy danh sách đơn vị nhận đã lưu"""
        return [r['name'] for r in self.q("SELECT name FROM receiving_units ORDER BY name")]

    def get_dispatch_notes(self, start_date: str = None, end_date: str = None):
        """Lấy danh sách phiếu xuất kho"""
        if start_date and end_date:
            return self.q('''
                SELECT dn.*, COUNT(di.id) as item_count
                FROM dispatch_notes dn
                LEFT JOIN dispatch_items di ON di.dispatchId = dn.id
                WHERE DATE(dn.createdAt) BETWEEN DATE(?) AND DATE(?)
                GROUP BY dn.id
                ORDER BY dn.createdAt DESC
            ''', (start_date, end_date))
        return self.q('''
            SELECT dn.*, COUNT(di.id) as item_count
            FROM dispatch_notes dn
            LEFT JOIN dispatch_items di ON di.dispatchId = dn.id
            GROUP BY dn.id
            ORDER BY dn.createdAt DESC
            LIMIT 50
        ''')

    def get_dispatch_detail(self, dispatch_id: int):
        """Lấy chi tiết phiếu xuất kho"""
        return self.q('''
            SELECT di.*, p.name as productName
            FROM dispatch_items di
            JOIN products p ON p.id = di.productId
            WHERE di.dispatchId = ?
            ORDER BY p.name
        ''', (dispatch_id,))

    # purchase (Nhập kho)
    def record_purchase(self, items, supplier: str, reason: str = 'Nhập kho', note: str = '', date_str: str = None):
        """
        Nhập kho thuốc, vaccine, VTYT và lưu phiếu nhập.
        items: list of {'productId', 'unitCode', 'qty', 'lotNo', 'expiryDate', 'cost'}
        """
        purchase_details = []
        try:
            self.conn.execute("BEGIN")

            # Thời gian tạo phiếu nhập
            if date_str:
                created_at = f"{date_str} {dt.datetime.now().strftime('%H:%M:%S')}"
            else:
                created_at = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Tạo số phiếu nhập
            note_number = f"PN-{dt.datetime.now().strftime('%y%m%d%H%M%S')}"
            cur = self.conn.execute(
                "INSERT INTO purchase_notes(noteNumber, supplier, reason, note, createdAt) VALUES(?,?,?,?,?)",
                (note_number, supplier, reason, note, created_at)
            )
            purchase_id = cur.lastrowid

            for it in items:
                # Bảo đảm lô hàng tồn tại
                bid = self.ensure_batch(it['productId'], it['lotNo'], it['expiryDate'])
                
                # Ghi chuyển động kho
                self.conn.execute(
                    "INSERT INTO stock_movements(productId, batchId, unitCode, qty, type, cost, receivingUnit, reason, createdAt) VALUES(?,?,?,?, 'PURCHASE', ?,?,?,?)",
                    (it['productId'], bid, it['unitCode'], float(it['qty']), float(it.get('cost') or 0), supplier, reason, created_at)
                )
                
                # Ghi chi tiết phiếu nhập
                self.conn.execute(
                    "INSERT INTO purchase_items(purchaseId, productId, batchId, unitCode, qty, lotNo, expiryDate, cost) VALUES(?,?,?,?,?,?,?,?)",
                    (purchase_id, it['productId'], bid, it['unitCode'], float(it['qty']), it['lotNo'], it['expiryDate'], float(it.get('cost') or 0))
                )
                
                # Đồng bộ giá bán base = giá nhập
                self.conn.execute(
                    "UPDATE product_units SET price=? WHERE productId=? AND unitCode=?",
                    (float(it.get('cost') or 0), it['productId'], it['unitCode'])
                )
                
                purchase_details.append({
                    'productId': it['productId'],
                    'productName': it.get('productName', f"#{it['productId']}"),
                    'unitCode': it['unitCode'],
                    'qty': float(it['qty']),
                    'lotNo': it['lotNo'],
                    'expiryDate': it['expiryDate'],
                    'cost': float(it.get('cost') or 0),
                    'batchId': bid
                })

            self.conn.commit()
            return purchase_id, note_number, purchase_details

        except Exception:
            self.conn.rollback()
            raise

    def get_purchase_notes(self, start_date: str = None, end_date: str = None):
        """Lấy danh sách phiếu nhập kho"""
        if start_date and end_date:
            return self.q('''
                SELECT pn.*, COUNT(pi.id) as item_count
                FROM purchase_notes pn
                LEFT JOIN purchase_items pi ON pi.purchaseId = pn.id
                WHERE DATE(pn.createdAt) BETWEEN DATE(?) AND DATE(?)
                GROUP BY pn.id
                ORDER BY pn.createdAt DESC
            ''', (start_date, end_date))
        return self.q('''
            SELECT pn.*, COUNT(pi.id) as item_count
            FROM purchase_notes pn
            LEFT JOIN purchase_items pi ON pi.purchaseId = pn.id
            GROUP BY pn.id
            ORDER BY pn.createdAt DESC
            LIMIT 50
        ''')

    def get_purchase_detail(self, purchase_id: int):
        """Lấy chi tiết phiếu nhập kho"""
        return self.q('''
            SELECT pi.*, p.name as productName
            FROM purchase_items pi
            JOIN products p ON p.id = pi.productId
            WHERE pi.purchaseId = ?
            ORDER BY p.name
        ''', (purchase_id,)) # Fix possible reference error in legacy SQL

    def get_suppliers(self):
        """Lấy danh sách nhà cung cấp đã từng nhập hàng"""
        rows = self.q("SELECT DISTINCT supplier FROM purchase_notes WHERE supplier != '' ORDER BY supplier")
        return [r['supplier'] for r in rows]

    # ---------------- Temperature Logs ----------------
    def add_temperature_log(self, log_date: str, session: str, location_name: str, temp: float, humidity: float, recorded_by: str):
        """Thêm hoặc cập nhật nhật ký nhiệt độ/độ ẩm"""
        return self.ex('''
            INSERT OR REPLACE INTO temperature_logs (logDate, session, locationName, temperature, humidity, recordedBy)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (log_date, session, location_name, temp, humidity, recorded_by))

    def get_temperature_logs(self, month_str: str = None, location_name: str = None):
        """Lấy danh sách nhật ký nhiệt độ lọc theo tháng (YYYY-MM) và vị trí"""
        sql = "SELECT * FROM temperature_logs WHERE 1=1"
        params = []
        if month_str:
            sql += " AND strftime('%Y-%m', logDate) = ?"
            params.append(month_str)
        if location_name and location_name != "Tất cả":
            sql += " AND locationName = ?"
            params.append(location_name)
        sql += " ORDER BY logDate DESC, case session when 'Sáng' then 1 else 2 end DESC"
        return self.q(sql, tuple(params))

    def delete_temperature_log(self, log_id: int):
        """Xóa một bản ghi nhật ký nhiệt độ"""
        self.ex("DELETE FROM temperature_logs WHERE id = ?", (log_id,))

    def get_temperature_locations(self):
        """Lấy danh sách các vị trí đã từng ghi nhận nhiệt độ"""
        rows = self.q("SELECT DISTINCT locationName FROM temperature_logs ORDER BY locationName")
        return [r['locationName'] for r in rows]

