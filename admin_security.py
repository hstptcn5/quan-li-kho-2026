import base64
import hashlib
import hmac
import json
import math
import os
import secrets
import time


class AdminPinConfigError(RuntimeError):
    """Raised when the persisted admin PIN configuration is missing or malformed."""


class AdminPinStore:
    SCHEMA_VERSION = 1
    ALGORITHM = "pbkdf2-sha256"
    ITERATIONS = 600_000
    MIN_ITERATIONS = 100_000
    MAX_ITERATIONS = 2_000_000
    PIN_LENGTH = 6

    def __init__(self, path: str):
        self.path = path

    @classmethod
    def validate_pin(cls, pin: str) -> None:
        if (
            not isinstance(pin, str)
            or len(pin) != cls.PIN_LENGTH
            or not pin.isascii()
            or not pin.isdigit()
        ):
            raise ValueError(f"PIN Admin phải gồm đúng {cls.PIN_LENGTH} chữ số.")

    def is_configured(self) -> bool:
        return bool(self.path and os.path.isfile(self.path))

    @staticmethod
    def _encode(raw: bytes) -> str:
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def _decode(value: str, field_name: str) -> bytes:
        try:
            if not isinstance(value, str):
                raise TypeError
            return base64.b64decode(value.encode("ascii"), validate=True)
        except Exception as exc:
            raise AdminPinConfigError(
                f"Cấu hình PIN Admin có trường {field_name} không hợp lệ."
            ) from exc

    def _load_record(self) -> dict:
        if not self.is_configured():
            raise AdminPinConfigError("Chưa cấu hình PIN Admin.")
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                record = json.load(handle)
        except Exception as exc:
            raise AdminPinConfigError("Không thể đọc cấu hình PIN Admin.") from exc

        if not isinstance(record, dict):
            raise AdminPinConfigError("Cấu hình PIN Admin không đúng định dạng.")
        if record.get("schema_version") != self.SCHEMA_VERSION:
            raise AdminPinConfigError("Phiên bản cấu hình PIN Admin không được hỗ trợ.")
        if record.get("algorithm") != self.ALGORITHM:
            raise AdminPinConfigError("Thuật toán PIN Admin không được hỗ trợ.")

        iterations = record.get("iterations")
        if (
            not isinstance(iterations, int)
            or iterations < self.MIN_ITERATIONS
            or iterations > self.MAX_ITERATIONS
        ):
            raise AdminPinConfigError("Số vòng băm PIN Admin không hợp lệ.")

        salt = self._decode(record.get("salt"), "salt")
        digest = self._decode(record.get("digest"), "digest")
        if len(salt) < 16 or len(digest) != hashlib.sha256().digest_size:
            raise AdminPinConfigError("Cấu hình PIN Admin không vượt qua kiểm tra cấu trúc.")

        return {
            "iterations": iterations,
            "salt": salt,
            "digest": digest,
        }

    @staticmethod
    def _derive(pin: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            iterations,
        )

    def set_pin(self, pin: str) -> None:
        self.validate_pin(pin)
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)

        salt = secrets.token_bytes(16)
        digest = self._derive(pin, salt, self.ITERATIONS)
        record = {
            "schema_version": self.SCHEMA_VERSION,
            "algorithm": self.ALGORITHM,
            "iterations": self.ITERATIONS,
            "salt": self._encode(salt),
            "digest": self._encode(digest),
        }

        temp_path = (
            f"{self.path}.tmp.{os.getpid()}.{secrets.token_hex(4)}"
        )
        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(record, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def verify_pin(self, pin: str) -> bool:
        try:
            self.validate_pin(pin)
        except ValueError:
            return False

        record = self._load_record()
        candidate = self._derive(pin, record["salt"], record["iterations"])
        return hmac.compare_digest(candidate, record["digest"])


class AdminSessionGuard:
    def __init__(
        self,
        store: AdminPinStore,
        session_seconds: int = 15 * 60,
        max_attempts: int = 5,
        lockout_seconds: int = 5 * 60,
        clock=time.monotonic,
    ):
        self.store = store
        self.session_seconds = int(session_seconds)
        self.max_attempts = int(max_attempts)
        self.lockout_seconds = int(lockout_seconds)
        self._clock = clock
        self.failed_attempts = 0
        self.blocked_until = 0.0
        self.unlocked_until = 0.0

    def is_unlocked(self) -> bool:
        return self._clock() < self.unlocked_until

    def is_blocked(self) -> bool:
        return self._clock() < self.blocked_until

    def remaining_lock_seconds(self) -> int:
        return max(0, int(math.ceil(self.blocked_until - self._clock())))

    def remaining_attempts(self) -> int:
        return max(0, self.max_attempts - self.failed_attempts)

    def unlock(self, pin: str) -> bool:
        now = self._clock()
        if now < self.blocked_until:
            return False

        if self.blocked_until:
            self.blocked_until = 0.0
            self.failed_attempts = 0

        if self.store.verify_pin(pin):
            self.failed_attempts = 0
            self.blocked_until = 0.0
            self.unlocked_until = now + self.session_seconds
            return True

        self.unlocked_until = 0.0
        self.failed_attempts += 1
        if self.failed_attempts >= self.max_attempts:
            self.blocked_until = now + self.lockout_seconds
        return False

    def lock(self) -> None:
        self.unlocked_until = 0.0
