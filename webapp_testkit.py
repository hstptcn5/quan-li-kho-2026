# -*- coding: utf-8 -*-
"""Harness HTTP dùng chung cho test của backend web."""

import http.client
import json

from webapp.auth import LocalSession
from webapp.listener import LocalListener


class Harness:
    def __init__(self, test_case, router, web_root):
        self.session = LocalSession()
        self.listener = LocalListener(router, self.session, web_root)
        self.listener.start()
        test_case.addCleanup(self.listener.stop)
        self.cookie = None

    @property
    def port(self):
        return self.listener.port

    def request(self, method, path, *, headers=None, body=None, cookie=None):
        merged = dict(headers or {})
        cookie_value = cookie if cookie is not None else self.cookie
        if cookie_value:
            merged["Cookie"] = cookie_value
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.request(method, path, body=body, headers=merged)
            response = conn.getresponse()
            data = response.read()
            return response.status, {k.lower(): v for k, v in response.getheaders()}, data
        finally:
            conn.close()

    def json(self, method, path, **kwargs):
        status, headers, data = self.request(method, path, **kwargs)
        return status, headers, json.loads(data.decode("utf-8"))

    def login(self):
        status, headers, _ = self.request("GET", f"/boot/{self.session.boot_token}", cookie="")
        assert status == 302, status
        self.cookie = headers["set-cookie"].split(";", 1)[0]
        return self.cookie


def seed_demo_database(db_path):
    """DB mẫu cho smoke test và kiểm tra thủ công: 1 hết hạn, 1 cận hạn, 1 tồn thấp, 1 bình thường.

    Tên sản phẩm đầu tiên chứa thẻ HTML và dấu nháy để kiểm tra hiển thị an toàn.
    """
    import datetime as dt
    import os

    from database import DB

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    today = dt.date.today()
    products = [
        (1, '<b>x</b> Thuốc hết hạn & "q"', "L-EXP", -10, 20),
        (2, "Thuốc cận hạn", "L-NEAR", 30, 50),
        (3, "Vật tư tồn thấp", "L-LOW", 800, 5),
        (4, "Thuốc bình thường", "L-OK", 900, 100),
    ]
    db = DB(db_path)
    try:
        for product_id, name, lot, offset_days, qty in products:
            db.conn.execute(
                "INSERT INTO products(id, name, defaultUnit) VALUES(?, ?, 'Viên')", (product_id, name)
            )
            db.conn.execute(
                "INSERT INTO product_units(productId, unitCode, toBaseQty, price) VALUES(?, 'Viên', 1, 0)",
                (product_id,),
            )
            db.conn.commit()
            db.record_purchase(
                [{
                    "productId": product_id, "productName": name, "qty": qty, "unitCode": "Viên",
                    "lotNo": lot, "expiryDate": (today + dt.timedelta(days=offset_days)).isoformat(),
                    "cost": 1000, "fundSource": "BHYT",
                }],
                "NCC", "Nhập kho", "",
            )
    finally:
        db.conn.close()
    return {"counts": {"all": 3, "expired": 1, "near": 1, "low": 1}, "literal": "<b>x</b>"}
