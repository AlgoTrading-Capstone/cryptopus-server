# Cryptopus Server — Auth Integration Guide

> For the Java desktop client developer.
> Base URL (local): `http://127.0.0.1:8000`
> Base URL (production): `https://api.cryptopus.com`

---

## Overview

The auth flow has two phases:

**Phase 1 — Registration (one time)**
```
Register → Verify Email → Setup OTP → Verify OTP Setup
```

**Phase 2 — Login (every session)**
```
Login → Verify OTP → Get JWT Tokens
```

---

## Running the server locally

Make sure you have Docker installed, then run:

```bash
docker-compose up
```

Server will be available at `http://127.0.0.1:8000`.

---

## Phase 1 — Registration Flow

### Step 1 — Register

**POST** `/api/auth/register`

Request:
```json
{
    "email": "user@cryptopus.com",
    "password": "StrongPassword123!",
    "first_name": "Moshe",
    "last_name": "Avi"
}
```

Response `201`:
```json
{
    "status": "success",
    "data": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@cryptopus.com",
        "created_at": "2026-03-30T10:00:00Z"
    }
}
```

---

### Step 2 — Verify Email

A 6-character verification code is sent to the user's email.
> In development: the code is printed to the server console.

**POST** `/api/auth/verify-email`

Request:
```json
{
    "email": "user@cryptopus.com",
    "verification_code": "ABC123"
}
```

Response `200`:
```json
{
    "status": "success",
    "data": {
        "email_verified": true,
        "otp_setup_required": true,
        "message": "Email verified successfully."
    }
}
```

---

### Step 2.5 — Resend Verification Email (optional)

If the verification code was never received or has expired, the client may request a new one. Any previously issued code for this email is invalidated server-side. The endpoint is rate-limited — clients must wait `cooldown_seconds` before the next request.

**POST** `/api/auth/resend-verification-email`

Request:
```json
{
    "email": "user@cryptopus.com"
}
```

Response `200`:
```json
{
    "status": "success",
    "data": {
        "message": "Verification code resent.",
        "expires_in_seconds": 600,
        "cooldown_seconds": 30
    }
}
```

Errors:
- `400` — invalid email format
- `404` — no such pending registration
- `409` — email already verified
- `429` — cooldown active, wait before retrying

---

### Step 3 — Setup OTP

**POST** `/api/auth/setup-otp`

Request:
```json
{
    "email": "user@cryptopus.com"
}
```

Response `200`:
```json
{
    "status": "success",
    "data": {
        "otp_secret": "JBSWY3DPEHPK3PXP",
        "qr_code_url": "otpauth://totp/Cryptopus:user%40cryptopus.com?secret=JBSWY3DPEHPK3PXP&issuer=Cryptopus",
        "message": "OTP setup initialized successfully."
    }
}
```

**Action required:** Display `qr_code_url` as a QR code in the UI.
The user scans it with Google Authenticator or Authy.

> Java library for QR code generation: `com.google.zxing`

---

### Step 4 — Verify OTP Setup

After the user scans the QR code, ask them to enter the 6-digit code from their authenticator app.

**POST** `/api/auth/verify-otp-setup`

Request:
```json
{
    "email": "user@cryptopus.com",
    "otp_code": "123456"
}
```

Response `200`:
```json
{
    "status": "success",
    "data": {
        "otp_enabled": true,
        "message": "OTP enabled successfully. You can now log in."
    }
}
```

Registration is complete. Redirect user to login screen.

---

## Phase 2 — Login Flow

### Step 1 — Login

**POST** `/api/auth/login`

Request:
```json
{
    "email": "user@cryptopus.com",
    "password": "StrongPassword123!"
}
```

Response `200` — the shape depends on registration state:

**Fully registered (email verified + OTP set up):**
```json
{
    "status": "success",
    "data": {
        "email_verified": true,
        "otp_verified": true,
        "temporary_session_id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Password verified. OTP verification required."
    }
}
```
Proceed to Step 2 (Verify OTP) using `temporary_session_id`.

**Email not verified (abandoned after register):**
```json
{
    "status": "success",
    "data": {
        "email_verified": false,
        "otp_verified": false,
        "temporary_session_id": null,
        "message": "Email not verified. Please complete registration."
    }
}
```
Redirect the user to the Verify Email screen. If the original code has expired, call `/api/auth/resend-verification-email` first.

**Email verified but OTP not set up (abandoned after email verification):**
```json
{
    "status": "success",
    "data": {
        "email_verified": true,
        "otp_verified": false,
        "temporary_session_id": null,
        "message": "OTP setup not completed. Please finish registration."
    }
}
```
Redirect the user to the Setup OTP screen (Phase 1 Step 3).

**Client routing rules:**

| `email_verified` | `otp_verified` | Next screen |
|---|---|---|
| `false` | `false` | Verify Email |
| `true` | `false` | Setup OTP |
| `true` | `true` | Verify OTP (use `temporary_session_id`) |

**Store** `temporary_session_id` in memory when present — needed for the next step.

---

### Step 2 — Verify OTP

Ask the user for the 6-digit code from their authenticator app.

**POST** `/api/auth/verify-otp`

Request:
```json
{
    "temporary_session_id": "550e8400-e29b-41d4-a716-446655440000",
    "otp_code": "123456"
}
```

Response `200`:
```json
{
    "status": "success",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "expires_in": 3600,
        "user_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

**Store both tokens securely.** The user is now authenticated.

---

## Using the Access Token

Every authenticated request must include the access token in the header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Java example:
```java
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://api.cryptopus.com/api/portfolio/summary"))
    .header("Authorization", "Bearer " + accessToken)
    .header("Content-Type", "application/json")
    .GET()
    .build();
```

---

## Token Refresh

The access token expires after **1 hour**. When you get a `401` response, refresh it:

**POST** `/api/auth/refresh`

Request:
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response `200`:
```json
{
    "status": "success",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "expires_in": 3600
    }
}
```

Replace the stored access token with the new one.

---

## Logout

**POST** `/api/auth/logout`

Request:
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response `200`:
```json
{
    "status": "success",
    "data": {
        "message": "Logged out successfully."
    }
}
```

After logout, clear both tokens from memory. The refresh token is permanently invalidated.

---

## Error Handling

All errors follow this format:
```json
{
    "error": "Error message here"
}
```

| Status Code | Meaning |
|---|---|
| `400` | Bad request — invalid input or business logic error |
| `401` | Unauthorized — missing or expired access token |
| `404` | Not found |
| `409` | Conflict — e.g. email already registered |
| `429` | Too many requests — rate-limit cooldown active |

---

## Token Storage Recommendation

Store tokens **in memory only** (not in files or persistent storage) for security.
Clear them on app exit or logout.

---

## Summary

| Endpoint | Method | Auth Required |
|---|---|---|
| `/api/auth/register` | POST | No |
| `/api/auth/verify-email` | POST | No |
| `/api/auth/resend-verification-email` | POST | No |
| `/api/auth/setup-otp` | POST | No |
| `/api/auth/verify-otp-setup` | POST | No |
| `/api/auth/login` | POST | No |
| `/api/auth/verify-otp` | POST | No |
| `/api/auth/refresh` | POST | No |
| `/api/auth/logout` | POST | No |
