# JWT (JSON Web Tokens)

## Table of Contents
1. [What is a JWT?](#1-what-is-a-jwt)
2. [Anatomy of a JWT](#2-anatomy-of-a-jwt)
3. [How JWT Authentication Works](#3-how-jwt-authentication-works)
4. [Signing Algorithms](#4-signing-algorithms)
5. [Standard Claims](#5-standard-claims)
6. [JWT vs Sessions](#6-jwt-vs-sessions)
7. [Access Tokens vs Refresh Tokens](#7-access-tokens-vs-refresh-tokens)
8. [Storage: Where to Keep JWTs on the Client](#8-storage-where-to-keep-jwts-on-the-client)
9. [Common Vulnerabilities & Attacks](#9-common-vulnerabilities--attacks)
10. [Best Practices](#10-best-practices)
11. [Revocation & Logout Strategies](#11-revocation--logout-strategies)
12. [Advanced Topics](#12-advanced-topics)
13. [JWT in Practice (Python / FastAPI example)](#13-jwt-in-practice-python--fastapi-example)
14. [Quick Reference Cheat Sheet](#14-quick-reference-cheat-sheet)

---

## 1. What is a JWT?

**JWT (JSON Web Token)** is an open standard (**RFC 7519**) for securely transmitting information between two parties as a compact, URL-safe JSON object. That information can be **verified and trusted** because it's digitally signed.

Key properties:
- **Compact** — small enough to send in a URL, POST body, or HTTP header.
- **Self-contained** — the token itself carries all the data needed to identify the user (no server-side lookup required, unlike sessions).
- **Stateless** — the server doesn't need to store the token; it just verifies the signature.

Typical use cases:
- Authentication (most common) — after login, the server issues a JWT, and the client sends it with every request.
- Authorization — the claims inside a JWT can encode what a user is allowed to do.
- Secure information exchange — since JWTs are signed, the receiver can confirm the sender's identity and that content wasn't tampered with.

---

## 2. Anatomy of a JWT

A JWT is a string made of **three parts** separated by dots (`.`):

```
xxxxx.yyyyy.zzzzz
Header.Payload.Signature
```

### 2.1 Header
A JSON object describing the token type and signing algorithm, then Base64Url-encoded.

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### 2.2 Payload
A JSON object containing **claims** — statements about the entity (usually the user) plus metadata. Also Base64Url-encoded.

```json
{
  "sub": "1234567890",
  "name": "Jane Doe",
  "role": "admin",
  "iat": 1690000000,
  "exp": 1690003600
}
```

⚠️ **Important**: The payload is only **encoded**, not **encrypted**. Anyone can decode it (e.g. on [jwt.io](https://jwt.io)) and read its contents. Never put secrets or sensitive data (passwords, credit card numbers) in the payload.

### 2.3 Signature
Created by taking the encoded header, encoded payload, a secret (or private key), and running them through the algorithm specified in the header:

```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

The signature is what makes the token **tamper-evident** — if anyone changes the header or payload, the signature won't match anymore.

---

## 3. How JWT Authentication Works

Typical flow:

1. **Login**: User submits credentials (email/password) to the server.
2. **Verification**: Server checks credentials against the database.
3. **Token issuance**: Server creates a JWT, signs it with a secret/private key, and sends it back to the client.
4. **Client stores the token** (memory, cookie, or storage — see Section 8).
5. **Subsequent requests**: Client attaches the token, usually in the `Authorization` header:
   ```
   Authorization: Bearer <token>
   ```
6. **Server verifies**: On each request, the server checks the signature and claims (expiry, issuer, audience, etc.) — **without needing to query the database** for session state.
7. **Access granted/denied** based on the validated claims.

```
Client                     Server
  |--- POST /login -------->|
  |                         | verify credentials
  |<--- JWT -----------------|
  |                         |
  |--- GET /feed ----------->|  (Authorization: Bearer <JWT>)
  |                         | verify signature + claims
  |<--- data -----------------|
```

---

## 4. Signing Algorithms

JWTs can be signed using different algorithms, broadly split into two families:

### 4.1 Symmetric (HMAC family — e.g., `HS256`, `HS384`, `HS512`)
- One **shared secret** used to both sign and verify.
- Simple, fast.
- Anyone who can verify the token can also forge one (since they hold the same secret) — so the secret must be kept strictly server-side.
- Good for single-service / monolithic setups.

### 4.2 Asymmetric (RSA/ECDSA family — e.g., `RS256`, `ES256`)
- A **private key** signs the token; a **public key** verifies it.
- The public key can be shared with other services safely — they can verify tokens but can't create new ones.
- Ideal for microservices / distributed systems where multiple services need to verify tokens issued by a central auth server.
- Slightly more computationally expensive than HMAC.

### 4.3 `none` Algorithm — Danger!
JWT spec technically allows an `alg: none`, meaning "unsigned." **This should always be rejected** by verifiers — it's a classic attack vector (see Section 9).

---

## 5. Standard Claims

Claims are key-value pairs in the payload. There are three types:

### 5.1 Registered Claims (predefined, optional, recommended)
| Claim | Meaning |
|-------|---------|
| `iss` | Issuer — who created the token |
| `sub` | Subject — who the token is about (usually user ID) |
| `aud` | Audience — intended recipient(s) |
| `exp` | Expiration time (Unix timestamp) — token invalid after this |
| `nbf` | Not before — token invalid until this time |
| `iat` | Issued at — when the token was created |
| `jti` | JWT ID — unique identifier for the token (useful for revocation/replay prevention) |

### 5.2 Public Claims
Custom claims defined by whoever is using JWTs, but registered in the [IANA JSON Web Token Registry](https://www.iana.org/assignments/jwt/jwt.xhtml) to avoid collisions, or namespaced with a URI (e.g. `https://myapp.com/roles`).

### 5.3 Private Claims
Custom claims agreed upon between parties for their own use (e.g., `role`, `permissions`, `tenant_id`) — not registered anywhere, just app-specific.

---

## 6. JWT vs Sessions

| | Session (stateful) | JWT (stateless) |
|---|---|---|
| Storage | Server stores session data (in-memory/Redis/DB); client holds only a session ID | Server stores nothing; all data lives in the token itself |
| Scalability | Needs shared session store across servers | Any server with the secret/public key can verify — scales horizontally easily |
| Revocation | Easy — just delete the session server-side | Hard — token is valid until it expires (see Section 11) |
| Size | Small cookie (just an ID) | Larger — grows with number of claims |
| Cross-domain/service use | Harder | Easier — token can be verified by any service with the key |

**Rule of thumb**: Use sessions when you control a single backend and want simple, instant revocation. Use JWTs when you have distributed/microservice architectures, mobile clients, or third-party API access.

---

## 7. Access Tokens vs Refresh Tokens

Because JWTs can't be easily revoked, best practice is to use **two tokens**:

- **Access Token**
  - Short-lived (minutes to ~1 hour)
  - Sent with every API request
  - If stolen, damage window is small

- **Refresh Token**
  - Long-lived (days to weeks)
  - Stored more securely (e.g., httpOnly cookie), rarely transmitted
  - Used only to request a new access token when the old one expires
  - Often stored server-side (in a DB) so it **can** be revoked/rotated

Flow:
1. Login → get access token + refresh token.
2. Access token expires → client sends refresh token to a `/refresh` endpoint.
3. Server validates refresh token (checks it against DB/revocation list) → issues a new access token (and often a new refresh token — "rotation").

**Refresh token rotation**: each time a refresh token is used, invalidate it and issue a new one. If an old (already-used) refresh token is presented again, treat it as a signal of theft and revoke the whole token family.

---

## 8. Storage: Where to Keep JWTs on the Client

| Storage | Pros | Cons |
|---|---|---|
| `localStorage` | Easy to use, persists across tabs | Vulnerable to **XSS** — any injected script can read it |
| `sessionStorage` | Cleared when tab closes | Still vulnerable to XSS |
| **httpOnly Cookie** | Not accessible to JS → protects against XSS | Vulnerable to **CSRF** unless mitigated (SameSite cookies, CSRF tokens) |
| In-memory (JS variable) | Not accessible to other scripts persistently | Lost on refresh; needs a refresh-token flow to re-fetch |

**Common recommended pattern**: Access token in memory (or short-lived httpOnly cookie), refresh token in a `Secure`, `httpOnly`, `SameSite=Strict` cookie.

---

## 9. Common Vulnerabilities & Attacks

1. **`alg: none` attack** — Attacker crafts a token with `"alg": "none"` and no signature; poorly implemented verifiers accept it as valid. **Fix**: always explicitly whitelist accepted algorithms server-side.

2. **Algorithm confusion (RS256 → HS256)** — If a server expects `RS256` (asymmetric) but the verification code doesn't enforce it, an attacker can take the public key (often publicly available) and use it as an HMAC secret to sign a fake token with `HS256`. **Fix**: explicitly specify and enforce the expected algorithm when verifying.

3. **Weak secrets** — If using HMAC (`HS256`) with a short/guessable secret, attackers can brute-force it offline. **Fix**: use long, random, high-entropy secrets (32+ bytes).

4. **No expiration / long expiration** — Tokens that never expire are dangerous if leaked. **Fix**: always set `exp`, keep access tokens short-lived.

5. **Sensitive data in payload** — Payload is only encoded, not encrypted; don't store passwords, SSNs, etc. **Fix**: keep payload minimal (user ID, role); use JWE (encrypted JWT) if you truly need confidentiality.

6. **No revocation mechanism** — A stolen-but-not-yet-expired token remains valid. **Fix**: short expirations + refresh-token revocation list / blocklist for critical scenarios.

7. **Token replay** — A valid token intercepted (e.g. over non-HTTPS) can be reused by an attacker. **Fix**: always use HTTPS; consider `jti` + a short-lived nonce store for extra-sensitive operations.

8. **Cross-Site Scripting (XSS)** if stored in `localStorage`/`sessionStorage` — malicious script can steal the token. **Fix**: prefer httpOnly cookies, sanitize inputs, use CSP headers.

9. **Cross-Site Request Forgery (CSRF)** if stored in cookies — Fix: `SameSite=Strict/Lax` cookies + CSRF tokens for state-changing requests.

---

## 10. Best Practices

- ✅ Always use **HTTPS** — tokens sent over plain HTTP can be intercepted.
- ✅ Set a **short expiration** (`exp`) on access tokens (5–60 minutes typical).
- ✅ Use **refresh tokens** for long-lived sessions, stored securely and revocably.
- ✅ Explicitly whitelist the **signing algorithm** on the verifier side — never trust the `alg` field in the token blindly.
- ✅ Keep the **payload minimal** — just enough to identify/authorize the user.
- ✅ Use strong, random secrets (HMAC) or proper key pairs (RSA/ECDSA), and **rotate keys periodically**.
- ✅ Validate **all relevant claims** on every request: `exp`, `nbf`, `iss`, `aud`.
- ✅ Store tokens as securely as possible on the client (httpOnly cookies > memory > localStorage).
- ✅ Implement **logout** by clearing client-side storage and, where possible, revoking refresh tokens server-side.
- ✅ Log and monitor for anomalous token usage (e.g., same token used from wildly different IPs/geolocations).
- ❌ Don't put secrets, passwords, or excessive PII in the payload.
- ❌ Don't rely on JWTs for information that must be instantly revocable without a supporting revocation mechanism.

---

## 11. Revocation & Logout Strategies

JWTs are stateless by design, which makes "invalidating" a token before its natural expiry tricky. Common approaches:

1. **Short expiration + refresh tokens** — Minimize the damage window; don't bother revoking access tokens, just let them expire quickly, and revoke the refresh token instead.

2. **Blocklist / denylist** — Maintain a store (e.g., Redis) of revoked token IDs (`jti`) or user IDs whose tokens should be rejected until a certain time. Every request checks this list — this reintroduces some statefulness but only for revoked tokens (much smaller than a full session store).

3. **Token versioning** — Store a `token_version` (or `password_changed_at`) field on the user record. Include the version in the JWT. On verification, compare token's version to current DB version; mismatched = invalid. Useful for "log out all devices" or "invalidate after password change."

4. **Allowlist (opposite approach)** — Only tokens present in a server-side store are considered valid (closer to session-based auth; sacrifices some statelessness benefits).

---

## 12. Advanced Topics

### 12.1 JWE vs JWS
- **JWS (JSON Web Signature)** — what people usually mean by "JWT": signed, but payload is readable (Base64 only).
- **JWE (JSON Web Encryption)** — the payload itself is encrypted, not just signed. Use JWE when the payload contains data that must stay confidential even from the client holding the token.

### 12.2 JWK & JWKS (JSON Web Key / Key Set)
- A **JWK** is a JSON representation of a cryptographic key.
- A **JWKS** is a set of JWKs, typically exposed at a `/.well-known/jwks.json` endpoint by an identity provider (e.g., Auth0, Google, Okta).
- Services verifying tokens fetch the issuer's JWKS to get the current public key(s) — this enables **key rotation** without downtime, since multiple keys (old + new) can be published simultaneously, each identified by a `kid` (Key ID) in the JWT header.

### 12.3 `kid` (Key ID) Header
Identifies which key (from a JWKS) was used to sign the token, so the verifier knows which public key to use — critical for supporting key rotation.

### 12.4 OAuth2 / OpenID Connect (OIDC) and JWT
- OAuth2 defines **authorization** (delegated access) — access tokens *may* be JWTs, but the spec doesn't require it.
- **OpenID Connect** (built on top of OAuth2) explicitly uses JWTs for the **ID Token**, which carries identity/authentication claims (`sub`, `email`, `name`, etc.).
- So: "logging in with Google" → the ID Token you get back is a JWT signed by Google, verifiable using Google's published JWKS.

### 12.5 Multi-tenant Claims
In SaaS/multi-tenant apps, JWTs often carry a `tenant_id` or `org_id` claim so that a single auth server can issue tokens scoped to a particular organization/workspace, and downstream services can apply tenant isolation directly from the token.

### 12.6 Token Introspection (Opaque Tokens Alternative)
Sometimes systems use **opaque tokens** (random strings, not JWTs) + a `/introspect` endpoint (per OAuth2 spec, RFC 7662) that the resource server calls to check validity. This trades statelessness for instant revocability — essentially a middle ground between sessions and JWTs.

### 12.7 Clock Skew
Distributed systems may have slightly different clocks. Verifiers often allow a small **leeway** (e.g., 30–60 seconds) when checking `exp`/`nbf` to avoid false rejections due to clock drift.

---

## 13. JWT in Practice (Python / FastAPI example)

Using `fastapi-users` (as in a typical FastAPI JWT setup):

```python
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

SECRET = "your-long-random-secret"  # In production: load from env var, not hardcoded!

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)  # 1 hour expiry

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
```

What happens under the hood:
- `BearerTransport` tells the library to expect the token in the `Authorization: Bearer <token>` header.
- `JWTStrategy` handles encoding/decoding using the `SECRET` (HMAC, i.e., `HS256` by default) and sets the `exp` claim automatically based on `lifetime_seconds`.
- On each protected request, the dependency (e.g. `current_active_user`) decodes and verifies the token, extracts the user ID (`sub`), and loads the user from the DB.

Manual decode/encode with `PyJWT` for comparison:

```python
import jwt
import datetime

SECRET = "your-long-random-secret"

# Encoding (creating a token)
payload = {
    "sub": "user_id_123",
    "role": "admin",
    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
}
token = jwt.encode(payload, SECRET, algorithm="HS256")

# Decoding (verifying a token)
try:
    decoded = jwt.decode(token, SECRET, algorithms=["HS256"])  # explicitly whitelist algorithm!
except jwt.ExpiredSignatureError:
    print("Token expired")
except jwt.InvalidTokenError:
    print("Invalid token")
```

---

## 14. Quick Reference Cheat Sheet

- **Structure**: `Header.Payload.Signature` (Base64Url-encoded, dot-separated)
- **Encoded, not encrypted** — never store secrets in the payload
- **`exp`** = expiration, **`iat`** = issued at, **`sub`** = subject/user ID
- **HS256** = shared secret (symmetric); **RS256/ES256** = public/private key pair (asymmetric)
- Always whitelist algorithms on verification — never trust the token's own `alg` header blindly
- Short-lived access tokens + longer-lived, revocable refresh tokens
- Prefer httpOnly, Secure, SameSite cookies over localStorage for storage
- Revocation isn't free with JWTs — plan for it (blocklist, versioning, or short expiry)
- Always use HTTPS
