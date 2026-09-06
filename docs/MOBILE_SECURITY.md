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

The LAN server still uses plain HTTP. H1.1 protects credentials from browser-accessible storage and URLs, but it does not provide transport encryption. Use the mobile server only on a trusted local network.

H1.2 is intentionally separate and will address request size limits, timeouts and concurrent request handling.
