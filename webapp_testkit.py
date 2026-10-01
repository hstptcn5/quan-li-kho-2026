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
