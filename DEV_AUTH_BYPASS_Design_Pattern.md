# Development Authentication Bypass Pattern

## Overview

The **Development Authentication Bypass Pattern** is a design pattern that enables developers to bypass full authentication workflows during local development. Instead of requiring login credentials to test protected endpoints, developers can use a special HTTP header to automatically authenticate requests against a local user.

This pattern dramatically speeds up development by eliminating repetitive login flows while maintaining strict security boundaries—the bypass is **only** active when explicitly enabled via an environment variable and when requests include a specific opt-in header.

---

## Key Principles

1. **Defense in Depth**: The bypass requires BOTH a server-side flag (`DEV_AUTH_BYPASS=true`) AND a client-side header (`X-DEV-AUTH: 1`) to activate. Neither alone is sufficient.
2. **Explicit Opt-In**: The pattern is disabled by default. It must be explicitly enabled through environment configuration.
3. **No Production Code Paths**: Production builds should have an empty/falsy bypass header configuration, ensuring the bypass logic is never triggered in production.
4. **Warning on Activation**: When the bypass is enabled, the server logs a warning message at startup to remind developers this mode is active.
5. **Configurable**: The header name and target user are configurable through environment variables.

---

## Architecture

### Components

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **Backend** | Settings/Configuration | Define bypass flags: enable toggle, header name, optional target user email |
| **Backend** | Authentication Dependency/Middleware | Check for bypass conditions before normal auth flow |
| **Frontend** | Environment Configuration | Define bypass header name (empty in production) |
| **Frontend** | HTTP Interceptor | Automatically attach bypass header to all outgoing requests in dev mode |
| **Frontend** | Auth Guard | Handle auth bypass for route protection |
| **Frontend** | Auth Service | Initialize session via bypass probe on startup |

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPMENT MODE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Frontend                                                                   │
│  ┌─────────────┐    ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ HTTP Request├───►│ Auth Interceptor ├───►│ Request + X-DEV-AUTH: 1 │   │
│  └─────────────┘    │ (adds header)    │    └───────────┬──────────────┘   │
│                     └──────────────────┘                │                  │
│                                                         ▼                  │
│  Backend                                                                   │
│  ┌────────────────────┐    ┌──────────────────────────────────────────┐   │
│  │ Auth Dependency    │    │ 1. Check DEV_AUTH_BYPASS setting         │   │
│  │ (middleware)       ├───►│ 2. Check for DEV_BYPASS_HEADER in req    │   │
│  │                    │    │ 3. If both true → return dev user        │   │
│  │                    │    │ 4. Otherwise → normal JWT validation     │   │
│  └────────────────────┘    └──────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION MODE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Frontend: devBypassHeader = '' (empty/falsy)                               │
│  → Interceptor never adds header                                            │
│                                                                             │
│  Backend: DEV_AUTH_BYPASS = false (default)                                 │
│  → Auth dependency skips bypass check entirely                              │
│  → Normal JWT authentication always required                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend Configuration

**1.1 Add bypass settings to your configuration module**

Add the following settings to your application configuration (e.g., `settings.py`, `.env` file, or config class):

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `DEV_AUTH_BYPASS` | `bool` | `false` | Master toggle for dev bypass feature |
| `DEV_BYPASS_HEADER` | `string` | `"X-DEV-AUTH"` | Name of the HTTP header to check |
| `DEV_BYPASS_USER_EMAIL` | `string \| null` | `null` | (Optional) Email of specific user to return; if null, returns first user in database |

**1.2 Add startup warning**

When the application starts and `DEV_AUTH_BYPASS` is `true`, print/log a warning:
```
WARNING: DEV_AUTH_BYPASS is ENABLED. This should only be used in local development environments.
```

### Phase 2: Backend Authentication Logic

**2.1 Modify authentication dependency/middleware**

At the **beginning** of your authentication check (before JWT validation), add bypass logic:

```
IF DEV_AUTH_BYPASS is enabled:
    IF request contains DEV_BYPASS_HEADER with value "1":
        IF DEV_BYPASS_USER_EMAIL is set:
            → Find user by that email and return it
        ELSE:
            → Return first user from database
        IF no user exists:
            → Create a dummy "dev bypass" user and return it
        
# Continue with normal authentication (JWT validation, etc.)
```

**Key implementation notes:**
- The bypass check must happen BEFORE any token extraction/validation
- If bypass conditions are not met, fall through to normal auth
- The value "1" is a simple truthy signal; any non-"1" value should not trigger bypass

### Phase 3: Frontend Environment Configuration

**3.1 Add bypass header to environment files**

Development environment (`environment.ts` / `environment.development.ts`):
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api',
  devBypassHeader: 'X-DEV-AUTH'  // Must match backend's DEV_BYPASS_HEADER
};
```

Production environment (`environment.prod.ts`):
```typescript
export const environment = {
  production: true,
  apiUrl: '/api',
  devBypassHeader: ''  // Empty string - bypass NEVER added in production
};
```

### Phase 4: Frontend HTTP Interceptor

**4.1 Create or modify HTTP interceptor to add bypass header**

In your HTTP interceptor (runs on every outgoing request):

```
IF NOT production mode AND devBypassHeader is truthy:
    Add header: { [devBypassHeader]: '1' } to request
    (Optional) Log debug message about header being added

