# -*- coding: utf-8 -*-
import json
import unittest

from webapp.routing import (
    SCOPE_LAN,
    SCOPE_LOCAL,
    HttpError,
    Request,
    Response,
    Router,
    json_response,
)


def make_request(method="GET", path="/api/x", scope=SCOPE_LOCAL):
    return Request(method=method, path=path, query={}, headers={}, body=b"", scope=scope)


def body_of(response):
    return json.loads(response.body.decode("utf-8"))


class RouterTests(unittest.TestCase):
    def test_dispatches_to_the_matching_handler(self):
        router = Router()
        router.add("GET", "/api/x", lambda request: json_response({"success": True, "path": request.path}))
        response = router.dispatch(make_request())
        self.assertEqual(response.status, 200)
        self.assertEqual(body_of(response), {"success": True, "path": "/api/x"})

    def test_local_only_route_is_forbidden_from_the_lan_scope(self):
        router = Router()
        router.add("GET", "/api/admin", lambda request: json_response({"success": True}))
        response = router.dispatch(make_request(path="/api/admin", scope=SCOPE_LAN))
        self.assertEqual(response.status, 403)
        self.assertFalse(body_of(response)["success"])

    def test_route_declared_for_lan_is_allowed_from_lan_and_local_only_when_listed(self):
        router = Router()
        router.add("GET", "/api/lan", lambda request: json_response({"success": True}), scopes=(SCOPE_LAN,))
        router.add("GET", "/api/both", lambda request: json_response({"success": True}), scopes=(SCOPE_LOCAL, SCOPE_LAN))
        self.assertEqual(router.dispatch(make_request(path="/api/lan", scope=SCOPE_LAN)).status, 200)
        self.assertEqual(router.dispatch(make_request(path="/api/lan", scope=SCOPE_LOCAL)).status, 403)
        self.assertEqual(router.dispatch(make_request(path="/api/both", scope=SCOPE_LAN)).status, 200)
        self.assertEqual(router.dispatch(make_request(path="/api/both", scope=SCOPE_LOCAL)).status, 200)

    def test_unknown_path_is_404(self):
        self.assertEqual(Router().dispatch(make_request(path="/api/none")).status, 404)

    def test_wrong_method_is_405_with_allow_header(self):
        router = Router()
        router.add("GET", "/api/x", lambda request: json_response({"success": True}))
        router.add("POST", "/api/x", lambda request: json_response({"success": True}))
        response = router.dispatch(make_request(method="DELETE"))
        self.assertEqual(response.status, 405)
        self.assertEqual(response.headers["Allow"], "GET, POST")

    def test_http_error_becomes_a_json_error(self):
        def handler(request):
            raise HttpError(400, "Tham số sai")

        router = Router()
        router.add("GET", "/api/x", handler)
        response = router.dispatch(make_request())
        self.assertEqual(response.status, 400)
        self.assertEqual(body_of(response), {"success": False, "message": "Tham số sai"})

    def test_unexpected_exception_hides_internal_details(self):
        def handler(request):
            raise RuntimeError(r"không mở được C:\Users\secret\pharm.db")

        router = Router()
        router.add("GET", "/api/x", handler)
        with self.assertLogs("webapp.routing", level="ERROR"):
            response = router.dispatch(make_request())
        self.assertEqual(response.status, 500)
        self.assertEqual(body_of(response), {"success": False, "message": "Lỗi hệ thống"})
        self.assertNotIn(b"secret", response.body)

    def test_json_response_is_utf8_and_never_cached(self):
        response = json_response({"tên": "Thuốc Ư"})
        self.assertIsInstance(response, Response)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIn("Thuốc Ư".encode("utf-8"), response.body)


if __name__ == "__main__":
    unittest.main()
