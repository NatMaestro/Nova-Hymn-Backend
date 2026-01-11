"""
RevenueCat Webhook Handler

This module handles webhooks from RevenueCat for subscription events.
RevenueCat sends webhooks when subscriptions are created, renewed, cancelled, etc.

To set up webhooks in RevenueCat:
1. Go to RevenueCat Dashboard > Project Settings > Webhooks
2. Add webhook URL: https://yourdomain.com/api/v1/webhooks/revenuecat/
3. Select events to receive (recommended: all subscription events)
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json
import hmac
import hashlib
import logging

from .models import User, Subscription
from .serializers import SubscriptionSerializer

logger = logging.getLogger(__name__)

# RevenueCat webhook secret - Get this from RevenueCat dashboard
# Store in environment variable: REVENUECAT_WEBHOOK_SECRET
import os
REVENUECAT_WEBHOOK_SECRET = os.environ.get('REVENUECAT_WEBHOOK_SECRET', '')


def verify_webhook_signature(request_body: bytes, signature: str) -> bool:
    """
    Verify RevenueCat webhook signature to ensure request is authentic.
    """
    if not REVENUECAT_WEBHOOK_SECRET:
        logger.warning("RevenueCat webhook secret not configured. Skipping signature verification.")
        return True  # In development, you might want to skip verification
    
    expected_signature = hmac.new(
        REVENUECAT_WEBHOOK_SECRET.encode('utf-8'),
        request_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def revenuecat_webhook(request):
    """
    Handle RevenueCat webhook events.
    
    RevenueCat sends webhooks for various events:
    - INITIAL_PURCHASE: First purchase
    - RENEWAL: Subscription renewed
    - CANCELLATION: Subscription cancelled
    - UNCANCELLATION: Cancelled subscription reactivated
    - EXPIRATION: Subscription expired
    - BILLING_ISSUE: Payment issue
    - PRODUCT_CHANGE: Subscription product changed
    
    Webhook payload structure:
    {
        "event": {
            "id": "event_id",
            "type": "INITIAL_PURCHASE",
            "app_user_id": "user_id",
            "product_id": "com.novahymnal.premium.monthly",
            "period_type": "NORMAL",
            "purchased_at_ms": 1234567890,
            "expires_at_ms": 1234567890,
            "environment": "SANDBOX",
            "entitlement_ids": ["premium"],
            ...
        }
    }
    """
    try:
        # Verify webhook signature
        signature = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not verify_webhook_signature(request.body, signature):
            logger.warning("Invalid webhook signature")
            return Response(
                {'error': 'Invalid signature'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Parse webhook payload
        payload = json.loads(request.body)
        event = payload.get('event', {})
        event_type = event.get('type')
        app_user_id = event.get('app_user_id')
        product_id = event.get('product_id')
        purchased_at_ms = event.get('purchased_at_ms')
        expires_at_ms = event.get('expires_at_ms')
        environment = event.get('environment', 'PRODUCTION')
        entitlement_ids = event.get('entitlement_ids', [])
        transaction_id = event.get('transaction_id', '')
        original_transaction_id = event.get('original_transaction_id', transaction_id)

        logger.info(f"Received RevenueCat webhook: {event_type} for user {app_user_id}")

        # Get or create user by app_user_id
        # Note: app_user_id should match your user's ID
        try:
            user = User.objects.get(id=int(app_user_id))
        except (User.DoesNotExist, ValueError):
            logger.warning(f"User not found for app_user_id: {app_user_id}")
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Handle different event types
        if event_type in ['INITIAL_PURCHASE', 'RENEWAL', 'UNCANCELLATION']:
            # Create or update active subscription
            purchased_at = timezone.datetime.fromtimestamp(purchased_at_ms / 1000, tz=timezone.utc) if purchased_at_ms else timezone.now()
            expires_at = timezone.datetime.fromtimestamp(expires_at_ms / 1000, tz=timezone.utc) if expires_at_ms else None
            
            # Determine subscription type from product_id
            subscription_type = 'monthly'
            if 'yearly' in product_id.lower():
                subscription_type = 'yearly'
            elif 'lifetime' in product_id.lower():
                subscription_type = 'lifetime'
                expires_at = None  # Lifetime subscriptions don't expire

            # Determine platform from product_id or environment
            platform = 'ios' if 'ios' in product_id.lower() or environment == 'SANDBOX' else 'android'

            subscription, created = Subscription.objects.update_or_create(
                transaction_id=transaction_id,
                defaults={
                    'user': user,
                    'product_id': product_id,
                    'original_transaction_id': original_transaction_id,
                    'subscription_type': subscription_type,
                    'status': 'active',
                    'platform': platform,
                    'started_at': purchased_at,
                    'expires_at': expires_at,
                    'receipt_data': json.dumps(payload),  # Store full payload for reference
                }
            )

            logger.info(f"Subscription {'created' if created else 'updated'}: {subscription.id}")

        elif event_type == 'CANCELLATION':
            # Mark subscription as cancelled (but still active until expiration)
            subscription = Subscription.objects.filter(
                user=user,
                original_transaction_id=original_transaction_id
            ).first()

            if subscription:
                subscription.status = 'cancelled'
                subscription.cancelled_at = timezone.now()
                subscription.save()
                logger.info(f"Subscription cancelled: {subscription.id}")

        elif event_type == 'EXPIRATION':
            # Mark subscription as expired
            subscription = Subscription.objects.filter(
                user=user,
                original_transaction_id=original_transaction_id
            ).first()

            if subscription:
                subscription.status = 'expired'
                subscription.expires_at = timezone.now()
                subscription.save()
                logger.info(f"Subscription expired: {subscription.id}")

        elif event_type == 'BILLING_ISSUE':
            # Handle billing issue (subscription still active but payment failed)
            subscription = Subscription.objects.filter(
                user=user,
                original_transaction_id=original_transaction_id
            ).first()

            if subscription:
                # You might want to add a 'billing_issue' status or handle differently
                logger.warning(f"Billing issue for subscription: {subscription.id}")

        # Return success response
        return Response({'status': 'success'}, status=status.HTTP_200_OK)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return Response(
            {'error': 'Invalid JSON'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

