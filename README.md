# Day 22 Practice Project — Authenticate and Authorize the Library Lending API

Not a new app. Take your Day 16 project (SQLAlchemy + SQLite + Alembic, two migrations applied) and add complete authentication and authorization to it, using everything from Days 17–21. All config and secrets move to `BaseSettings` + `.env`. Everything is `def`. The only `async def` in the project is still the logging middleware.

---

## What stays the same

- All Day 11/16 business rules: availability check, loan limits (3 basic / 10 premium), loan periods (14 / 30 days), ISBN validation, email/ISBN uniqueness (DB-enforced).
- `LibraryError` hierarchy and the **single** global exception handler. Auth failures must come back in the same `{"error": {"type", "message"}}` shape as everything else.
- Eager loading on `GET /loans` and `GET /loans/{id}`. Adding auth must not reintroduce N+1.
- `Publisher`, `Book`, `Loan` models and their relationships.

## What changes

- **`Member` gets an owner.** A new `User` table is the authentication identity (email, password hash, role, active flag). `Member` stays the library profile (name, membership type). `Member.user_id` is a nullable, unique FK to `users.id`. Relationship: `User.member` (`uselist=False`) / `Member.user`, with `back_populates`.
  - Nullable because (a) members already in your DB from Day 16 have no user, and (b) admin users have no member profile.
  - Those legacy members simply cannot log in. Leave them; don't write a data migration.
- **`require_admin` (X-API-Key header, hardcoded `"admin-secret-123"`) is deleted entirely.** Not deprecated, not kept alongside. JWT + roles replaces it.
- **`POST /members` is removed.** Registration is now `POST /auth/register`.
- **Every hardcoded config value moves to `Settings`:** DB URL, CORS origins, JWT secret/algorithm/expiry, rate-limit string, bootstrap admin credentials.

---

## Required project structure

```
library_api/
├── main.py                   # CHANGED — auth router, limiter, settings-driven CORS
├── config.py                 # NEW — Settings, get_settings
├── .env                      # NEW — never committed
├── .env.example              # NEW — committed, placeholder values only
├── .gitignore                # CHANGED
├── database.py               # CHANGED — URL from settings
├── alembic.ini
├── alembic/                  # CHANGED — env.py reads URL from settings; 3rd migration
├── core/
│   ├── exceptions.py         # CHANGED — auth errors, optional headers
│   ├── security.py           # NEW — hashing + JWT encode/decode, no FastAPI imports
│   └── permissions.py        # NEW — pure authorization policy functions
├── models/
│   ├── user.py               # NEW
│   ├── member.py             # CHANGED — user_id FK
│   └── ...
├── routers/
│   ├── auth.py               # NEW
│   └── ...                   # books / members / loans CHANGED
├── schemas/
│   ├── auth.py               # NEW
│   └── ...
├── services/
│   ├── auth_service.py       # NEW
│   └── ...                   # member / loan services CHANGED
├── scripts/
│   └── create_admin.py       # NEW
├── dependencies.py           # CHANGED
└── middleware.py
```

`core/security.py` takes everything it needs as arguments (secret, algorithm, expiry). It does not import FastAPI or read global settings. `core/permissions.py` is the same idea for authorization: plain functions of `(user, resource)` that return a bool or raise `ForbiddenError`, so the rules are testable without HTTP. This is the Day 9 principle applied to auth: policy in plain Python, HTTP concerns in dependencies/routers.

---

## Roles

`Role(str, Enum)` with two values: `member` and `admin`. No `user.role == "admin"` string comparisons scattered through routers.

- **Role is never accepted from the client.** No `role` field on any request schema. Registration always creates `role=member`. A test will send `{"role": "admin"}` in the register body and confirm it's ignored or rejected (your call which — be consistent with how your other schemas treat extra fields).
- **Role is not authoritative in the token.** The JWT carries identity only. `get_current_user` loads the `User` row on every request and reads `role` and `is_active` from the DB. Consequence: a role change or deactivation takes effect on the next request, not at token expiry. Cost: one extra query per authenticated request. You should be able to explain why that trade is being made.
- **The first admin** comes from `scripts/create_admin.py`, which reads `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` from `Settings`, hashes the password, and inserts the user. It must be idempotent (running twice does not create a second admin or crash). Not a startup hook — your schema is Alembic-managed and startup side effects hide.

