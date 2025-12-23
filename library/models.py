from decimal import Decimal
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db import models
from django.conf import settings


class Author(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} {self.surname}"

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"


class Book(models.Model):

    class CoverType(models.TextChoices):
        HARD = "Hard"
        SOFT = "Soft"

    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(to=Author)
    cover = models.CharField(
        choices=CoverType.choices,
        default=CoverType.SOFT,
        verbose_name="Book cover type",
    )
    inventory = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Book inventory",
    )
    daily_fee = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Book daily fee",
    )

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ["title"]

    def __str__(self):
        return f"{self.title}, left ({self.inventory})"


class Borrowing(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrowings"
    )
    borrow_date = models.DateField(
        default=timezone.localdate,
        verbose_name="Borrow date"
    )
    expected_return_date = models.DateField(
        verbose_name="Expected return date"
    )
    actual_return_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Actual return date"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings",
        verbose_name="User",
    )

    class Meta:
        verbose_name = "Borrowing"
        verbose_name_plural = "Borrowings"
        ordering = ["-borrow_date"]

    def __str__(self):
        status = "Returned" \
            if self.actual_return_date \
            else "Not returned"
        return (f"{self.user.email} "
                f"borrowed {self.book.title} ({status})")

    @property
    def is_active(self):
        return self.actual_return_date is None


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "Pending"
        PAID = "Paid"

    class Type(models.TextChoices):
        PAYMENT = "Payment"
        FINE = "Fine"

    status = models.CharField(
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Payment Status",
    )
    payment_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.PAYMENT,
        verbose_name="Payment Type",
    )
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE)
    session_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Session URL"
    )
    session_id = models.CharField(
        blank=True,
        null=True,
        verbose_name="Session ID"
    )
    money_to_pay = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Money to pay",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]

    def __str__(self):
        return (f"Payment {self.payment_type} "
                f"- {self.money_to_pay} ({self.status})")
