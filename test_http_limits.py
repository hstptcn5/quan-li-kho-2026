# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import unittest

import http_limits
import mobile_http_hardening as hardening

ROOT = os.path.dirname(os.path.abspath(__file__))


class HttpLimitsTests(unittest.TestCase):
    def test_module_loads_without_pulling_in_the_legacy_server(self):
        code = (
            "import sys, http_limits; "
            "bad = [m for m in ('server', 'config', 'database', 'mobile_templates') if m in sys.modules]; "
            "assert not bad, bad"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mobile_hardening_reexports_the_same_objects(self):
        for name in (
            "MAX_REQUEST_BODY_BYTES",
            "REQUEST_SOCKET_TIMEOUT_SECONDS",
            "REQUEST_QUEUE_SIZE",
            "RequestBodyPolicyError",
            "validate_request_body_headers",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(hardening, name), getattr(http_limits, name))

    def test_validation_behaviour_is_unchanged(self):
        self.assertEqual(http_limits.validate_request_body_headers({}), 0)
        self.assertEqual(
            http_limits.validate_request_body_headers({"Content-Length": " 128 "}), 128
        )
        for headers, status in (
            ({"Content-Length": "abc"}, 400),
            ({"Content-Length": "-1"}, 400),
            ({"Content-Length": str(http_limits.MAX_REQUEST_BODY_BYTES + 1)}, 413),
            ({"Transfer-Encoding": "chunked"}, 400),
        ):
            with self.subTest(headers=headers):
                with self.assertRaises(http_limits.RequestBodyPolicyError) as ctx:
                    http_limits.validate_request_body_headers(headers)
                self.assertEqual(ctx.exception.status_code, status)


if __name__ == "__main__":
    unittest.main()
