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

The LAN server still uses plain HTTP. H1.1 and H1.2 improve credential handling and request resilience, but they do **not** provide transport encryption. Use the mobile server only on a trusted local network.
