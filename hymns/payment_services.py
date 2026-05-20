"""
Flutterwave verification and premium plan pricing (server-side source of truth).
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from decouple import config
from django.utils import timezone

logger = logging.getLogger(__name__)

FLUTTERWAVE_SECRET_KEY = config("FLUTTERWAVE_SECRET_KEY", default="")
PAYSTACK_SECRET_KEY = config("PAYSTACK_SECRET_KEY", default="")
PREMIUM_CURRENCY = config("PREMIUM_CURRENCY", default="GHS").upper()
PREMIUM_MONTHLY_AMOUNT = Decimal(str(config("PREMIUM_MONTHLY_AMOUNT", default="50")))
PREMIUM_YEARLY_AMOUNT = Decimal(str(config("PREMIUM_YEARLY_AMOUNT", default="500")))


@dataclass(frozen=True)
class PlanConfig:
    plan_id: str
    amount: Decimal
    currency: str
    product_id: str
    subscription_type: str
    duration: timedelta | None


PLANS: dict[str, PlanConfig] = {
    "monthly": PlanConfig(
        plan_id="monthly",
        amount=PREMIUM_MONTHLY_AMOUNT,
        currency=PREMIUM_CURRENCY,
        product_id="nova_hymnal_premium_web_monthly",
        subscription_type="monthly",
        duration=timedelta(days=30),
    ),
    "yearly": PlanConfig(
        plan_id="yearly",
        amount=PREMIUM_YEARLY_AMOUNT,
        currency=PREMIUM_CURRENCY,
        product_id="nova_hymnal_premium_web_yearly",
        subscription_type="yearly",
        duration=timedelta(days=365),
    ),
}


def get_plan(plan_id: str) -> PlanConfig | None:
    return PLANS.get(plan_id)


@dataclass
class FlutterwaveTransaction:
    transaction_id: str
    tx_ref: str
    amount: Decimal
    currency: str
    status: str


class FlutterwaveError(Exception):
    pass


class PaystackError(Exception):
    pass


@dataclass
class PaystackTransaction:
    reference: str
    amount: Decimal
    currency: str
    status: str


def verify_flutterwave_transaction(transaction_id: str) -> FlutterwaveTransaction:
    if not FLUTTERWAVE_SECRET_KEY:
        raise FlutterwaveError("Flutterwave is not configured on the server")

    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        logger.warning("Flutterwave HTTP error %s for tx %s", e.code, transaction_id)
        raise FlutterwaveError("Could not verify payment with Flutterwave") from e
    except urllib.error.URLError as e:
        logger.warning("Flutterwave network error for tx %s: %s", transaction_id, e)
        raise FlutterwaveError("Payment verification unavailable") from e

    if payload.get("status") != "success":
        raise FlutterwaveError("Invalid verification response")

    data = payload.get("data") or {}
    if data.get("status") != "successful":
        raise FlutterwaveError("Transaction was not successful")

    return FlutterwaveTransaction(
        transaction_id=str(data.get("id", transaction_id)),
        tx_ref=str(data.get("tx_ref", "")),
        amount=Decimal(str(data.get("amount", 0))),
        currency=str(data.get("currency", "")).upper(),
        status=str(data.get("status", "")),
    )


def verify_paystack_transaction(reference: str) -> PaystackTransaction:
    if not PAYSTACK_SECRET_KEY:
        raise PaystackError("Paystack is not configured on the server")

    encoded_reference = urllib.parse.quote(reference, safe="")
    url = f"https://api.paystack.co/transaction/verify/{encoded_reference}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "NovaHymnal/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = "Could not verify payment with Paystack"
        try:
            error_payload = json.loads(e.read().decode())
            detail = str(error_payload.get("message") or detail)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        logger.warning(
            "Paystack HTTP error %s for reference %s: %s",
            e.code,
            reference,
            detail,
        )
        raise PaystackError(detail) from e
    except urllib.error.URLError as e:
        logger.warning("Paystack network error for reference %s: %s", reference, e)
        raise PaystackError("Payment verification unavailable") from e

    if payload.get("status") is not True:
        raise PaystackError("Invalid verification response")

    data = payload.get("data") or {}
    if data.get("status") != "success":
        raise PaystackError("Transaction was not successful")

    # Paystack returns amount in the smallest currency unit (e.g. pesewas/kobo).
    amount = Decimal(str(data.get("amount", 0))) / Decimal("100")

    return PaystackTransaction(
        reference=str(data.get("reference", reference)),
        amount=amount,
        currency=str(data.get("currency", "")).upper(),
        status=str(data.get("status", "")),
    )


def amounts_match(expected: Decimal, paid: Decimal, tolerance: Decimal = Decimal("0.01")) -> bool:
    return abs(expected - paid) <= tolerance
