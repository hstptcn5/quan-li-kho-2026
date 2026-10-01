# -*- coding: utf-8 -*-
import tempfile
import unittest
from pathlib import Path

from http_limits import MAX_REQUEST_BODY_BYTES
from webapp.auth import LocalSession
from webapp.listener import LocalListener
from webapp.routing import SCOPE_LAN, Router, json_response
from webapp.security import SECURITY_HEADERS
from webapp_testkit import Harness


class ListenerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.web = Path(self.tmp.name)
        (self.web / "js").mkdir()
        (self.web / "index.html").write_text("<!doctype html><p>trang chủ</p>", encoding="utf-8")
        (self.web / "js" / "a.js").write_text("export const a = 1;", encoding="utf-8")
        router = Router()
        router.add("GET", "/api/ping", lambda request: json_response({"success": True, "scope": request.scope}))
        router.add("GET", "/api/lan-only", lambda request: json_response({"success": True}), scopes=(SCOPE_LAN,))
        self.harness = Harness(self, router, self.web)

    @property
    def origin(self):
        return {"Origin": f"http://127.0.0.1:{self.harness.port}"}


class AuthenticationTests(ListenerCase):
    def test_api_without_cookie_is_401_json(self):
        status, _, payload = self.harness.json("GET", "/api/ping")
        self.assertEqual(status, 401)
        self.assertEqual(payload, {"success": False, "message": "Chưa xác thực", "auth_required": True})

    def test_page_without_cookie_is_401_and_empty(self):
        status, _, body = self.harness.request("GET", "/")
        self.assertEqual(status, 401)
        self.assertEqual(body, b"")

    def test_boot_sets_an_httponly_cookie_and_redirects_home(self):
        status, headers, _ = self.harness.request("GET", f"/boot/{self.harness.session.boot_token}")
        self.assertEqual(status, 302)
        self.assertEqual(headers["location"], "/")
        cookie = headers["set-cookie"]
        for attribute in ("HttpOnly", "SameSite=Strict", "Path=/"):
            self.assertIn(attribute, cookie)

    def test_cookie_unlocks_pages_and_api_repeatedly(self):
        self.harness.login()
        for _ in range(2):
            status, _, body = self.harness.request("GET", "/")
            self.assertEqual(status, 200)
            self.assertIn("trang chủ".encode("utf-8"), body)
        status, _, payload = self.harness.json("GET", "/api/ping")
        self.assertEqual((status, payload["scope"]), (200, "local"))

    def test_boot_token_is_single_use_but_the_cookie_keeps_working(self):
        cookie = self.harness.login()
        status, _, _ = self.harness.request("GET", f"/boot/{self.harness.session.boot_token}", cookie="")
        self.assertEqual(status, 401)
        self.assertEqual(self.harness.request("GET", "/", cookie=cookie)[0], 200)

    def test_wrong_boot_token_is_rejected_and_the_real_one_still_works(self):
        status, _, _ = self.harness.request("GET", "/boot/not-the-token", cookie="")
        self.assertEqual(status, 401)
        self.harness.login()

    def test_a_forged_cookie_is_rejected(self):
        self.harness.login()
        status, _, _ = self.harness.request("GET", "/api/ping", cookie="qlk_session=forged")
        self.assertEqual(status, 401)


