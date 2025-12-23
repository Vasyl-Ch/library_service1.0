import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending notifications to Telegram"""

    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.chat_id = settings.TELEGRAM_CHAT_ID

    async def _send_message_async(self, message: str) -> bool:
        """Asynchronous message sending"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode="HTML"
            )
            logger.info(f"Message sent to Telegram: {message[:50]}...")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_message(self, message: str) -> bool:
        """Synchronous wrapper for sending messages"""
        try:
            return asyncio.run(self._send_message_async(message))
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return False

    def send_borrowing_notification(self, borrowing) -> bool:
        """New borrowing notification"""
        message = (
            f"📚 <b>New Borrowing</b>\n\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Return date: {borrowing.expected_return_date}\n"
        )
        return self.send_message(message)

    def send_return_notification(self, borrowing) -> bool:
        """Book return notification"""
        message = (
            f"✅ <b>Book Returned</b>\n\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Return date: {borrowing.actual_return_date}\n"
        )
        return self.send_message(message)

    def send_payment_notification(self, payment) -> bool:
        """Payment notification"""
        message = (
            f"💰 <b>Payment Received</b>\n\n"
            f"User: {payment.borrowing.user.email}\n"
            f"Book: {payment.borrowing.book.title}\n"
            f"Amount: ${payment.money_to_pay}\n"
            f"Type: {payment.get_type_display()}\n"
        )
        return self.send_message(message)
