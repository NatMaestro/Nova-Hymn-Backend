"""
Secure payment confirmation (server-side verification + idempotency).
"""
import json
import logging

from django.db import IntegrityError, transaction
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import PaymentLedger, Subscription
from .payment_services import (
    FlutterwaveError,
    PaystackError,
    amounts_match,
    get_plan,
    verify_flutterwave_transaction,
    verify_paystack_transaction,
)

logger = logging.getLogger(__name__)


def _ledger_success_payload(ledger, plan):
    return {
        "verified": True,
        "plan_id": ledger.plan_id,
        "expires_at": ledger.expires_at.isoformat(),
        "transaction_id": ledger.transaction_id,
        "product_id": plan.product_id,
    }


def _link_ledger_to_user(ledger, user, plan, receipt_data):
    """Attach a guest payment to the first authenticated account that claims it."""
    if ledger.user_id:
        if ledger.user_id != user.id:
            raise PermissionError("payment_linked_to_other_user")
        return
    ledger.user = user
    ledger.save(update_fields=["user"])
    _subscription_for_user(
        user,
        plan,
        ledger.transaction_id,
        receipt_data,
        ledger.expires_at,
    )


def _subscription_for_user(user, plan, transaction_id, receipt_data, expires_at):
    """Create or extend subscription for authenticated user."""
    duration = plan.duration
    now = timezone.now()
    sub, created = Subscription.objects.get_or_create(
        transaction_id=transaction_id,
        defaults={
            "user": user,
            "product_id": plan.product_id,
            "receipt_data": receipt_data,
            "platform": "web",
            "status": "active",
            "subscription_type": plan.subscription_type,
            "expires_at": expires_at,
        },
    )
    if not created:
        sub.status = "active"
        sub.subscription_type = plan.subscription_type
        sub.platform = "web"
        if duration and expires_at:
            base = (
                sub.expires_at
                if sub.expires_at and sub.expires_at > now
                else now
            )
            sub.expires_at = base + duration
        sub.save()
    return sub


