# FastAPI: From Zero to Production

> A guide to FastAPI with modern Python type hints and Pydantic v2 style.

## 1. What FastAPI is

**FastAPI** is a Python framework for building HTTP APIs. You describe an endpoint with normal Python functions and type annotations; FastAPI uses those annotations to:

- read data from the request;
- validate and convert it;
- produce helpful errors when it is invalid;
- generate an OpenAPI schema automatically;
- expose interactive documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc).

It is built on **Starlette** (ASGI web layer: requests, responses, middleware, WebSockets) and **Pydantic** (data parsing/validation/serialization).

### The mental model

```
client -> HTTP request -> ASGI server (Uvicorn) -> FastAPI route
       -> parse + validate -> dependencies -> your function -> response validation
       -> JSON/other HTTP response
```

An API has **resources** (users, products, orders) and **operations** (create, read, update, delete). HTTP gives the operation meaning:

| Intent | Usual method | Example |
|---|---|---|
| Read | `GET` | `GET /products/42` |
| Create | `POST` | `POST /products` |
| Replace | `PUT` | `PUT /products/42` |
| Partial update | `PATCH` | `PATCH /products/42` |
| Delete | `DELETE` | `DELETE /products/42` |

`GET` should not change data. `PUT` is normally idempotent: repeating the same request has the same resulting state. `POST` commonly is not.

## 2. Install and run

Use a virtual environment in a real project.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install "fastapi[standard]"
```

Create `main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Store API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI"}
```

Run during development:

```bash
fastapi dev main.py
# Alternative: uvicorn main:app --reload
```

`main:app` means: import the `app` object from module `main`. Visit `http://127.0.0.1:8000/docs`.

## 3. Routes and path operations

A **path operation** is a function attached to an HTTP method and URL path.

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.get("/health", status_code=status.HTTP_200_OK, tags=["system"])
async def health_check():
    return {"ok": True}
```

Useful decorator arguments:

- `response_model`: response contract and filtering.
- `status_code`: successful HTTP status.
- `tags`: groups routes in docs.
- `summary`, `description`, `responses`: documentation/OpenAPI metadata.
- `dependencies`: dependencies that run even when their return values are unused.
- `deprecated=True`, `include_in_schema=False`: API lifecycle/docs control.

### Path parameters

Values in braces are extracted from the URL. Their Python type controls validation.

```python
from uuid import UUID
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: UUID):
    return {"id": user_id}
```

`/users/not-a-uuid` returns a 422 validation response; your function is not called. Route order matters when paths overlap: declare `/users/me` before `/users/{user_id}`.

### Query parameters

Function arguments not found in the path become query parameters.

```python
from typing import Annotated
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/products")
async def list_products(
    q: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    tags: list[str] = [],
):
    return {"q": q, "page": page, "size": size, "tags": tags}
```

Example: `/products?q=book&page=2&tags=python&tags=api`. Prefer `Annotated[T, Query(...)]`: it keeps type `T` clear while attaching FastAPI metadata. Avoid a mutable default in ordinary Python functions, though FastAPI handles parameter defaults safely; `default_factory` is clearer in request models.

### Headers and cookies

```python
from typing import Annotated
from fastapi import Header, Cookie

@app.get("/whoami")
async def whoami(
    user_agent: Annotated[str | None, Header()] = None,
    session: Annotated[str | None, Cookie()] = None,
):
    return {"user_agent": user_agent, "has_session": session is not None}
```

By default, `user_agent` maps to header `user-agent`. Set `convert_underscores=False` only when a nonstandard header truly needs underscores.

## 4. Request bodies and Pydantic models

For JSON bodies, define a class inheriting from `BaseModel`.

```python
from pydantic import BaseModel, Field, EmailStr, field_validator

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, examples=["Mechanical keyboard"])
    price: float = Field(gt=0)
    in_stock: bool = True
    owner_email: EmailStr | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()
```

```python
@app.post("/products", status_code=201)
async def create_product(product: ProductCreate):
    return product
```

FastAPI reads the JSON body, asks Pydantic to validate it, and hands a typed `ProductCreate` instance to the function. A body is not automatically a database record—validate first, then persist using a repository/service.

### Nested data, optionality, and aliases

```python
from pydantic import BaseModel, ConfigDict, Field

class Address(BaseModel):
    city: str
    country: str = "IN"

class CustomerCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    full_name: str = Field(alias="fullName", min_length=1)
    address: Address | None = None
    labels: set[str] = Field(default_factory=set)
