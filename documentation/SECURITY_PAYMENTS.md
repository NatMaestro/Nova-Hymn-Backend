# Payment & premium security

This document describes threats, mitigations, and remaining risks for **Nova Hymnal Web** checkout (Paystack primary, Flutterwave fallback) and **Nova Hymnal Backend** premium access.

## Payment flow (intended)

1. User selects **monthly** or **yearly** on the web app (display prices are cosmetic; server enforces amounts).
2. Paystack checkout runs in the browser (public key only). Flutterwave remains available in code as a temporary fallback.
3. On Paystack success, the client calls `POST /api/payments/paystack/verify` (Next.js), which proxies to Django `POST /api/v1/payments/paystack/confirm/`.
4. Django verifies the transaction with **Paystack’s API** using `PAYSTACK_SECRET_KEY`, checks amount/currency against `PREMIUM_*` env vars, and writes **`PaymentLedger`** (`transaction_id` unique).
5. The client stores `expires_at` and `premium_verified_transaction_id` in localStorage; logged-in users also sync via `subscriptions/verify/` (web platform requires a ledger row).

## Threats mitigated

| Threat | Mitigation |
|--------|------------|
| **Replay** (reuse same `transaction_id`) | `PaymentLedger.transaction_id` unique; confirm endpoint is idempotent; duplicate inserts hit `IntegrityError` + safe read |
| **Race** (double callback / double-click) | DB `select_for_update()` on ledger row; client `sessionStorage` in-flight lock; `claimTransactionLocally()` |
| **Amount tampering** (pay less, claim yearly) | Server compares verified gateway amount to `PREMIUM_MONTHLY_AMOUNT` / `PREMIUM_YEARLY_AMOUNT` (not client `amount`) |
| **Plan mismatch on replay** | Idempotent path rejects `plan_id` ≠ ledger `plan_id` |
| **Secret key exposure** | Gateway secrets only on Django; Next stores public keys only |
| **Brute-force confirm** | `django-ratelimit` 20 POST/min per IP on gateway confirm endpoints |
| **Subscription theft (web)** | `subscriptions/verify` with `platform=web` requires existing `PaymentLedger`; `product_id` must match server plan |
| **Cross-account ledger hijack** | Ledger `user` set on first authenticated link; conflicts return 409 |
| **Premium API content leak** | Hymn detail / sheet / audio viewsets strip URLs unless `user.has_active_premium` |

## Client-side premium (limitations)

- **localStorage** (`premium_status`, `premium_expires_at`, `premium_verified_transaction_id`) can be forged in DevTools.
- UI gates (ads, tabs, playlists) trust this for UX only.
- **Authoritative access** to sheet music and audio URLs requires a valid backend session with `has_active_premium` (or anonymous users only see non-premium assets).

**Recommendation:** Sign in after purchase so entitlement is tied to the account and syncs across devices.

## Remaining risks & follow-ups

1. **iOS / Android `subscriptions/verify`** still trusts client-supplied `receipt_data` without store receipt validation in this codebase. Harden before treating mobile IAP as production-ready.
2. **Guest checkout:** Anyone who obtains a valid gateway transaction reference can call confirm and activate premium locally until expiry. IDs are hard to guess but not secret; prefer login-before-pay for stricter binding.
3. **Rate limiting** uses in-process `LocMemCache` by default. On Render with multiple Gunicorn workers, use **Redis** for `CACHES` so limits apply globally.
4. **Manual renewals:** One-time web payments do not auto-renew; expiry is time-based only.
5. **Render cold start:** Slow confirm may cause client retries; idempotent server responses are safe; ensure UX shows “processing” state.

## Required environment variables

### Django (Render / `.env`)

```env
FLUTTERWAVE_SECRET_KEY=...
PAYSTACK_SECRET_KEY=...
PREMIUM_MONTHLY_AMOUNT=50
PREMIUM_YEARLY_AMOUNT=500
PREMIUM_CURRENCY=GHS
```

### Next.js (`.env.local`)

```env
NEXT_PUBLIC_FLUTTERWAVE_PUBLIC_KEY=...
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=...
NEXT_PUBLIC_PREMIUM_MONTHLY_PRICE=50
NEXT_PUBLIC_PREMIUM_YEARLY_PRICE=500
NEXT_PUBLIC_PREMIUM_CURRENCY=GHS
```

Keep **monthly/yearly amounts in sync** between web display env and Django server env.

## Deployment checklist

- [ ] Run migration `0004_paymentledger`
- [ ] Set Paystack, Flutterwave fallback, and premium env vars on Render
- [ ] Rotate Flutterwave keys if secret was ever committed to the web repo
- [ ] `DEBUG=False`, `ALLOWED_HOSTS`, CORS for production web origin
- [ ] Smoke-test: pay → confirm → hymn premium URLs with logged-in user
