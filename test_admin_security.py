import json
import os
import tempfile
import unittest

from admin_security import AdminPinConfigError, AdminPinStore, AdminSessionGuard


class FakeClock:
    def __init__(self, value=1000.0):
        self.value = float(value)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class TestAdminPinStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp_dir.name, "admin_auth.json")
        self.store = AdminPinStore(self.path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pin_is_hashed_and_verifiable(self):
        self.store.set_pin("123456")
        self.assertTrue(self.store.is_configured())
        self.assertTrue(self.store.verify_pin("123456"))
        self.assertFalse(self.store.verify_pin("654321"))

        with open(self.path, "r", encoding="utf-8") as handle:
            raw = handle.read()
        self.assertNotIn("123456", raw)

        record = json.loads(raw)
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["algorithm"], "pbkdf2-sha256")
        self.assertGreaterEqual(record["iterations"], 100_000)

    def test_pin_policy_requires_exactly_six_ascii_digits(self):
        invalid = ["", "12345", "1234567", "abcdef", "１２３４５６", "12 456"]
        for pin in invalid:
            with self.subTest(pin=pin):
                with self.assertRaises(ValueError):
                    self.store.set_pin(pin)

    def test_corrupt_config_fails_closed(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write('{"schema_version": 1, "algorithm": "pbkdf2-sha256"}')

        with self.assertRaises(AdminPinConfigError):
            self.store.verify_pin("123456")

    def test_replacing_pin_invalidates_old_pin(self):
        self.store.set_pin("123456")
        self.store.set_pin("654321")
        self.assertFalse(self.store.verify_pin("123456"))
        self.assertTrue(self.store.verify_pin("654321"))


class TestAdminSessionGuard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        path = os.path.join(self.temp_dir.name, "admin_auth.json")
        self.store = AdminPinStore(path)
        self.store.set_pin("123456")
        self.clock = FakeClock()
        self.guard = AdminSessionGuard(
            self.store,
            session_seconds=60,
            max_attempts=5,
            lockout_seconds=300,
            clock=self.clock,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_unlock_expires_and_lock_is_immediate(self):
        self.assertTrue(self.guard.unlock("123456"))
        self.assertTrue(self.guard.is_unlocked())

        self.clock.advance(59)
        self.assertTrue(self.guard.is_unlocked())
        self.clock.advance(2)
        self.assertFalse(self.guard.is_unlocked())

        self.assertTrue(self.guard.unlock("123456"))
        self.guard.lock()
        self.assertFalse(self.guard.is_unlocked())

    def test_five_failures_trigger_temporary_lockout(self):
        for attempt in range(5):
            self.assertFalse(self.guard.unlock("000000"))
            if attempt < 4:
                self.assertFalse(self.guard.is_blocked())

        self.assertTrue(self.guard.is_blocked())
        self.assertEqual(self.guard.remaining_attempts(), 0)
        self.assertFalse(self.guard.unlock("123456"))

        self.clock.advance(301)
        self.assertTrue(self.guard.unlock("123456"))
        self.assertFalse(self.guard.is_blocked())
        self.assertTrue(self.guard.is_unlocked())


if __name__ == "__main__":
    unittest.main()
