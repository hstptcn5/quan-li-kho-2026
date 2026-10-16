// Gọi API cùng origin. Cookie phiên HttpOnly tự được trình duyệt gửi kèm.

export class ApiError extends Error {
  constructor(status, message, authRequired) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.authRequired = Boolean(authRequired);
  }
}

export async function getJson(path, params = {}) {
  const url = new URL(path, window.location.origin);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, String(value));
  }

  let response;
  try {
    response = await fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } });
  } catch (error) {
    throw new ApiError(0, "Không kết nối được tới ứng dụng", false);
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch (error) {
    payload = null;
  }

  if (!response.ok || !payload || payload.success === false) {
    const message = (payload && payload.message) || `Lỗi ${response.status}`;
    throw new ApiError(response.status, message, response.status === 401 || Boolean(payload && payload.auth_required));
  }
  return payload;
}