---

## Endpoints

### New: `routers/auth.py`

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/auth/register` | Public. Body: `name`, `email`, `password`. 201. Creates `User` **and** `Member` in one transaction (`membership_type=basic`, always). Returns the member profile, never the hash. |
| POST | `/auth/login` | Public. `OAuth2PasswordRequestForm` (form data, not JSON). Returns `{"access_token", "token_type": "bearer"}`. Rate limited. |
| GET | `/auth/me` | Any authenticated user. Returns user id, email, role, and member profile if one exists. |

### Permission matrix for existing endpoints

| Endpoint | Anonymous | `member` | `admin` |
| --- | --- | --- | --- |
| `GET /books`, `/books/available`, `/books/{id}` | ✅ | ✅ | ✅ |
| `POST /books`, `PATCH /books/{id}`, `DELETE /books/{id}` | ❌ 401 | ❌ 403 | ✅ |
| `GET /members` | ❌ 401 | ❌ 403 | ✅ |
| `GET /members/{id}` | ❌ 401 | own only | any |
| `PATCH /members/{id}` | ❌ 401 | own only, **`name` only** | any, `name` + `membership_type` |
| `POST /loans` | ❌ 401 | body `member_id` must be own | any `member_id` |
| `GET /loans` | ❌ 401 | own loans only | all (with filters) |
| `GET /loans/overdue` | ❌ 401 | ❌ 403 | ✅ |
| `GET /loans/{id}` | ❌ 401 | own only | any |
| `PATCH /loans/{id}/return` | ❌ 401 | ❌ 403 | ✅ (returns are processed at the desk) |

The body shape of `POST /loans` (`member_id`, `book_id` as two `Body(embed=True)` params) is unchanged.

### Rules behind the matrix

1. **401 vs 403.** 401 = no valid credentials (missing, malformed, expired, bad signature, user gone/inactive). 403 = valid credentials, role insufficient. 401 responses carry `WWW-Authenticate: Bearer`.
2. **Object-level denial returns 404, not 403.** A `member` requesting someone else's member/loan gets the same `MemberNotFoundError` / `LoanNotFoundError` response, byte-for-byte, as a nonexistent id. Role-level denial (non-admin on an admin-only route) stays 403. Reason: a 403 on `/loans/7` confirms loan 7 exists. For `/members/{id}`, compare against the caller's own member id **before** any lookup so the nonexistent and not-yours paths are the same code path.
3. **`POST /loans` with a foreign `member_id` → 403** `ForbiddenError`, no lookup of that member first.
4. **`membership_type` is privileged.** A non-admin sending it on `PATCH /members/{id}` gets 403. Otherwise a basic member promotes themselves to premium and bypasses the loan limit. This is field-level authorization; it can't be expressed with a role dependency alone.
5. **List filtering happens in the SQL query**, not by filtering a Python list after fetching. For a `member`, `GET /loans` adds `WHERE loans.member_id = :own` before `OFFSET/LIMIT`. Post-filtering after pagination returns short or empty pages. If a `member` passes `?member_id=<other>`, return 403.
6. **Email is not independently patchable.** `User.email` is the login identity and `Member.email` mirrors it from registration. If your `MemberUpdate` currently allows email, remove it for now; two diverging copies of an identity is a bug you don't want.

---

## Security requirements

### Passwords (Day 17)

- bcrypt directly (no passlib). Hash on register and in `create_admin.py`; never store, log, or return plaintext or the hash.
- Validate at the schema: min 8 characters, max **72 bytes** (UTF-8 encoded, not characters). bcrypt only uses the first 72 bytes, and recent bcrypt versions raise `ValueError` past that — unvalidated, that's a 500 on register. Use `field_validator`.
- Emails are normalized (`strip().lower()`) on register **and** login. SQLite's `UNIQUE` on text is case-sensitive, so `A@x.com` and `a@x.com` would otherwise be two accounts.

### Login (Day 18)

- Unknown email and wrong password return the **same** `InvalidCredentialsError` (401, same message). Not enough on its own: bcrypt verification is deliberately slow, so "user not found → return immediately" is measurably faster than "user found → verify → mismatch" and leaks which emails exist. When the user isn't found, run `verify_password` against a fixed dummy hash anyway.
- An inactive user with the correct password also gets the same 401. A distinct "account disabled" response confirms the password was right.
- Rate limit `/auth/login` and `/auth/register` with slowapi (limit string from `Settings`). Exceeding it returns 429 — and must also come back through your error shape, so wire slowapi's `RateLimitExceeded` into a handler that produces it.

### JWT (Day 18)

- PyJWT. Claims: `sub` = `str(user.id)` (recent PyJWT versions reject a non-string `sub` on decode), `iat`, `exp`. Nothing else.
- Decode with `algorithms=[settings.jwt_algorithm]` — an explicit list from config, never anything read from the token header.
- Expiry in minutes from `Settings`.
- Every decode failure (expired, bad signature, malformed, missing `sub`, `sub` not parseable, user not found, user inactive) collapses to one `NotAuthenticatedError` (401). Don't give the client a taxonomy of failure reasons.

### Dependency chain (Day 19)

```
oauth2_scheme  →  get_current_user  →  require_role(Role.admin)
                                    →  object-level checks (via core/permissions.py)