```

- `str` means required string.
- `str | None` permits `null`; it is still required unless it also has a default (`= None`).
- `list[Thing]`, `dict[str, int]`, `set[str]` support nested validation.
- `Field` supplies constraints, examples, aliases, titles, and descriptions.
- `model_dump()` produces a Python dictionary; `model_dump(exclude_unset=True)` is key for PATCH.
- `model_validate(obj)` validates data into a model; `model_validate` with `from_attributes=True` supports ORM-style objects.

### Separate input and output schemas

Never casually return a model with a password hash, internal flag, or secret merely because it was convenient.

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)

class UserPublic(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

@app.post("/users", response_model=UserPublic, status_code=201)
async def create_user(payload: UserCreate) -> UserPublic:
    saved = {"id": 1, "email": payload.email, "is_active": True,
             "password_hash": "do-not-leak"}
    return saved  # response_model filters password_hash
```

`response_model` is both a client-facing contract and a security boundary. Return annotations are useful too; use `response_model` when filtering or richer OpenAPI control is needed.

### PATCH correctly

Use a model whose fields are optional, then apply only fields supplied by the client.

```python
class ProductPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    price: float | None = Field(default=None, gt=0)
    in_stock: bool | None = None

@app.patch("/products/{product_id}")
async def patch_product(product_id: int, changes: ProductPatch):
    update_data = changes.model_dump(exclude_unset=True)
    # repository.update(product_id, update_data)
    return {"id": product_id, **update_data}
```

`exclude_unset=True` distinguishes a missing field from a deliberately supplied `null` (provided the schema allows null).

## 5. Validation and error handling

Validation failures are automatically returned as **422 Unprocessable Content**. They contain a `detail` list identifying the failing location and rule. Do not catch them just to return a vague 400.

For expected application errors, raise `HTTPException`:

```python
from fastapi import HTTPException, status

def require_product(product_id: int) -> dict:
    product = None  # lookup
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product
```

Common meanings: 200 success; 201 created; 202 accepted for later work; 204 successful with no body; 400 malformed/invalid request; 401 unauthenticated (normally includes `WWW-Authenticate`); 403 authenticated but forbidden; 404 absent; 409 conflict; 422 structurally valid but validation failed; 429 rate limited; 500 unexpected server error.

### Custom exception handlers

Use domain exceptions in business code and translate them at the HTTP edge.

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class ProductMissing(Exception):
    def __init__(self, product_id: int): self.product_id = product_id

@app.exception_handler(ProductMissing)
async def product_missing_handler(_: Request, exc: ProductMissing):
    return JSONResponse(status_code=404, content={"detail": f"Product {exc.product_id} not found"})
```

Do not expose tracebacks, SQL errors, or tokens to clients. Log unexpected exceptions with request context; return a generic response.

## 6. Responses, status, files, and streaming

FastAPI normally JSON-encodes your return value. For special behavior, return a response object.

```python
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, StreamingResponse

@app.get("/landing", response_class=HTMLResponse)
async def landing():
    return "<h1>Welcome</h1>"

@app.get("/old")
async def old():
    return RedirectResponse("/new", status_code=307)

@app.get("/report")
async def report():
    return FileResponse("reports/monthly.pdf", media_type="application/pdf", filename="monthly.pdf")
```

For a large generated response, use `StreamingResponse` with an iterator/async iterator. For a `204`, return no content. Do not send a JSON body with it.

To set cookies or headers while retaining response-model processing:

```python
from fastapi import Response

@app.post("/login")
async def login(response: Response):
    response.set_cookie("session", "signed-value", httponly=True, secure=True, samesite="lax")
    response.headers["X-Request-ID"] = "..."
    return {"ok": True}
```

Use `httponly`, `secure`, and an appropriate `samesite` policy for browser session cookies. Do not put sensitive credentials in a URL query string.

## 7. Dependency injection (the central FastAPI pattern)

A **dependency** is a callable FastAPI runs and injects into an endpoint. It can read headers/query/body, return a value, raise errors, and itself depend on other dependencies.

```python
from typing import Annotated
from fastapi import Depends, Header, HTTPException

async def verify_api_key(x_api_key: Annotated[str, Header()]) -> str:
    if x_api_key != "expected-key":
        raise HTTPException(401, "Invalid API key")
    return x_api_key

ApiKey = Annotated[str, Depends(verify_api_key)]

@app.get("/private")
async def private_area(_: ApiKey):
    return {"message": "allowed"}
