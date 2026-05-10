# payments/views.py
import stripe
import logging
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from ..models import Payment
from ..models import Order
from microservices.producer import publish_message

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """
    Receive and process Stripe webhook events.
    Stripe calls this endpoint to notify us about payment state changes.
    """

    authentication_classes = []  # No JWT needed — Stripe signs the request instead
    permission_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.headers.get("Stripe-Signature")

        # Verify the webhook came from Stripe using the signing secret
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Invalid Stripe webhook signature: {e}")
            return Response("Invalid signature", status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return Response("Webhook error", status=status.HTTP_400_BAD_REQUEST)

        # Handle different event types
        if event.type == "payment_intent.succeeded":
            return self._handle_payment_succeeded(event)

        elif event.type == "payment_intent.payment_failed":
            return self._handle_payment_failed(event)

        elif event.type == "charge.refunded":
            return self._handle_refund(event)

        else:
            # Event type we don't care about, but still return 200
            logger.info(f"Unhandled event type: {event.type}")
            return Response(status=status.HTTP_200_OK)

    def _handle_payment_succeeded(self, event):
        """Payment succeeded — confirm the order and start fulfillment."""
        intent = event.data.object
        order_id = int(intent._data["metadata"]["order_id"])

        if not order_id:
            logger.error(f"PaymentIntent {intent.id} missing order_id in metadata")
            return Response(status=status.HTTP_200_OK)

        try:
            with transaction.atomic():
                # Update payment record
                payment = Payment.objects.filter(intent_id=intent.id).select_for_update().first()

                if not payment:
                    logger.error(f"Payment not found for intent {intent.id}")
                    return Response(status=status.HTTP_200_OK)

                payment.status = Payment.COMPLETE
                payment.save()

                # Update order status
                order = Order.objects.filter(id=order_id).select_for_update().first()
                if order:
                    order.status = Order.CONFIRMED
                    order.save()

        except Exception as e:
            logger.error(f"Error handling payment_intent.succeeded: {e}")
            # Still return 200 so Stripe doesn't retry infinitely
            # The payment succeeded on Stripe's side; our database is the issue

        return Response(status=status.HTTP_200_OK)

    def _handle_payment_failed(self, event):
        """Payment failed — release the stock reservation."""
        intent = event.data.object
        order_id = int(intent._data["metadata"]["order_id"])

        if not order_id:
            logger.error(f"PaymentIntent {intent.id} missing order_id in metadata")
            return Response(status=status.HTTP_200_OK)

        try:
            with transaction.atomic():
                # Update payment record
                payment = Payment.objects.filter(intent_id=intent.id).select_for_update().first()

                if payment:
                    payment.status = Payment.UNPAID
                    payment.save()

                # Update order status
                order = Order.objects.filter(id=order_id).select_for_update().first()
                if order:
                    order.status = Order.CANCELLED
                    order.save()

                # Release the stock reservation
                order_items = order.order_items.all().values_list("product_id", "quantity")
                items_data = [{"product_id": pid, "quantity": qty} for pid, qty in order_items]

                publish_message(items_data, "release-product")

                logger.warning(f"Payment failed for order {order_id}: {intent.last_payment_error}")

        except Exception as e:
            logger.error(f"Error handling payment_intent.payment_failed: {e}")

        return Response(status=status.HTTP_200_OK)

    def _handle_refund(self, event):
        """Refund issued — mark payment as refunded."""
        charge = event.data.object
        intent_id = charge.payment_intent

        try:
            payment = Payment.objects.filter(intent_id=intent_id).select_for_update().first()

            if payment:
                payment.status = Payment.REFUNDED
                payment.save()

                # Optionally cancel the order
                order = payment.order
                if order and order.status == "confirmed":
                    order.status = Order.REFUNDED
                    order.save()

                logger.info(f"Refund processed for payment {intent_id}")

        except Exception as e:
            logger.error(f"Error handling charge.refunded: {e}")

        return Response(status=status.HTTP_200_OK)