```

- `OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)`. With the default `auto_error=True` the scheme raises FastAPI's own `HTTPException` and your response is `{"detail": "Not authenticated"}`, bypassing your handler. With `False` it returns `None` and you raise `NotAuthenticatedError` yourself.
- `require_role(*roles)` is the dependency-factory pattern from Day 19, replacing the old `require_admin`.
- `LibraryError` gains an optional `headers` attribute, and the global handler forwards it to the response (needed for `WWW-Authenticate`). Still one handler.
- **Structural decision for `routers/books.py`:** the router is now mixed — reads public, writes admin. Router-level `dependencies=[...]` (what you did on Day 11) no longer fits the whole router. Pick a structure (two routers on one prefix, per-route `Depends`, or `include_router(dependencies=)` on a split) and be ready to justify it in review.
- Reuse `get_existing_book` from Day 11. Add `get_existing_member` / `get_existing_loan` only if it makes your object-level checks cleaner.
- `/docs` must show the lock icon on protected routes, and **Authorize** → log in → call a protected endpoint must work from the Swagger UI.

---

## Config and secrets (Day 21)

`config.py`:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", ...)
    ...

@lru_cache
def get_settings() -> Settings: ...
```

Required fields (names are yours, but all of these must exist):

- `app_env` (`dev` / `test` / `prod`)
- `database_url`
- `jwt_secret_key: SecretStr` — **no default**. Delete `.env` and the app must fail at startup with a `ValidationError` naming the missing field, not run with a fallback secret. Add a validator rejecting secrets shorter than 32 characters (short HMAC keys are weak, and PyJWT warns on them). Generate yours with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- `jwt_algorithm`, `access_token_expire_minutes`
- `cors_allowed_origins: list[str]`
- `login_rate_limit` (e.g. `"5/minute"`)
- `first_admin_email`, `first_admin_password: SecretStr`

Rules:

- `.env` is in `.gitignore`; `.env.example` is committed with placeholders only. Prove it: `git check-ignore -v .env`.
- `SecretStr` values are unwrapped (`.get_secret_value()`) in exactly one place each — inside the call that needs them. Printing `settings` must not reveal them.
- `alembic/env.py` takes the DB URL from `get_settings()`, not from the hardcoded `sqlalchemy.url` in `alembic.ini`. Leave nothing connection-related in `alembic.ini`.
- `CORSMiddleware` origins come from settings. `allow_headers` must include `Authorization`. No `"*"` origin together with credentials.
- The settings object is injected via `Depends(get_settings)` wherever a route/dependency needs it, so tests can use `dependency_overrides`. Tests run with `app_env=test` and a **separate** SQLite file (or in-memory with `StaticPool`), never `library.db`.
- grep your project for `"admin-secret-123"`, `"sqlite:///"`, and your JWT secret. Each should appear only in `.env` / `.env.example` / `config.py` defaults for non-secret fields — nowhere in code.

---

## Alembic (Day 15)

Third migration, generated with autogenerate, **reviewed by you before applying**:

