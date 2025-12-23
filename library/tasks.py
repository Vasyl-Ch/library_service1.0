from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from library.models import Borrowing, Payment
from library.telegram_service import TelegramService


@shared_task
def send_borrowing_notification(borrowing_id):
    """
    Triggered right after creating a Borrowing
    """
    try:
        borrowing = Borrowing.objects.select_related("user", "book").get(
            id=borrowing_id
        )
        telegram = TelegramService()
        telegram.send_borrowing_notification(borrowing)
    except Borrowing.DoesNotExist:
        pass


@shared_task
def send_return_notification(borrowing_id):
    """
    Triggered after setting actual_return_date
    """
    try:
        borrowing = Borrowing.objects.select_related("user", "book").get(
            id=borrowing_id
        )
        telegram = TelegramService()
        telegram.send_return_notification(borrowing)
    except Borrowing.DoesNotExist:
        pass


@shared_task
def send_payment_notification(payment_id):
    """
    Triggered after successful payment
    """
    try:
        payment = Payment.objects.select_related(
            "borrowing__user", "borrowing__book"
        ).get(id=payment_id)
        telegram = TelegramService()
        telegram.send_payment_notification(payment)
    except Payment.DoesNotExist:
        pass


@shared_task
def send_daily_report():
    """
    Shows statistics for the last 24 hours
    """
    telegram = TelegramService()

    yesterday = timezone.now() - timedelta(days=1)

    new_borrowings = Borrowing.objects.filter(
        borrow_date__gte=yesterday
    ).count()

    returns = Borrowing.objects.filter(
        actual_return_date__gte=yesterday
    ).count()

    payments = Payment.objects.filter(
        created_at__gte=yesterday, status=Payment.Status.PAID
    )
    total_earned = sum(
        p.money_to_pay for p in payments
    ) or Decimal("0")

    message = (
        f"📊 <b>Daily Report</b>\n"
        f"Period: last 24 hours\n\n"
        f"📚 New borrowings: {new_borrowings}\n"
        f"✅ Returns: {returns}\n"
        f"💰 Earnings: ${total_earned}\n"
        f"💳 Payments: {payments.count()}\n"
    )

    telegram.send_message(message)
