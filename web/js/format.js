// Định dạng hiển thị khớp date_utils.py (DD-MM-YYYY) và bản Tkinter.

export function formatDate(value) {
  const text = String(value || "");
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(text);
  return match ? `${match[3]}-${match[2]}-${match[1]}` : text;
}

export function formatDateTime(value) {
  const text = String(value || "").trim();
  const match = /^(\d{4})-(\d{2})-(\d{2})[ T](.+)$/.exec(text);
  return match ? `${match[3]}-${match[2]}-${match[1]} ${match[4]}` : formatDate(text);
}

export function formatCount(value) {
  return new Intl.NumberFormat("vi-VN").format(Number(value) || 0);
}

export function formatQty(value) {
  const number = Number(value);
  return Number.isFinite(number) ? String(Math.round(number * 10000) / 10000) : "";
}
