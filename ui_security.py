import os
import tkinter as tk
from tkinter import messagebox, simpledialog

from admin_security import AdminPinConfigError, AdminPinStore, AdminSessionGuard
from config import APP_DIR


class AdminSecurityMixin:
    """Desktop admin unlock layer for destructive/local-administration actions."""

    ADMIN_SESSION_SECONDS = 15 * 60
    ADMIN_MAX_ATTEMPTS = 5
    ADMIN_LOCKOUT_SECONDS = 5 * 60

    def __init__(self, *args, **kwargs):
        auth_path = os.path.join(APP_DIR, "admin_auth.json")
        self._admin_store = AdminPinStore(auth_path)
        self._admin_guard = AdminSessionGuard(
            self._admin_store,
            session_seconds=self.ADMIN_SESSION_SECONDS,
            max_attempts=self.ADMIN_MAX_ATTEMPTS,
            lockout_seconds=self.ADMIN_LOCKOUT_SECONDS,
        )
        self._admin_expiry_generation = 0
        super().__init__(*args, **kwargs)

        # The previous desktop role selector started in Admin without authentication.
        # Start locked instead; protected actions can elevate through the PIN flow.
        self.current_role = "Thủ kho"

    def make_ui(self):
        super().make_ui()
        try:
            menubar = self.nametowidget(self.cget("menu"))
            end_index = menubar.index("end")
            if end_index is not None:
                for index in range(end_index, -1, -1):
                    try:
                        if menubar.entrycget(index, "label") == "Vai trò":
                            menubar.delete(index)
                    except tk.TclError:
                        continue

            self.security_menu = tk.Menu(menubar, tearoff=0)
            self.security_menu.add_command(
                label="Mở khóa Admin…",
                command=self.unlock_admin,
            )
            self.security_menu.add_command(
                label="Khóa Admin",
                command=self.lock_admin,
            )
            self.security_menu.add_separator()
            self.security_menu.add_command(
                label="Đổi PIN Admin…",
                command=self.change_admin_pin,
            )
            menubar.add_cascade(label="Bảo mật", menu=self.security_menu)
        except Exception as exc:
            print(f"Không thể khởi tạo menu bảo mật desktop: {exc}")

        self._update_security_label()

    def _update_security_label(self):
        if not hasattr(self, "role_label"):
            return
        if self._admin_guard.is_unlocked():
            text = "Bảo mật: Admin mở khóa"
        else:
            text = "Bảo mật: Đã khóa"
        try:
            self.role_label.config(text=text)
        except Exception:
            pass

    def _set_admin_active(self):
        self.current_role = "Admin"
        self._update_security_label()
        self._schedule_admin_expiry()

    def _set_locked_role(self):
        self.current_role = "Thủ kho"
        self._update_security_label()

    def _schedule_admin_expiry(self):
        self._admin_expiry_generation += 1
        generation = self._admin_expiry_generation
        delay_ms = int((self.ADMIN_SESSION_SECONDS + 1) * 1000)

        def expire_if_current():
            if generation != self._admin_expiry_generation:
                return
            if self._admin_guard.is_unlocked():
                return
            self._admin_guard.lock()
            self._set_locked_role()
            try:
                self.toast("Phiên Admin đã tự động khóa")
            except Exception:
                pass

        try:
            self.after(delay_ms, expire_if_current)
        except Exception:
            pass

    def set_current_role(self, role):
        """Compatibility hook for legacy role commands; Admin now requires PIN."""
        if role == "Admin":
            return self.unlock_admin()

        self._admin_guard.lock()
        self._admin_expiry_generation += 1
        self._set_locked_role()
        try:
            self.toast("Đã khóa quyền Admin")
        except Exception:
            pass
        return True

    def _prompt_new_admin_pin(self):
        pin = simpledialog.askstring(
            "Thiết lập PIN Admin",
            "Tạo PIN Admin gồm đúng 6 chữ số:",
            show="*",
            parent=self,
        )
        if pin is None:
            return None

        confirm = simpledialog.askstring(
            "Xác nhận PIN Admin",
            "Nhập lại PIN Admin:",
            show="*",
            parent=self,
        )
        if confirm is None:
            return None
        if pin != confirm:
            messagebox.showerror(
                "PIN không khớp",
                "Hai lần nhập PIN Admin không giống nhau.",
                parent=self,
            )
            return None
        try:
            self._admin_store.validate_pin(pin)
        except ValueError as exc:
            messagebox.showerror("PIN không hợp lệ", str(exc), parent=self)
            return None
        return pin

    def _setup_admin_pin(self, action=None):
        action_text = f" để {action}" if action else ""
        if not messagebox.askyesno(
            "Thiết lập bảo mật Admin",
            "Ứng dụng chưa có PIN Admin.\n\n"
            f"Thiết lập PIN 6 chữ số ngay{action_text}?\n"
            "PIN chỉ được lưu dưới dạng băm, không lưu văn bản gốc.",
            parent=self,
        ):
            return False

        pin = self._prompt_new_admin_pin()
        if pin is None:
            return False
        try:
            self._admin_store.set_pin(pin)
            if not self._admin_guard.unlock(pin):
                raise RuntimeError("Không thể mở khóa bằng PIN vừa tạo.")
        except Exception as exc:
            messagebox.showerror(
                "Lỗi thiết lập PIN Admin",
                str(exc),
                parent=self,
            )
            return False

        self._set_admin_active()
        try:
            self.toast("Đã thiết lập và mở khóa Admin")
        except Exception:
            pass
        return True

    def unlock_admin(self, action=None):
        if self._admin_guard.is_unlocked():
            self._set_admin_active()
            return True

        if not self._admin_store.is_configured():
            return self._setup_admin_pin(action=action)

        if self._admin_guard.is_blocked():
            seconds = self._admin_guard.remaining_lock_seconds()
            messagebox.showwarning(
                "Admin tạm khóa",
                f"Nhập sai PIN quá số lần cho phép. Thử lại sau {seconds} giây.",
                parent=self,
            )
            self._set_locked_role()
            return False

        suffix = f" để {action}" if action else ""
        pin = simpledialog.askstring(
            "Mở khóa Admin",
            f"Nhập PIN Admin 6 chữ số{suffix}:",
            show="*",
            parent=self,
        )
        if pin is None:
            self._set_locked_role()
            return False

        try:
            unlocked = self._admin_guard.unlock(pin)
        except AdminPinConfigError as exc:
            self._set_locked_role()
            messagebox.showerror(
                "Cấu hình PIN Admin bị lỗi",
                f"{exc}\n\nỨng dụng từ chối tự reset PIN để tránh bypass bảo mật.",
                parent=self,
            )
            return False

        if unlocked:
            self._set_admin_active()
            try:
                self.toast("Admin đã mở khóa trong 15 phút")
            except Exception:
                pass
            return True

        self._set_locked_role()
        if self._admin_guard.is_blocked():
            seconds = self._admin_guard.remaining_lock_seconds()
            messagebox.showerror(
                "Admin tạm khóa",
                f"PIN sai. Quyền Admin bị khóa tạm thời trong {seconds} giây.",
                parent=self,
            )
        else:
            remaining = self._admin_guard.remaining_attempts()
            messagebox.showerror(
                "PIN Admin sai",
                f"PIN không đúng. Còn {remaining} lần thử trước khi bị khóa tạm thời.",
                parent=self,
            )
        return False

    def lock_admin(self, silent=False):
        self._admin_guard.lock()
        self._admin_expiry_generation += 1
        self._set_locked_role()
        if not silent:
            try:
                self.toast("Đã khóa quyền Admin")
            except Exception:
                pass
        return True

    def change_admin_pin(self):
        if not self._admin_store.is_configured():
            return self._setup_admin_pin(action="thiết lập PIN Admin")

        if not self._admin_guard.is_unlocked():
            if not self.unlock_admin(action="đổi PIN Admin"):
                return False

        new_pin = self._prompt_new_admin_pin()
        if new_pin is None:
            return False
        try:
            self._admin_store.set_pin(new_pin)
            self._admin_guard.lock()
            if not self._admin_guard.unlock(new_pin):
                raise RuntimeError("Không thể xác minh PIN Admin mới.")
        except Exception as exc:
            messagebox.showerror(
                "Lỗi đổi PIN Admin",
                str(exc),
                parent=self,
            )
            return False

        self._set_admin_active()
        try:
            self.toast("Đã đổi PIN Admin")
        except Exception:
            pass
        return True

    def require_admin_action(self, action):
        """Require a real PIN-backed admin session for destructive actions."""
        if self._admin_guard.is_unlocked():
            return True

        # A stale visual role must never authorize an operation after expiry.
        self._set_locked_role()
        return self.unlock_admin(action=action)