class HostAndOriginTests(ListenerCase):
    def test_foreign_or_wrong_port_host_is_403_even_with_a_valid_cookie(self):
        self.harness.login()
        for host in ("evil.example", f"127.0.0.1:{self.harness.port + 1}", "127.0.0.1"):
            with self.subTest(host=host):
                status, _, _ = self.harness.request("GET", "/api/ping", headers={"Host": host})
                self.assertEqual(status, 403)

    def test_wrong_host_does_not_consume_the_boot_token(self):
        status, _, _ = self.harness.request(
            "GET", f"/boot/{self.harness.session.boot_token}", headers={"Host": "evil.example"}, cookie=""
        )
        self.assertEqual(status, 403)
        self.harness.login()

    def test_localhost_alias_host_is_accepted(self):
        self.harness.login()
        status, _, _ = self.harness.request(
            "GET", "/api/ping", headers={"Host": f"localhost:{self.harness.port}"}
        )
        self.assertEqual(status, 200)

    def test_unsafe_methods_need_a_same_origin_marker(self):
        self.harness.login()
        status, _, _ = self.harness.request("POST", "/api/ping", body=b"{}")
        self.assertEqual(status, 403)
        status, _, _ = self.harness.request("POST", "/api/ping", body=b"{}", headers={"Origin": "http://evil.example"})
        self.assertEqual(status, 403)
        # Origin hợp lệ đi qua được lớp kiểm tra, tới router và nhận 405 (route chỉ có GET).
        status, _, _ = self.harness.request("POST", "/api/ping", body=b"{}", headers=self.origin)
        self.assertEqual(status, 405)
        status, _, _ = self.harness.request(
            "POST", "/api/ping", body=b"{}", headers={"Sec-Fetch-Site": "same-origin"}
        )
        self.assertEqual(status, 405)


class RoutingAndStaticTests(ListenerCase):
    def test_lan_only_route_is_403_on_the_local_listener(self):
        self.harness.login()
        self.assertEqual(self.harness.request("GET", "/api/lan-only")[0], 403)

    def test_unknown_api_path_is_404_json_and_unknown_page_is_404(self):
        self.harness.login()
        self.assertEqual(self.harness.json("GET", "/api/none")[0], 404)
        self.assertEqual(self.harness.request("GET", "/nope.html")[0], 404)

    def test_responses_carry_security_and_cache_headers(self):
        self.harness.login()
        _, page_headers, _ = self.harness.request("GET", "/")
        _, api_headers, _ = self.harness.request("GET", "/api/ping")
        _, denied_headers, _ = self.harness.request("GET", "/api/ping", cookie="")
        for headers in (page_headers, api_headers, denied_headers):
            for name, value in SECURITY_HEADERS.items():
                self.assertEqual(headers[name.lower()], value)
        self.assertEqual(page_headers["cache-control"], "no-cache")
        self.assertEqual(api_headers["cache-control"], "no-store")
        self.assertNotIn("python", page_headers.get("server", "").lower())

    def test_javascript_is_served_as_a_module_capable_type(self):
        self.harness.login()
        status, headers, body = self.harness.request("GET", "/js/a.js")
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "text/javascript; charset=utf-8")
        self.assertEqual(body, b"export const a = 1;")


class FramingTests(ListenerCase):
    def test_oversized_and_malformed_bodies_are_rejected_before_reading(self):
        self.harness.login()
        cases = (
            ({"Content-Length": str(MAX_REQUEST_BODY_BYTES + 1)}, 413),
            ({"Content-Length": "abc"}, 400),
            ({"Content-Length": "-5"}, 400),
            ({"Transfer-Encoding": "chunked"}, 400),
        )
        for extra, expected in cases:
            with self.subTest(extra=extra):
                headers = dict(self.origin)
                headers.update(extra)
                status, _, _ = self.harness.request("POST", "/api/ping", headers=headers)
                self.assertEqual(status, expected)


class ConstructionTests(unittest.TestCase):
    def test_only_loopback_binding_is_allowed(self):
        for host in ("0.0.0.0", "192.168.1.10", "", "localhost"):
            with self.subTest(host=host):
                with self.assertRaises(ValueError):
                    LocalListener(Router(), LocalSession(), Path("."), host=host)

    def test_port_is_assigned_by_the_system_and_boot_url_uses_it(self):
        session = LocalSession()
        listener = LocalListener(Router(), session, Path("."))
        try:
            self.assertGreater(listener.port, 0)
            self.assertEqual(listener.boot_url(), f"http://127.0.0.1:{listener.port}/boot/{session.boot_token}")
        finally:
            listener.stop()

    def test_stop_is_idempotent_and_safe_without_start(self):
        listener = LocalListener(Router(), LocalSession(), Path("."))
        listener.stop()
        listener.stop()


if __name__ == "__main__":
    unittest.main()