```

Why dependencies matter: shared pagination, authentication, authorization, DB sessions, tenant resolution, request tracing, configuration, and reusable service construction without globals.

### Dependency graph and caching

Dependencies can have dependencies. FastAPI solves the graph per request and normally reuses the same dependency result if requested multiple times. Use `Depends(dep, use_cache=False)` only when it must run again.

### Resources with `yield`

Code before `yield` acquires the resource; code after it cleans up even if the endpoint raises.

```python
def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

DbSession = Annotated[object, Depends(get_db)]
```

This is the normal shape for a request-scoped database session. Keep commit/rollback policy explicit: many teams commit in the service/use-case layer and roll back on exceptions.

### Dependency overrides in tests

```python
app.dependency_overrides[get_db] = lambda: fake_session
# run test
app.dependency_overrides.clear()
```

This is a clean way to substitute databases, current users, external clients, and settings.

## 8. Database design and ORM integration

FastAPI does not impose a database or ORM. Common choices include SQLAlchemy/SQLModel for SQL, or database-specific async clients. Key rule: match your access library to your concurrency model.

Recommended layers:

```
router (HTTP) -> service/use case (business rules) -> repository (persistence) -> database
```

- **Router**: HTTP parsing, dependency injection, status code, response schema.
- **Service**: business rules and transactions.
- **Repository**: queries and persistence abstraction.
- **Schema**: API DTOs, separate from ORM entities.

Avoid a giant `main.py`, raw database calls throughout routers, and a shared database session across requests. Apply migrations with a tool such as Alembic; do not create production schema as an import side effect.

### Async database caution

An `async def` route is not magically non-blocking. A synchronous ORM query inside it can block the event loop. Either use an async driver/session and `await` its calls, or make a route/dependency `def` when using blocking libraries so FastAPI can run that callable in its threadpool. CPU-heavy work needs a worker/process, not merely `async`.

## 9. Application structure and routers

As projects grow, split by domain. Example:

```
app/
  main.py                 # create app, middleware, include routers
  core/config.py           # settings
  api/routes/users.py      # HTTP endpoints
  api/deps.py              # common dependencies
  schemas/user.py          # Pydantic input/output models
  services/users.py        # use cases
  repositories/users.py    # persistence
  db/session.py
  tests/
```

```python
# app/api/routes/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id}

# app/main.py
from fastapi import FastAPI
from app.api.routes import users

app = FastAPI()
app.include_router(users.router, prefix="/api/v1")
```

The final route is `/api/v1/users/{user_id}`. Put versioning in a path (`/api/v1`) when long-lived external clients need a clear compatibility boundary.

## 10. Security: authentication is not authorization

- **Authentication**: who is calling? (token/session/API key)
- **Authorization**: may this caller do this action? (roles, ownership, scopes, policies)

Authentication must be paired with authorization; knowing a user ID is not enough. Enforce authorization server-side for every sensitive action—never trust a frontend role flag.

### Bearer-token extraction

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = verify_and_decode_token(token)  # validate signature, expiry, audience, issuer
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
```

`OAuth2PasswordBearer` primarily describes/extracts a Bearer token; it does not itself issue or cryptographically validate tokens. Use reputable password hashing (Argon2/bcrypt via a maintained library), short-lived access tokens, secure refresh-token storage/rotation where appropriate, and secrets from environment/secret managers—not source code.

For third-party identity, prefer standards-based OAuth2/OIDC flows and validate issuer, audience, signature, expiry, and required claims. Use `Security(..., scopes=[...])` when OAuth2 scopes should appear in OpenAPI.

### CORS and browser security

Browsers enforce CORS; servers and non-browser clients do not. Configure exact trusted origins:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Do not use `allow_origins=["*"]` with credentials. CORS is not authorization. For cookie authentication, also understand CSRF defenses; `SameSite` helps but is not a universal replacement for a CSRF strategy.

## 11. Middleware, lifespan, static files, templates

**Middleware** wraps every request/response. Common use: correlation IDs, timing, security headers, logging. Keep it small and avoid reading large bodies unnecessarily.

```python
import time
from fastapi import Request

@app.middleware("http")
async def timing(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.perf_counter() - started)
    return response
```

Use **lifespan** for resources shared for the whole application—connection pools, long-lived HTTP clients, loaded models.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = make_client()
    yield
    await app.state.http_client.aclose()

