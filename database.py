# database.py — Lớp cơ sở dữ liệu cho phần mềm Quản lý XNT
import sqlite3
import datetime as dt
from config import SCHEMA_SQL, SCHEMA_VERSION

class DB:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.executescript(SCHEMA_SQL)
        self.conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

        try: self.conn.execute("ALTER TABLE products ADD COLUMN barcode TEXT")
        except sqlite3.OperationalError: pass

        self.migrate_schema()

        self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode) WHERE barcode IS NOT NULL")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sm_product_batch ON stock_movements(productId, batchId)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_batches_product ON batches(productId)")
        self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_units_unique ON product_units(productId, unitCode)")
        self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_purchase_notenum ON purchase_notes(noteNumber)")
        self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dispatch_notenum ON dispatch_notes(noteNumber)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sm_reference ON stock_movements(referenceType, referenceId)")
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
        if not self._has_column('stock_movements', 'fundSource'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN fundSource TEXT")

        # === Lỗi 1: Thêm cột qtyBase, originalQty, originalUnit ===
        if not self._has_column('stock_movements', 'qtyBase'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN qtyBase REAL")
        if not self._has_column('stock_movements', 'originalQty'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN originalQty REAL")
        if not self._has_column('stock_movements', 'originalUnit'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN originalUnit TEXT")

        # === Lỗi 6: Thêm cột reference liên kết chứng từ ===
        if not self._has_column('stock_movements', 'referenceType'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN referenceType TEXT")
        if not self._has_column('stock_movements', 'referenceId'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN referenceId INTEGER")
        if not self._has_column('stock_movements', 'referenceItemId'):
            self.conn.execute("ALTER TABLE stock_movements ADD COLUMN referenceItemId INTEGER")

        # Thêm cột nguồn kinh phí cho purchase_items (v2.1)
        if not self._has_column('purchase_items', 'fundSource'):
            self.conn.execute("ALTER TABLE purchase_items ADD COLUMN fundSource TEXT")

        # Thêm cột nguồn kinh phí cho dispatch_items (v2.2)
        if not self._has_column('dispatch_items', 'fundSource'):
            self.conn.execute("ALTER TABLE dispatch_items ADD COLUMN fundSource TEXT")

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

        # === Lỗi 1: Migration dữ liệu cũ — gán qtyBase cho bản ghi hiện có ===
        self.conn.execute('''
            UPDATE stock_movements
            SET originalQty = CASE WHEN originalQty IS NULL THEN ABS(qty) ELSE originalQty END,
                originalUnit = CASE WHEN originalUnit IS NULL THEN unitCode ELSE originalUnit END,
                qtyBase = CASE WHEN qtyBase IS NULL THEN qty * COALESCE(
                    (SELECT pu.toBaseQty FROM product_units pu
                     WHERE pu.productId = stock_movements.productId
                       AND pu.unitCode = stock_movements.unitCode), 1)
                ELSE qtyBase END
            WHERE qtyBase IS NULL
        ''')

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

    def add_audit_log(self, action: str, note_id: int = None, details: str = None, ip: str = "Local"):
        """Ghi nhận nhật ký kiểm toán (Audit Log)"""
        try:
            # Dùng một connection riêng biệt hoặc self.conn trực tiếp
            # Vì log này ghi ngay lập tức không phụ thuộc transaction của nghiệp vụ chính
            # Nên chúng ta commit trực tiếp qua self.ex
            self.ex(
                "INSERT INTO audit_logs (ip, action, noteId, details) VALUES (?, ?, ?, ?)",
                (ip, action, note_id, details)
            )
        except Exception as e:
            print(f"Lỗi ghi audit log: {e}")

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
               ROUND(SUM(COALESCE(sm.qtyBase, sm.qty)),4) AS qtyBase,
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
                    ORDER BY sm3.id DESC LIMIT 1) * SUM(COALESCE(sm.qtyBase, sm.qty))
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
                   ROUND(SUM(COALESCE(sm.qtyBase, sm.qty)),4) AS qtyBase
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
        FROM ( SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
               FROM stock_movements sm GROUP BY sm.productId, sm.batchId ) v
        JOIN products p ON p.id=v.productId
        GROUP BY p.id, p.name HAVING qtyBaseTotal<>0
        ORDER BY LOWER(p.name)
        '''
        return self.q(sql)

    def xnt_report(self, start_date: str, end_date: str, fund_source: str = None):
        """
        Báo cáo Xuất–Nhập–Tồn theo sản phẩm trong khoảng ngày [start_date, end_date].
        - Nhập:  type='PURCHASE'
        - Xuất:  type IN ('SALE','DISCARD','DISPATCH')  (DISCARD và DISPATCH tính như xuất)
        - Sử dụng COALESCE(qtyBase, qty) để tương thích dữ liệu cũ
        - fund_source: lọc theo nguồn kinh phí (None hoặc 'Tất cả' = không lọc)
        """
        fund_filter = ""
        extra_params = []
        if fund_source and fund_source != 'Tất cả':
            fund_filter = " AND sm.fundSource = ?"
            extra_params = [fund_source] * 4  # Dùng trong 4 mệnh đề CASE

        sql = f'''
        SELECT
          p.id   AS productId,
          p.name AS productName,
          p.defaultUnit AS unit,
          b.lotNo AS lotNo,
          b.expiryDate AS expiryDate,
          COALESCE(sm.fundSource, '') AS fundSource,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) < DATE(?){fund_filter} THEN COALESCE(sm.qtyBase, sm.qty)
            ELSE 0 END), 4), 0) AS opening,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) BETWEEN DATE(?) AND DATE(?) AND sm.type='PURCHASE'{fund_filter}
              THEN COALESCE(sm.qtyBase, sm.qty) ELSE 0 END), 4), 0) AS inbound,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) BETWEEN DATE(?) AND DATE(?) AND sm.type IN ('SALE','DISCARD','DISPATCH'){fund_filter}
              THEN -COALESCE(sm.qtyBase, sm.qty) ELSE 0 END), 4), 0) AS outbound,

          COALESCE(ROUND(SUM(CASE
            WHEN DATE(sm.createdAt) <= DATE(?){fund_filter} THEN COALESCE(sm.qtyBase, sm.qty)
            ELSE 0 END), 4), 0) AS closing
        FROM products p
        LEFT JOIN stock_movements sm ON sm.productId = p.id
        LEFT JOIN batches b ON sm.batchId = b.id
        GROUP BY p.id, p.name, b.id, b.lotNo, b.expiryDate, COALESCE(sm.fundSource, '')
        HAVING opening <> 0 OR inbound <> 0 OR outbound <> 0 OR closing <> 0
        ORDER BY LOWER(p.name), b.expiryDate ASC
        '''
        if fund_source and fund_source != 'Tất cả':
            params = [
                start_date, fund_source,
                start_date, end_date, fund_source,
                start_date, end_date, fund_source,
                end_date, fund_source
            ]
        else:
            params = [start_date, start_date, end_date, start_date, end_date, end_date]
        return self.q(sql, tuple(params))

    def stock_summary_by_product_range(self, start_date: str, end_date: str):
        """
        Tồn theo sản phẩm trong khoảng thời gian (lọc theo createdAt của stock_movements).
        """
        sql = '''
        SELECT p.id AS productId, p.name AS productName,
               ROUND(SUM(v.qtyBase), 4) AS qtyBaseTotal
        FROM (
          SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
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

    def validate_batch(self, product_id, lot_no, expiry_date):
        """Lỗi Lô hàng (Atomic Excel) — Chỉ kiểm tra tính hợp lệ mà KHÔNG chèn bản ghi vào DB"""
        r = self.q("SELECT expiryDate FROM batches WHERE productId=? AND lotNo=?", (product_id, lot_no))
        if r:
            if r[0]['expiryDate'] != expiry_date:
                raise ValueError(
                    f"Số lô '{lot_no}' đã tồn tại với HSD {r[0]['expiryDate']}, "
                    f"không khớp {expiry_date}"
                )

    def ensure_batch(self, product_id, lot_no, expiry_date):
        """Validate và lấy/tạo lô hàng mà không tự động commit transaction dở dang."""
        r = self.q("SELECT id, expiryDate FROM batches WHERE productId=? AND lotNo=?", (product_id, lot_no))
        if r:
            if r[0]['expiryDate'] != expiry_date:
                raise ValueError(
                    f"Số lô '{lot_no}' đã tồn tại với HSD {r[0]['expiryDate']}, "
                    f"không khớp HSD mới {expiry_date}."
                )
            return r[0]['id']
        cur = self.conn.execute("INSERT INTO batches(productId, lotNo, expiryDate) VALUES(?,?,?)", (product_id, lot_no, expiry_date))
        return cur.lastrowid

    def _assert_no_negative_stock(self):
        """Kiểm tra bất biến: Tồn kho của bất kỳ sản phẩm, lô hàng và nguồn kinh phí nào không bao giờ bị âm."""
        negative_rows = self.q("""
            SELECT productId, batchId, COALESCE(fundSource, '') AS fundSource,
                   SUM(COALESCE(qtyBase, qty)) AS balance
            FROM stock_movements
            GROUP BY productId, batchId, COALESCE(fundSource, '')
            HAVING balance < -0.0001
        """)
        if negative_rows:
            raise ValueError(f"Phát hiện tồn kho âm không hợp lệ trong hệ thống: {negative_rows}")

    # purchase
    def add_purchase(self, items):
        """Legacy purchase — cũng cần ghi qtyBase"""
        try:
            self.conn.execute("BEGIN")
            for it in items:
                bid = self.ensure_batch(it['productId'], it['lotNo'], it['expiryDate'])
                to_base, _ = self.unit_info(it['productId'], it['unitCode'])
                if to_base is None:
                    to_base = 1.0
                qty_base = float(it['qty']) * to_base
                self.conn.execute(
                    "INSERT INTO stock_movements(productId, batchId, unitCode, qty, qtyBase, originalQty, originalUnit, type, cost) VALUES(?,?,?,?,?,?,?, 'PURCHASE', ?)",
                    (it['productId'], bid, it['unitCode'], float(it['qty']), qty_base, float(it['qty']), it['unitCode'], float(it.get('cost') or 0))
                )
            self._assert_no_negative_stock()
            self.conn.commit()
        except Exception:
            self.conn.rollback(); raise

    # sell (FEFO)
    def sell(self, items):
        """Lỗi 1+2: Sử dụng qtyBase, bỏ fallback nguồn rỗng"""
        total = 0.0
        for it in items:
            to_base, unit_price = self.unit_info(it['productId'], it['unitCode'])
            if to_base is None: raise Exception('Sản phẩm chưa có giá/đơn vị cơ sở')
            need_base = float(it['qty']) * to_base
            lots = self.q('''
              SELECT v.batchId, v.qtyBase, b.expiryDate FROM (
                SELECT sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                FROM stock_movements sm WHERE sm.productId=? GROUP BY sm.batchId
              ) v JOIN batches b ON b.id=v.batchId
              WHERE v.qtyBase>0 AND DATE(b.expiryDate) >= DATE('now')
              ORDER BY DATE(b.expiryDate)
            ''', (it['productId'],))
            for lot in lots:
                if need_base <= 0: break
                take_base = min(need_base, float(lot['qtyBase']))
                
                # Tìm các nguồn kinh phí khả dụng của lô hàng này
                funds_avail = self.q('''
                    SELECT fundSource, SUM(COALESCE(qtyBase, qty)) AS qb
                    FROM stock_movements
                    WHERE productId=? AND batchId=?
                    GROUP BY fundSource
                    HAVING qb > 0
                ''', (it['productId'], lot['batchId']))
                
                if not funds_avail:
                    raise Exception(f"Lô hàng #{lot['batchId']} không còn nguồn kinh phí khả dụng")
                
                lot_need_base = take_base
                for fa in funds_avail:
                    if lot_need_base <= 0:
                        break
                    fa_qty = float(fa['qb'])
                    take_fa = min(lot_need_base, fa_qty)
                    fund_name = fa['fundSource'] or ''
                    
                    self.conn.execute(
                        "INSERT INTO stock_movements(productId, batchId, unitCode, qty, qtyBase, originalQty, originalUnit, type, fundSource) VALUES(?,?,?,?,?,?,?, 'SALE', ?)",
                        (it['productId'], lot['batchId'], it['unitCode'], -take_fa / to_base, -take_fa, float(it['qty']), it['unitCode'], fund_name)
                    )
                    lot_need_base -= take_fa

                if lot_need_base > 0.001:
                    raise Exception(f"Nguồn kinh phí không đủ cho lô hàng #{lot['batchId']}, còn thiếu {lot_need_base:.4f} đơn vị cơ sở")
                
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
            self._assert_no_negative_stock()
            self.conn.commit()
            return sale_id, finalized, total, change
        except Exception:
            self.conn.rollback(); raise

    # dispatch (Xuất kho / Cấp phát — FEFO)
    def _next_note_number(self, prefix):
        """Lỗi 9: Sinh số phiếu tuần tự dạng PN-2026-000001 / PX-2026-000001"""
        year = dt.datetime.now().strftime('%Y')
        table = 'purchase_notes' if prefix == 'PN' else 'dispatch_notes'
        row = self.q(
            f"SELECT noteNumber FROM {table} WHERE noteNumber LIKE ? ORDER BY noteNumber DESC LIMIT 1",
            (f"{prefix}-{year}-%",)
        )
        if row:
            try:
                last_seq = int(row[0]['noteNumber'].split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
        return f"{prefix}-{year}-{next_seq:06d}"

    def dispatch(self, items, receiving_unit: str, reason: str = 'Cấp phát', note: str = '', date_str: str = None, audit_ip: str = 'Local'):
        """
        Xuất kho / cấp phát hàng theo FEFO.
        Lỗi 1: Sử dụng qtyBase cho mọi tính toán
        Lỗi 2: Bỏ fallback nguồn rỗng, validate nguồn kinh phí
        Lỗi 6: Ghi referenceType/Id/ItemId liên kết chứng từ
        Lỗi 9: Số phiếu tuần tự unique
        """
        dispatch_details = []
        try:
            self.conn.execute("BEGIN")

            # Thời gian tạo phiếu xuất
            if date_str:
                created_at = f"{date_str} {dt.datetime.now().strftime('%H:%M:%S')}"
            else:
                created_at = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Lỗi 9: Tạo số phiếu tuần tự
            note_number = self._next_note_number('PX')
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
                original_qty = float(it['qty'])
                original_unit = it['unitCode']

                # Lấy lô hàng: thủ công nếu chọn trước, hoặc FEFO nếu để tự động
                fund_source_val = it.get('fundSource')
                if it.get('lotNo'):
                    if fund_source_val is not None:
                        lots = self.q('''
                          SELECT v.batchId, v.qtyBase, b.expiryDate, b.lotNo,
                                 COALESCE((
                                     SELECT sm2.cost FROM stock_movements sm2
                                     WHERE sm2.productId=v.productId AND sm2.batchId=v.batchId
                                       AND sm2.type='PURCHASE' AND sm2.cost IS NOT NULL
                                     ORDER BY sm2.id DESC LIMIT 1
                                 ), 0) AS costBase
                          FROM (
                            SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                            FROM stock_movements sm 
                            WHERE sm.productId=? AND sm.batchId=(
                                SELECT id FROM batches WHERE productId=? AND lotNo=? LIMIT 1
                            ) AND COALESCE(sm.fundSource, '')=?
                            GROUP BY sm.batchId
                          ) v JOIN batches b ON b.id=v.batchId
                        ''', (it['productId'], it['productId'], it['lotNo'], fund_source_val))
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
                            SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                            FROM stock_movements sm 
                            WHERE sm.productId=? AND sm.batchId=(
                                SELECT id FROM batches WHERE productId=? AND lotNo=? LIMIT 1
                            )
                            GROUP BY sm.batchId
                          ) v JOIN batches b ON b.id=v.batchId
                        ''', (it['productId'], it['productId'], it['lotNo']))
                else:
                    if fund_source_val is not None:
                        lots = self.q('''
                          SELECT v.batchId, v.qtyBase, b.expiryDate, b.lotNo,
                                 COALESCE((
                                     SELECT sm2.cost FROM stock_movements sm2
                                     WHERE sm2.productId=v.productId AND sm2.batchId=v.batchId
                                       AND sm2.type='PURCHASE' AND sm2.cost IS NOT NULL
                                     ORDER BY sm2.id DESC LIMIT 1
                                 ), 0) AS costBase
                          FROM (
                            SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                            FROM stock_movements sm 
                            WHERE sm.productId=? AND COALESCE(sm.fundSource, '')=?
                            GROUP BY sm.batchId
                          ) v JOIN batches b ON b.id=v.batchId
                          WHERE v.qtyBase>0 AND DATE(b.expiryDate) >= DATE('now')
                          ORDER BY DATE(b.expiryDate)
                        ''', (it['productId'], fund_source_val))
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
                            SELECT sm.productId, sm.batchId, SUM(COALESCE(sm.qtyBase, sm.qty)) AS qtyBase
                            FROM stock_movements sm WHERE sm.productId=? GROUP BY sm.batchId
                          ) v JOIN batches b ON b.id=v.batchId
                          WHERE v.qtyBase>0 AND DATE(b.expiryDate) >= DATE('now')
                          ORDER BY DATE(b.expiryDate)
                        ''', (it['productId'],))

                for lot in lots:
                    if need_base <= 0:
                        break
                    take_base = min(need_base, float(lot['qtyBase']))
                    
                    # Lỗi 2: Tìm nguồn kinh phí — không fallback nguồn rỗng
                    if it.get('fundSource') is not None:
                        funds_avail = self.q('''
                            SELECT fundSource, SUM(COALESCE(qtyBase, qty)) AS qb
                            FROM stock_movements
                            WHERE productId=? AND batchId=? AND COALESCE(fundSource, '')=?
                            GROUP BY fundSource
                            HAVING qb > 0
                        ''', (it['productId'], lot['batchId'], it['fundSource']))
                        if not funds_avail:
                            fund_label = it['fundSource'] or '(không rõ)'
                            raise Exception(
                                f"Nguồn '{fund_label}' không còn tồn kho cho sản phẩm #{it['productId']}, lô {lot['lotNo']}"
                            )
                    else:
                        funds_avail = self.q('''
                            SELECT fundSource, SUM(COALESCE(qtyBase, qty)) AS qb
                            FROM stock_movements
                            WHERE productId=? AND batchId=?
                            GROUP BY fundSource
                            HAVING qb > 0
                        ''', (it['productId'], lot['batchId']))
                    
                    if not funds_avail:
                        raise Exception(f"Lô {lot['lotNo']} không còn nguồn kinh phí khả dụng")
                    
                    lot_need_base = take_base
                    for fa in funds_avail:
                        if lot_need_base <= 0:
                            break
                        fa_qty = float(fa['qb'])
                        take_fa = min(lot_need_base, fa_qty)
                        take_fa_in_unit = take_fa / to_base
                        cost_fa_in_unit = float(lot['costBase']) * to_base
                        fund_name = fa['fundSource'] or ''
                        
                        # Lỗi 6: Ghi dispatch_items trước để lấy ID
                        di_cur = self.conn.execute(
                            "INSERT INTO dispatch_items(dispatchId, productId, batchId, unitCode, qty, lotNo, expiryDate, cost, fundSource) VALUES(?,?,?,?,?,?,?,?,?)",
                            (dispatch_id, it['productId'], lot['batchId'], it['unitCode'], take_fa_in_unit, lot['lotNo'], lot['expiryDate'], cost_fa_in_unit, fund_name)
                        )
                        dispatch_item_id = di_cur.lastrowid
                        
                        # Lỗi 1+6: Ghi stock_movements với qtyBase và referenceId
                        self.conn.execute(
                            """INSERT INTO stock_movements(
                                productId, batchId, unitCode, qty, qtyBase, originalQty, originalUnit,
                                type, cost, receivingUnit, reason, fundSource,
                                referenceType, referenceId, referenceItemId, createdAt
                            ) VALUES(?,?,?,?,?,?,?, 'DISPATCH', ?,?,?,?,  'DISPATCH',?,?,?)""",
                            (it['productId'], lot['batchId'], it['unitCode'], -take_fa_in_unit, -take_fa, original_qty, original_unit,
                             cost_fa_in_unit, receiving_unit, reason, fund_name,
                             dispatch_id, dispatch_item_id, created_at)
                        )
                        dispatch_details.append({
                            'productId': it['productId'],
                            'productName': it.get('productName', f"#{it['productId']}"),
                            'unitCode': it['unitCode'],
                            'qty': take_fa_in_unit,
                            'lotNo': lot['lotNo'],
                            'expiryDate': lot['expiryDate'],
                            'batchId': lot['batchId'],
                            'cost': cost_fa_in_unit,
                            'fundSource': fund_name
                        })
                        lot_need_base -= take_fa

                    if lot_need_base > 0.001:
                        raise Exception(
                            f"Nguồn kinh phí không đủ cho sản phẩm #{it['productId']}, lô {lot['lotNo']}. "
                            f"Còn thiếu {lot_need_base:.4f} đơn vị cơ sở"
                        )
                        
                    need_base -= take_base

                if need_base > 0:
                    raise Exception(f"Không đủ tồn kho cho sản phẩm #{it['productId']}")

            # Lưu đơn vị nhận vào bảng receiving_units (nếu chưa có)
            self._save_receiving_unit(receiving_unit)

            self._assert_no_negative_stock()
            self.conn.commit()
            try:
                self.add_audit_log(
                    action="XUAT_KHO",
                    note_id=dispatch_id,
                    details=f"Xuất kho thành công, số phiếu: {note_number}, đơn vị nhận: {receiving_unit}, số mặt hàng: {len(items)}",
                    ip=audit_ip
                )
            except Exception as log_err:
                print(f"Lỗi ghi log xuat kho: {log_err}")
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
    def record_purchase(self, items, supplier: str, reason: str = 'Nhập kho', note: str = '', date_str: str = None, audit_ip: str = 'Local'):
        """
        Nhập kho thuốc, vaccine, VTYT và lưu phiếu nhập.
        Lỗi 1: Ghi qtyBase, originalQty, originalUnit
        Lỗi 6: Ghi referenceType/Id/ItemId
        Lỗi 9: Số phiếu tuần tự unique
        """
        purchase_details = []
        try:
            self.conn.execute("BEGIN")

            # Thời gian tạo phiếu nhập
            if date_str:
                created_at = f"{date_str} {dt.datetime.now().strftime('%H:%M:%S')}"
            else:
                created_at = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Lỗi 9: Tạo số phiếu nhập tuần tự
            note_number = self._next_note_number('PN')
            cur = self.conn.execute(
                "INSERT INTO purchase_notes(noteNumber, supplier, reason, note, createdAt) VALUES(?,?,?,?,?)",
                (note_number, supplier, reason, note, created_at)
            )
            purchase_id = cur.lastrowid

            for it in items:
                # Bảo đảm lô hàng tồn tại (Lỗi 8: validate HSD)
                bid = self.ensure_batch(it['productId'], it['lotNo'], it['expiryDate'])
                fund_src = it.get('fundSource') or ''
                
                # Lỗi 1: Tính qtyBase
                to_base, _ = self.unit_info(it['productId'], it['unitCode'])
                if to_base is None:
                    to_base = 1.0
                qty_val = float(it['qty'])
                qty_base = qty_val * to_base
                
                # Lỗi 6: Ghi purchase_items trước để lấy ID
                pi_cur = self.conn.execute(
                    "INSERT INTO purchase_items(purchaseId, productId, batchId, unitCode, qty, lotNo, expiryDate, cost, fundSource) VALUES(?,?,?,?,?,?,?,?,?)",
                    (purchase_id, it['productId'], bid, it['unitCode'], qty_val, it['lotNo'], it['expiryDate'], float(it.get('cost') or 0), fund_src)
                )
                purchase_item_id = pi_cur.lastrowid
                
                # Lỗi 1+6: Ghi stock_movements với qtyBase và referenceId
                self.conn.execute(
                    """INSERT INTO stock_movements(
                        productId, batchId, unitCode, qty, qtyBase, originalQty, originalUnit,
                        type, cost, receivingUnit, reason, fundSource,
                        referenceType, referenceId, referenceItemId, createdAt
                    ) VALUES(?,?,?,?,?,?,?, 'PURCHASE', ?,?,?,?,  'PURCHASE',?,?,?)""",
                    (it['productId'], bid, it['unitCode'], qty_val, qty_base, qty_val, it['unitCode'],
                     float(it.get('cost') or 0), supplier, reason, fund_src,
                     purchase_id, purchase_item_id, created_at)
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
                    'qty': qty_val,
                    'lotNo': it['lotNo'],
                    'expiryDate': it['expiryDate'],
                    'cost': float(it.get('cost') or 0),
                    'fundSource': fund_src,
                    'batchId': bid
                })

            self._assert_no_negative_stock()
            self.conn.commit()
            try:
                self.add_audit_log(
                    action="NHAP_KHO",
                    note_id=purchase_id,
                    details=f"Nhập kho thành công, số phiếu: {note_number}, nhà cung cấp: {supplier}, số mặt hàng: {len(items)}",
                    ip=audit_ip
                )
            except Exception as log_err:
                print(f"Lỗi ghi log nhap kho: {log_err}")
            return purchase_id, note_number, purchase_details

        except Exception:
            self.conn.rollback()
            raise

    def bulk_import_products_and_stock(self, import_records, supplier: str = "Nhập kho ban đầu", reason: str = "Nhập kho ban đầu", note: str = "Nhập hàng loạt từ Excel", audit_ip: str = "Local"):
        """
        Thực hiện nhập sản phẩm, đơn vị quy đổi, lô hàng và tạo phiếu nhập kho ban đầu
        TRONG CÙNG MỘT TRANSACTION DUY NHẤT (Atomic Import).
        Nếu xảy ra bất kỳ lỗi nào, toàn bộ quá trình sẽ được ROLLBACK hoàn toàn.
        """
        try:
            self.conn.execute("BEGIN")
            created_at = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            imported_products = 0
            imported_units = 0
            purchase_items = []
            
            product_id_map = {}

            for rec in import_records:
                p_info = rec['product_info']
                name = p_info['name']
                default_unit = p_info['defaultUnit']
                
                if name not in product_id_map:
                    existing = self.conn.execute(
                        "SELECT id, defaultUnit FROM products WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))",
                        (name,)
                    ).fetchone()
                    
                    if existing:
                        p_id = existing['id']
                    else:
                        cur = self.conn.execute(
                            "INSERT INTO products (name, defaultUnit, barcode, productType, registrationNumber) VALUES (?, ?, ?, ?, ?)",
                            (name, default_unit, p_info.get('barcode', ''), p_info.get('productType', 'Thuốc'), p_info.get('registrationNumber', ''))
                        )
                        p_id = cur.lastrowid
                        imported_products += 1
                    product_id_map[name] = p_id
                else:
                    p_id = product_id_map[name]

                self.conn.execute(
                    "INSERT OR IGNORE INTO product_units(productId, unitCode, toBaseQty, price) VALUES(?,?,1,0)", 
                    (p_id, default_unit)
                )

                for u in p_info.get('units', []):
                    self.conn.execute(
                        "INSERT OR REPLACE INTO product_units (productId, unitCode, toBaseQty, price) VALUES (?, ?, ?, ?)",
                        (p_id, u['unitCode'], u['toBaseQty'], u['price'])
                    )
                    imported_units += 1

                s_info = rec.get('stock_info')
                if s_info:
                    self.validate_batch(p_id, s_info['lotNo'], s_info['expiryDate'])
                    purchase_items.append({
                        'productId': p_id,
                        'productName': name,
                        'lotNo': s_info['lotNo'],
                        'expiryDate': s_info['expiryDate'],
                        'unitCode': s_info.get('unitCode') or default_unit,
                        'qty': float(s_info['qty']),
                        'cost': float(s_info.get('cost') or 0.0),
                        'fundSource': s_info.get('fundSource', '')
                    })

            note_number = ""
            purchase_id = None
            if purchase_items:
                note_number = self._next_note_number('PN')
                cur = self.conn.execute(
                    "INSERT INTO purchase_notes(noteNumber, supplier, reason, note, createdAt) VALUES(?,?,?,?,?)",
                    (note_number, supplier, reason, note, created_at)
                )
                purchase_id = cur.lastrowid

                for it in purchase_items:
                    bid = self.ensure_batch(it['productId'], it['lotNo'], it['expiryDate'])
                    to_base, _ = self.unit_info(it['productId'], it['unitCode'])
                    if to_base is None:
                        to_base = 1.0
                    qty_val = float(it['qty'])
                    qty_base = qty_val * to_base
                    fund_src = it.get('fundSource') or ''

                    pi_cur = self.conn.execute(
                        "INSERT INTO purchase_items(purchaseId, productId, batchId, unitCode, qty, lotNo, expiryDate, cost, fundSource) VALUES(?,?,?,?,?,?,?,?,?)",
                        (purchase_id, it['productId'], bid, it['unitCode'], qty_val, it['lotNo'], it['expiryDate'], float(it['cost']), fund_src)
                    )
                    purchase_item_id = pi_cur.lastrowid

                    self.conn.execute(
                        """INSERT INTO stock_movements(
                            productId, batchId, unitCode, qty, qtyBase, originalQty, originalUnit,
                            type, cost, receivingUnit, reason, fundSource,
                            referenceType, referenceId, referenceItemId, createdAt
                        ) VALUES(?,?,?,?,?,?,?, 'PURCHASE', ?,?,?,?,  'PURCHASE',?,?,?)""",
                        (it['productId'], bid, it['unitCode'], qty_val, qty_base, qty_val, it['unitCode'],
                         float(it['cost']), supplier, reason, fund_src,
                         purchase_id, purchase_item_id, created_at)
                    )

            self._assert_no_negative_stock()
            self.conn.commit()

            if purchase_id and note_number:
                try:
                    self.add_audit_log(
                        action="NHAP_KHO",
                        note_id=purchase_id,
                        details=f"Nhập kho Excel thành công, số phiếu: {note_number}, nhà cung cấp: {supplier}, số mặt hàng: {len(purchase_items)}",
                        ip=audit_ip
                    )
                except Exception:
                    pass

            return imported_products, imported_units, len(purchase_items), note_number
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

    def get_fund_sources(self):
        """Lấy danh sách các nguồn kinh phí đã từng nhập hàng"""
        rows = self.q("SELECT DISTINCT fundSource FROM purchase_items WHERE fundSource IS NOT NULL AND fundSource != '' ORDER BY fundSource")
        return [r['fundSource'] for r in rows]

    def get_dispatch_stats_by_unit(self, start_date: str, end_date: str):
        """Thống kê cấp phát gom theo đơn vị nhận trong khoảng thời gian"""
        sql = '''
            SELECT dn.receivingUnit,
                   COUNT(DISTINCT dn.id) AS noteCount,
                   COALESCE(SUM(di.qty), 0) AS totalQty,
                   COALESCE(SUM(di.qty * di.cost), 0) AS totalValue
            FROM dispatch_notes dn
            JOIN dispatch_items di ON di.dispatchId = dn.id
            WHERE DATE(dn.createdAt) BETWEEN DATE(?) AND DATE(?)
              AND dn.receivingUnit IS NOT NULL AND dn.receivingUnit != ''
            GROUP BY dn.receivingUnit
            ORDER BY totalValue DESC
        '''
        return self.q(sql, (start_date, end_date))

    def get_dispatch_detail_by_unit(self, receiving_unit: str, start_date: str, end_date: str):
        """Lấy chi tiết các phiếu xuất cho một đơn vị nhận cụ thể"""
        sql = '''
            SELECT dn.noteNumber, dn.createdAt, dn.reason,
                   p.name AS productName, di.qty, di.cost, di.lotNo, di.expiryDate, di.fundSource
            FROM dispatch_notes dn
            JOIN dispatch_items di ON di.dispatchId = dn.id
            JOIN products p ON p.id = di.productId
            WHERE dn.receivingUnit = ?
              AND DATE(dn.createdAt) BETWEEN DATE(?) AND DATE(?)
            ORDER BY dn.createdAt DESC, p.name
        '''
        return self.q(sql, (receiving_unit, start_date, end_date))

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