def _confirm_verified_payment(
    *,
    request,
    provider,
    ledger_transaction_id,
    tx_ref,
    plan_id,
    plan,
    paid_amount,
    paid_currency,
):
    if not amounts_match(plan.amount, paid_amount):
        logger.warning(
            "%s amount mismatch tx=%s paid=%s expected=%s",
            provider,
            ledger_transaction_id,
            paid_amount,
            plan.amount,
        )
        return Response(
            {"verified": False, "detail": "Payment amount does not match plan"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if paid_currency != plan.currency:
        return Response(
            {"verified": False, "detail": "Payment currency does not match plan"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    expires_at = now + plan.duration if plan.duration else None
    receipt_data = json.dumps(
        {"source": provider, "plan_id": plan_id, "tx_ref": tx_ref}
    )

    try:
        with transaction.atomic():
            existing = (
                PaymentLedger.objects.select_for_update()
                .filter(transaction_id=ledger_transaction_id)
                .first()
            )
            if existing:
                if existing.plan_id != plan_id:
                    return Response(
                        {
                            "verified": False,
                            "detail": "plan_id does not match this transaction",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if existing.expires_at <= now:
                    return Response(
                        {"verified": False, "detail": "Payment entitlement has expired"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if request.user.is_authenticated:
                    try:
                        _link_ledger_to_user(
                            existing,
                            request.user,
                            get_plan(existing.plan_id) or plan,
                            receipt_data,
                        )
                    except PermissionError:
                        return Response(
                            {
                                "verified": False,
                                "detail": "This payment is already linked to another account",
                            },
                            status=status.HTTP_409_CONFLICT,
                        )
                payload = _ledger_success_payload(existing, plan)
                payload["idempotent"] = True
                return Response(payload)

            PaymentLedger.objects.create(
                transaction_id=ledger_transaction_id,
                tx_ref=tx_ref,
                plan_id=plan_id,
                amount=paid_amount,
                currency=paid_currency,
                expires_at=expires_at,
                user=request.user if request.user.is_authenticated else None,
            )

            if request.user.is_authenticated:
                _subscription_for_user(
                    request.user,
                    plan,
                    ledger_transaction_id,
                    receipt_data,
                    expires_at,
                )

    except IntegrityError:
        ledger = PaymentLedger.objects.filter(
            transaction_id=ledger_transaction_id
        ).first()
        if ledger:
            if request.user.is_authenticated and not ledger.user_id:
                try:
                    _link_ledger_to_user(
                        ledger,
                        request.user,
                        get_plan(ledger.plan_id) or plan,
                        receipt_data,
                    )
                except PermissionError:
                    return Response(
                        {
                            "verified": False,
                            "detail": "This payment is already linked to another account",
                        },
                        status=status.HTTP_409_CONFLICT,
                    )
            payload = _ledger_success_payload(ledger, plan)
            payload["idempotent"] = True
            return Response(payload)
        return Response(
            {"verified": False, "detail": "Could not process payment"},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(
        {
            "verified": True,
            "idempotent": False,
            "plan_id": plan_id,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "transaction_id": ledger_transaction_id,
            "product_id": plan.product_id,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="20/m", method="POST", block=True)
def flutterwave_confirm(request):
    """
    Verify a Flutterwave transaction and grant premium (idempotent).

    - Amount/currency come from server plan config (never trust client amounts).
    - transaction_id is stored in PaymentLedger to block replay attacks.
    - Optional: links to authenticated user subscription.
    """
    if getattr(request, "limited", False):
        return Response(
            {"verified": False, "detail": "Too many requests. Try again shortly."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    transaction_id = str(request.data.get("transaction_id", "")).strip()
    plan_id = str(request.data.get("plan_id", "")).strip().lower()

    if not transaction_id or len(transaction_id) > 128:
        return Response(
            {"verified": False, "detail": "Invalid transaction_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    plan = get_plan(plan_id)
    if not plan:
        return Response(
            {"verified": False, "detail": "plan_id must be monthly or yearly"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        fw = verify_flutterwave_transaction(transaction_id)
    except FlutterwaveError as e:
        return Response(
            {"verified": False, "detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not amounts_match(plan.amount, fw.amount):
        logger.warning(
            "Payment amount mismatch tx=%s paid=%s expected=%s",
            transaction_id,
            fw.amount,
            plan.amount,
        )
        return Response(
            {"verified": False, "detail": "Payment amount does not match plan"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if fw.currency != plan.currency:
        return Response(
            {"verified": False, "detail": "Payment currency does not match plan"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    expires_at = now + plan.duration if plan.duration else None
    receipt_data = f'{{"source":"flutterwave","plan_id":"{plan_id}","tx_ref":"{fw.tx_ref}"}}'

    try:
        with transaction.atomic():
            existing = (
                PaymentLedger.objects.select_for_update()
                .filter(transaction_id=transaction_id)
                .first()
            )
            if existing:
                if existing.plan_id != plan_id:
                    return Response(
                        {
                            "verified": False,
                            "detail": "plan_id does not match this transaction",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if existing.expires_at <= now:
                    return Response(
                        {"verified": False, "detail": "Payment entitlement has expired"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if request.user.is_authenticated:
                    try:
                        _link_ledger_to_user(
                            existing,
                            request.user,
                            get_plan(existing.plan_id) or plan,
                            receipt_data,
                        )
                    except PermissionError:
                        return Response(
                            {
                                "verified": False,
                                "detail": "This payment is already linked to another account",
                            },
                            status=status.HTTP_409_CONFLICT,
                        )
                payload = _ledger_success_payload(existing, plan)
                payload["idempotent"] = True
                return Response(payload)

            ledger = PaymentLedger.objects.create(
                transaction_id=transaction_id,
                tx_ref=fw.tx_ref,
                plan_id=plan_id,
                amount=fw.amount,
                currency=fw.currency,
                expires_at=expires_at,
                user=request.user if request.user.is_authenticated else None,
            )

            if request.user.is_authenticated:
                _subscription_for_user(
                    request.user,
                    plan,
                    transaction_id,
                    receipt_data,
                    expires_at,
                )

    except IntegrityError:
        ledger = PaymentLedger.objects.filter(transaction_id=transaction_id).first()
        if ledger:
            if request.user.is_authenticated and not ledger.user_id:
                try:
                    _link_ledger_to_user(
                        ledger,
                        request.user,
                        get_plan(ledger.plan_id) or plan,
                        receipt_data,
                    )
                except PermissionError:
                    return Response(
                        {
                            "verified": False,
                            "detail": "This payment is already linked to another account",
                        },
                        status=status.HTTP_409_CONFLICT,
                    )
            payload = _ledger_success_payload(ledger, plan)
            payload["idempotent"] = True
            return Response(payload)
        return Response(
            {"verified": False, "detail": "Could not process payment"},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(
        {
            "verified": True,
            "idempotent": False,
            "plan_id": plan_id,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "transaction_id": transaction_id,
            "product_id": plan.product_id,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="20/m", method="POST", block=True)
def paystack_confirm(request):
    """
    Verify a Paystack transaction and grant premium (idempotent).
    """
    if getattr(request, "limited", False):
        return Response(
            {"verified": False, "detail": "Too many requests. Try again shortly."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    reference = str(request.data.get("reference", "")).strip()
    plan_id = str(request.data.get("plan_id", "")).strip().lower()

    if not reference or len(reference) > 128:
        return Response(
            {"verified": False, "detail": "Invalid reference"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    plan = get_plan(plan_id)
    if not plan:
        return Response(
            {"verified": False, "detail": "plan_id must be monthly or yearly"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        ps = verify_paystack_transaction(reference)
    except PaystackError as e:
        return Response(
            {"verified": False, "detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return _confirm_verified_payment(
        request=request,
        provider="paystack",
        ledger_transaction_id=f"paystack:{ps.reference}",
        tx_ref=ps.reference,
        plan_id=plan_id,
        plan=plan,
        paid_amount=ps.amount,
        paid_currency=ps.currency,
    )