app = FastAPI(lifespan=lifespan)
```

Lifespan is app-scoped; a dependency with `yield` is request-scoped. `app.state` is acceptable for shared infrastructure, but do not store per-user/request mutable state there.

Mount `StaticFiles` for assets and use Starlette/Jinja templates only when FastAPI also serves HTML. An API-only backend usually serves JSON and lets another app handle UI.

## 12. Async, concurrency, and background work

Use `async def` if the work it awaits is asynchronous I/O (async database, HTTP client, WebSocket). Use normal `def` for blocking I/O libraries when FastAPI calls the route/dependency. Never call blocking `requests`, file/network operations, or long CPU work directly in an async route.

```python
@app.get("/remote")
async def remote():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://example.com")
    return response.json()
```

**Concurrency** means progressing multiple waiting tasks; **parallelism** means executing work at the same time on separate CPU cores. Async improves I/O-bound concurrency, not heavy computation.

`BackgroundTasks` runs small work after returning the response, in the same application process:

```python
from fastapi import BackgroundTasks

def send_email(address: str): ...

@app.post("/signup", status_code=202)
async def signup(email: str, tasks: BackgroundTasks):
    tasks.add_task(send_email, email)
    return {"accepted": True}
```

For durable/retryable/CPU-heavy jobs (email campaigns, video processing, reports), use a real queue and worker system. Process restart can lose in-process background tasks.

## 13. File uploads, forms, and WebSockets

Uploads are `multipart/form-data`, not JSON. Install the multipart dependency required by your environment.

```python
from typing import Annotated
from fastapi import File, UploadFile

@app.post("/files")
async def upload(file: Annotated[UploadFile, File()]):
    # stream/read in bounded chunks for large files; validate type and size yourself
    return {"name": file.filename, "content_type": file.content_type}
```

`UploadFile` is preferable for substantial uploads because it is file-like and supports async methods. Treat file names and claimed MIME types as untrusted; enforce size/type, scan where required, create server-side names, and store outside public paths.

Forms use `Form(...)`. For browser login forms, do not combine a JSON `Body` model and a multipart upload in one request—the content type can only be one format.

WebSockets provide persistent, bidirectional connections:

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            message = await ws.receive_text()
            await ws.send_text(f"echo: {message}")
    except WebSocketDisconnect:
        pass
```

For multi-instance real-time systems, use a shared broker/pub-sub layer; one process cannot broadcast to clients connected to another process by itself.

## 14. Testing

