# Mobile LAN Security

## H1.1 — Cookie-only session

The mobile inventory UI uses the desktop-generated six-digit PIN to create a LAN session.

Security rules after H1.1:

- The session secret is stored only in an `HttpOnly; SameSite=Strict; Path=/` cookie.
- The JSON login response does not contain the session token.
- `localStorage` is not used for the authentication credential. It remains in use only for non-secret cart drafts.
- Protected endpoints do not accept authentication from a Bearer token or a URL query parameter.
- Mobile print pages open on the same origin and therefore receive the HttpOnly cookie automatically; no session token is appended to print URLs.
- Sessions remain IP-bound and expire after eight hours, preserving the previous LAN session lifetime.
- Five failed PIN attempts trigger the existing five-minute IP lockout; after the lockout expires, the attempt counter starts a fresh window.

## H1.2 — HTTP resilience

The production mobile server adds bounded and concurrent request handling on top of the H1.1 cookie-only session:

- Requests are served through a `ThreadingHTTPServer` so one slow mobile client does not block every other LAN client.
- Worker threads are daemonized and server shutdown does not wait indefinitely for worker cleanup.
- Each accepted client socket receives a 15-second timeout to bound stalled reads/writes.
- POST request bodies are capped at 1 MiB before the legacy handler performs `rfile.read(...)`.
- Malformed or negative `Content-Length` values are rejected with HTTP 400.
- Oversized bodies are rejected with HTTP 413 without reading the body into memory.
- Unsupported `Transfer-Encoding` values such as `chunked` are rejected because the current legacy API expects fixed-length JSON bodies.
- Framing-policy rejections force `Connection: close` so unread bytes cannot be interpreted as a later keep-alive request.
- Access to the in-memory PIN attempt counters and active session-token registry is serialized so concurrent worker threads cannot race compound authentication updates.
- The existing port retry, offline QR asset check, server PIN generation and audit logging behavior are preserved.

## H3.1 — Request-thread SQLite ownership

The final hardening pass locks the SQLite ownership boundary required by the threaded LAN server:

- The desktop Tk thread keeps ownership of `app.db`.
- The legacy `MobileInventoryServer.db_instance` copy is detached before worker requests start.
- The `ThreadingHTTPServer` object is never given a desktop SQLite/`DB` connection.
- Mobile request handlers open their own SQLite connection or `DB(DB_PATH)` instance inside the request worker thread and close it after the operation.
- The HTTP server keeps only the desktop application reference needed to enqueue UI refreshes with `app.after(...)`; handlers must not access `app_instance.db`.
- CI includes a real concurrent HTTP integration test: two authenticated mobile dispatch requests race for the same 10-unit lot while the desktop DB connection remains open on the main thread. Exactly one request may commit, final stock must be 3, one dispatch note must exist, and no negative stock balance may be created.

This gate intentionally leaves SQLite's default `check_same_thread=True` protection enabled. A future regression that tries to reuse the desktop connection in an HTTP worker should therefore fail loudly in CI instead of silently weakening thread ownership.

The LAN server still uses plain HTTP. H1.1, H1.2 and H3.1 improve credential handling, request resilience and SQLite thread safety, but they do **not** provide transport encryption. Use the mobile server only on a trusted local network.