Continue with existing interceptor logic (adding auth token if present, etc.)
```

**Key implementation notes:**
- The bypass header should be added alongside (not instead of) any existing auth token
- This allows the backend to have both mechanisms available
- Debug logging helps during development troubleshooting

### Phase 5: Frontend Auth Service

**5.1 Probe current user on startup in dev mode**

In your auth service initialization:

```
IF NOT production mode AND devBypassHeader is truthy:
    Call GET /api/auth/me (or equivalent "current user" endpoint)
    → This request will have the bypass header attached by interceptor
    → Backend returns dev user without requiring login
    → Store user in app state (e.g., BehaviorSubject, store, etc.)
```

This automatically "logs in" the dev user when the app starts.

### Phase 6: Frontend Auth Guard (Optional)

**6.1 Modify route guards for dev mode**

For routes protected by an auth guard:

```
IF user is authenticated (has valid token):
    → Allow access

IF NOT production mode AND devBypassHeader is truthy:
    → Probe /api/auth/me endpoint
    → Allow navigation regardless of result (bypass active)

ELSE:
    → Redirect to login page
```

This prevents login redirects during development.

---

## Configuration Reference

### Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEV_AUTH_BYPASS` | No | `false` | Set to `true` to enable the bypass |
| `DEV_BYPASS_HEADER` | No | `X-DEV-AUTH` | HTTP header name to check |
| `DEV_BYPASS_USER_EMAIL` | No | `null` | Specific user email to authenticate as |

### Frontend Environment Properties

| Property | Development | Production | Description |
|----------|-------------|------------|-------------|
| `devBypassHeader` | `'X-DEV-AUTH'` | `''` (empty) | Header name; empty disables bypass |

---

## Security Considerations

1. **Never commit enabled bypass to version control**
   - Add `DEV_AUTH_BYPASS=true` to your `.env` file, NOT to checked-in config
   - Add `.env` to `.gitignore`

2. **Production builds are inherently safe**
   - Frontend: `devBypassHeader` is empty in production environment file
   - Backend: `DEV_AUTH_BYPASS` defaults to `false`
   - Both conditions must be true for bypass to work

3. **Header alone is not sufficient**
   - Even if someone sends `X-DEV-AUTH: 1` to a production server, the bypass check is skipped because `DEV_AUTH_BYPASS` is false

4. **Audit trail**
   - Consider logging when bypass is used (at debug level)
   - The startup warning ensures operators know bypass is active

---

## Testing

Create tests that verify:

1. **Bypass works when enabled**
   - Enable `DEV_AUTH_BYPASS` in test
   - Create a test user
   - Send request with bypass header
   - Assert: protected endpoint returns 200 and user data

2. **Bypass requires header**
   - Enable `DEV_AUTH_BYPASS` in test
   - Send request WITHOUT bypass header
   - Assert: request is rejected (401)

3. **Bypass is disabled by default**
   - Do NOT enable `DEV_AUTH_BYPASS`
   - Send request with bypass header
   - Assert: request is rejected (401) - header alone is not enough

4. **All protected endpoints work with bypass**
   - Enable bypass, iterate through protected endpoints
   - Assert: all return successful responses

---

## Example Usage

### Enabling for Local Development

1. Create/edit `backend/.env`:
   ```env
   DEV_AUTH_BYPASS=true
   # Optional: target a specific dev user by email (fallback is the first user in the DB)
   DEV_BYPASS_USER_EMAIL=dev@local
   ```

2. Restart backend server

3. Start frontend in development mode

4. Navigate to protected routes—you're automatically authenticated!

### Manual API Testing (curl/Postman)

```bash
# PowerShell
Invoke-RestMethod -Uri http://localhost:8000/api/protected-endpoint -Headers @{ 'X-DEV-AUTH' = '1' }

# Bash
curl -H "X-DEV-AUTH: 1" http://localhost:8000/api/protected-endpoint
```

---

## Checklist for Implementation

- [ ] Backend: Add `DEV_AUTH_BYPASS`, `DEV_BYPASS_HEADER`, `DEV_BYPASS_USER_EMAIL` to settings
- [ ] Backend: Add startup warning when bypass is enabled
- [ ] Backend: Modify auth dependency to check bypass before JWT validation
- [ ] Backend: Implement user lookup (by email or first user) in bypass path
- [ ] Backend: Optionally create dummy user if none exists
- [ ] Frontend: Add `devBypassHeader` to development environment config
- [ ] Frontend: Set `devBypassHeader` to empty string in production config
- [ ] Frontend: Modify HTTP interceptor to add header in dev mode
- [ ] Frontend: Modify auth service to probe `/me` on startup in dev mode
- [ ] Frontend: (Optional) Modify auth guard for dev mode navigation
- [ ] Tests: Add test cases for bypass behavior
- [ ] Documentation: Document the feature and its security implications