Test HTTP behavior, not only internal functions. `TestClient` is ideal for basic synchronous tests.

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
```

For async tests, use an async client/ASGI transport and your test framework's async support. Tests should cover:

- success, malformed input (422), unauthenticated (401), forbidden (403), missing (404), conflict (409);
- response shape (especially that secrets are absent);
- authorization ownership/role boundaries;
- database transaction rollback/isolation;
- dependency overrides for external systems;
- lifecycle behavior and WebSockets when used.

Use a separate test database or transactions that roll back. Never point automated tests at production data.

## 15. Observability and reliability

Production APIs need answers to: what failed, for whom, where, how often, and how slowly?

- **Structured logs**: JSON/key-value logs with request ID, route, method, status, duration; never log passwords/tokens/PII casually.
- **Metrics**: request count, error rate, latency percentiles, active connections, queue depth.
- **Tracing**: follows a request across services; propagate trace/correlation IDs.
- **Health checks**: liveness says process is alive; readiness says it can accept traffic (for example DB dependency is available). Keep them cheap and avoid leaking details publicly.
- **Timeouts/retries**: every outbound call needs a timeout. Retry only transient and idempotent operations, with exponential backoff and jitter.

Rate limit, request-size limit, and abuse protection are usually implemented at the gateway/reverse proxy or a dedicated library/store. Make write operations idempotent with an idempotency key if clients may retry after uncertain network failure.

## 16. Deployment

FastAPI is ASGI, so it is served by an ASGI server such as Uvicorn. Development uses reload; production must not.

```bash
fastapi run app/main.py
# Or an ASGI process manager/server configuration appropriate to your platform
```

Production checklist:

- terminate HTTPS at a trusted proxy/load balancer or configure TLS safely;
- run startup migrations as a controlled deployment step, not in every worker;
- supply configuration through environment variables/secrets manager;
- set resource limits and graceful shutdown;
- use multiple replicas/processes only when state is externalized (DB, cache, broker);
- configure trusted proxy headers correctly; do not blindly trust client-supplied forwarding headers;
- use a container health check and rolling deployment strategy;
- pin dependencies and scan/update them regularly.

### Configuration with Pydantic Settings

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    debug: bool = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Keep `.env` local and out of version control. Environment variables are strings; settings parses them. Cache settings per process, while allowing overrides in tests.

## 17. OpenAPI and API quality

FastAPI generates OpenAPI from types, routes, `response_model`, dependencies, and security definitions. Treat it as an API contract:

- give routes useful `summary`, `description`, tags, and examples;
- document expected non-2xx responses;
- use stable field names and deliberate deprecation/versioning;
- model error responses consistently;
- do not expose internal/admin routes in public docs (`include_in_schema=False` when appropriate).

An ergonomic endpoint is predictable: nouns in paths, correct HTTP semantics, pagination for collections, filtering/sorting conventions, clear errors, and no breaking response changes without versioning/migration.

## 18. Advanced patterns and common traps

### Conditional fields and cross-field rules

Use Pydantic model validators for rules involving several fields (for example `end > start`). Keep domain rules that need database state in a service, not a schema validator.

### Generic pagination

Use a standard envelope such as `{items, page, size, total}`. For very large/changing collections, cursor pagination is safer than offset pagination because offsets can drift and get slower.

### Multi-tenancy

Resolve tenant from an authenticated claim/subdomain/header dependency; apply it to **every** query and authorization check. Never accept a tenant ID from a client and assume it grants access.

### Request context

Use dependencies or middleware to establish request IDs and current-user context. Pass important context explicitly into services rather than hiding business behavior in globals.

### Avoid these mistakes

| Mistake | Better approach |
|---|---|
| One giant `main.py` | Routers, schemas, services, repositories |
| Returning ORM objects/secrets directly | Explicit public response models |
| Blocking code in `async def` | Async library or sync route/threadpool; job worker for CPU |
| Shared DB session/global mutable user state | Request-scoped dependency / external state |
| `*` CORS with cookies | Exact origins and deliberate browser security |
| JWT decode without full validation | Verify signature, expiry, issuer/audience and claims |
| BackgroundTasks for critical jobs | Durable queue/worker with retries/monitoring |
| Catch-all `except Exception` returning 200 | Correct errors; log unexpected exceptions |
| `PUT` pretending to be PATCH | Use required replacement fields or implement PATCH |
| Auto-running destructive migrations | Controlled migration pipeline and backups |

## 19. A compact production-style example

```python
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)

class ItemPublic(ItemCreate):
    id: int

items: dict[int, dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize shared resources here
    yield
    # close them here

app = FastAPI(title="Items API", version="1.0.0", lifespan=lifespan)

async def get_current_user() -> dict:
    # Replace with token validation + user lookup
    return {"id": 7, "role": "user"}

CurrentUser = Annotated[dict, Depends(get_current_user)]

@app.post("/api/v1/items", response_model=ItemPublic, status_code=status.HTTP_201_CREATED, tags=["items"])
async def create_item(payload: ItemCreate, user: CurrentUser):
    item_id = len(items) + 1
    item = {"id": item_id, **payload.model_dump(), "owner_id": user["id"]}
    items[item_id] = item
    return item

@app.get("/api/v1/items/{item_id}", response_model=ItemPublic, tags=["items"])
async def read_item(item_id: int, user: CurrentUser):
    item = items.get(item_id)
    if item is None:
        raise HTTPException(404, "Item not found")
    if item["owner_id"] != user["id"]:
        raise HTTPException(403, "Not allowed")
    return item
```

This example deliberately uses memory only to demonstrate concepts. Production replaces it with a database/repository, robust authentication, migrations, logging, tests, and externalized shared state.

## 20. Learning sequence and cheat sheet

1. Python typing, functions, virtual environments, HTTP/JSON.
2. Routes, path/query/header parameters, status codes.
3. Pydantic models, validation, input/output schemas.
4. Errors, dependencies, routers.
5. Database sessions, migrations, service boundaries.
6. Authentication and authorization.
7. Async rules, testing, uploads/WebSockets as needed.
8. Observability, security hardening, deployment.

**Remember:** types are your API declaration; Pydantic validates data; dependencies compose cross-cutting behavior; response models protect the public contract; `async` is for non-blocking I/O; production quality comes from security, tests, observability, and operational design—not just fast endpoints.

## Official references

- [FastAPI tutorial and reference](https://fastapi.tiangolo.com/)
- [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Async and concurrency](https://fastapi.tiangolo.com/async/)
- [Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [Deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/)
