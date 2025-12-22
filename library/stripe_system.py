import stripe
from django.conf import settings
from library.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    @staticmethod
    def _get_urls(request):
        """An auxiliary method for URL formation."""
        return {
            "success_url": request.build_absolute_uri("/api/payments/success/") + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": request.build_absolute_uri("/api/payments/cancel/")
        }

    @staticmethod
    def create_checkout_session(payments, success_url, cancel_url):
        """
        A universal method to create a Stripe session.
        Accepts a list of payments (even if there is only one).
        """
        if not payments:
            raise Exception("No payments provided")

        try:
            line_items = []
            payment_ids = []

            for payment in payments:
                payment_ids.append(str(payment.id))
                amount_in_cents = int(payment.money_to_pay * 100)
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_in_cents,
                        "product_data": {
                            "name": f"{payment.get_type_display()} for borrowing #{payment.borrowing.id}",
                            "description": f"Book: {payment.borrowing.book.title}",
                        },
                    },
                    "quantity": 1,
                })

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "payment_ids": ",".join(payment_ids),
                    "borrowing_id": str(payments[0].borrowing.id),
                },
            )

            return {
                "session_id": checkout_session.id,
                "session_url": checkout_session.url,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe API Error: {str(e)}")

    @staticmethod
    def get_or_create_session_for_borrowing(borrowing, request):
        """
        Basic method: finds all PENDING borrowing payments,
        creates a general session for them and updates the database.
        """
        pending_payments = Payment.objects.filter(
            borrowing=borrowing,
            status=Payment.Status.PENDING,
        )

        if not pending_payments.exists():
            return None

        urls = StripeService._get_urls(request)
        stripe_data = StripeService.create_checkout_session(
            payments=list(pending_payments),
            **urls
        )

        pending_payments.update(
            session_url=stripe_data["session_url"],
            session_id=stripe_data["session_id"]
        )

        return stripe_data

    @staticmethod
    def retrieve_session(session_id):
        try:
            return stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Session Acquisition Error: {str(e)}")

    @staticmethod
    def is_session_paid(session_id):
        try:
            session = StripeService.retrieve_session(session_id)
            return session.payment_status == "paid"
        except Exception:
            return False