- Creates `users` (unique `email`), adds `members.user_id` (nullable, unique, FK).
- **SQLite gotcha you will hit:** SQLite can't `ALTER TABLE ... ADD CONSTRAINT`, so a plain autogenerated `op.create_foreign_key` fails. Alembic's fix is batch mode — `render_as_batch=True` in `env.py`'s `context.configure(...)`, so the migration uses `op.batch_alter_table` (which recreates the table under the hood). Read what the batch migration actually does to `members` before applying, since it's a copy-and-swap on a table that has data.
- Apply it with your Day 16 data present. Confirm in the `.db` file that existing members survived with `user_id = NULL`.
- `alembic downgrade -1` then `alembic upgrade head` once, confirming the same.
- Still no `Base.metadata.create_all()` anywhere.

---

## Suggested order

1. `config.py` + `.env` + `.gitignore`; point `database.py` and `alembic/env.py` at it. Everything should still run before any auth exists.
2. `core/security.py` (hash/verify, encode/decode) — verify by hand in a REPL.
3. `User` model, `Member.user_id`, migration (with batch mode).
4. Auth errors in `core/exceptions.py`; `headers` on `LibraryError`; handler update.
5. `/auth/register`, `/auth/login`, `/auth/me`, `create_admin.py`.
6. `get_current_user`, `require_role`, `core/permissions.py`.
7. Apply the permission matrix router by router; services get the owner-filter changes.
8. Rate limit + CORS from settings. Carry your Day 20 security-headers middleware over too.

---

## What "done" looks like

I'll run these against your code with `TestClient`. Run them yourself first.

**Config**

- App refuses to start with `.env` removed, and the error names `jwt_secret_key`.
- `print(get_settings())` shows no secret values.
- `git check-ignore -v .env` matches; `.env.example` is tracked.

**Registration / login**

- Register → 201; response has no `password`, `hashed_password`, or hash-looking string; `/openapi.json` response schemas don't contain those fields either.
- Register with `{"role": "admin"}` in the body does not produce an admin.
- Register `A@x.com`, then `a@x.com` → `DuplicateEmailError` 409. No orphan `users` row remains after the failed second attempt.
- Register with a 73-byte password (including one that's under 73 *characters* but over 72 bytes) → 422, not 500.
- Login wrong password and login unknown email → identical status, body, and `WWW-Authenticate` header.
- Login timing: unknown email isn't dramatically faster than wrong password (measure both; same order of magnitude).
- Sixth login attempt in a minute (with a `5/minute` limit) → 429 in your error shape.

**Token handling**

- No header, `Bearer garbage`, expired token, token signed with a different secret, token with a flipped payload byte → all identical 401 with your error shape (not `{"detail": ...}`).
- Valid token, user then set `is_active=False` in the DB → next request 401 with the same token.
- Valid token, user then promoted/demoted in the DB → next request reflects the new role with the same token.

**Authorization**

- Every row of the permission matrix: anonymous, `member`, `admin`. Status codes exactly as listed.
- Member A requests member B's `/members/{id}` and `/loans/{id}`: response body identical to requesting a nonexistent id.
- Member A `POST /loans` with B's `member_id` → 403.
- Member A `PATCH /members/{own_id}` with `membership_type` → 403; with `name` only → 200.
- Member with 5 loans in a DB of 15 total: `GET /loans?skip=0&limit=3` returns exactly 3 of their own, `limit=10` returns exactly 5. Not short pages.
- `GET /loans` as admin with 20 loans: query count still fixed (your Day 16 hook), regardless of auth added.

**Existing behavior**

- Day 16 data intact after the third migration; legacy members visible to admin, unable to log in.
- Full borrow → limit-hit 409 → return → `copies_available` restored flow works end to end using real tokens.
- `uvicorn main:app --reload` starts clean; `/docs` Authorize flow works.

Bring me the code when it runs. Same review process as Day 5, 11, and 16.

*Look ahead:* `hash_password` / `verify_password` are CPU-bound and blocking. Inside a `def` route FastAPI runs them in a threadpool, which is why this works fine today. Put the same call inside an `async def` route and it stalls the event loop for every request. That's the Day 23 blocking-call trap, with a real example you'll already have written.
