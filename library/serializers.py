from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from library.models import (
    Author,
    Book,
    Borrowing,
    Payment
)
from library.stripe_system import StripeService
from library.tasks import send_borrowing_notification, send_return_notification


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "surname"]
        read_only_fields = ["id"]


class BookSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Author.objects.all()
    )
    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "authors",
            "cover",
            "inventory",
            "daily_fee"
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):

        with transaction.atomic():
            authors_data = validated_data.pop("authors")
            book = Book.objects.create(**validated_data)
            for author in authors_data:
                book.authors.add(author)
            return book

    def update(self, instance: Book, validated_data):

        with transaction.atomic():
            authors_data = validated_data.pop("authors", None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            if authors_data is not None:
                instance.authors.set(authors_data)

        instance.save()
        return instance


class BookListSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "authors",
            "cover",
            "inventory",
            "daily_fee",
            "availability"
        ]

    def get_authors(self, obj: Book) -> list[str]:
        return [
            f"{author.name} {author.surname}" for author in obj.authors.all()
        ]

    def get_availability(self, obj: Book) -> str:
        return "Available" if obj.inventory > 0 else "Not available"


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="borrowing.user.email", read_only=True)
    book_title = serializers.CharField(source="borrowing.book.title", read_only=True)
    session_url = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "type",
            "user_email",
            "borrowing",
            "book_title",
            "money_to_pay",
            "session_url",
            "session_id",
            "created_at"
        ]
        read_only_fields = [
            "id",
            "status",
            "user_email",
            "book_title",
            "money_to_pay",
            "session_url",
            "session_id",
            "created_at"
        ]

    def get_session_url(self, obj: Payment) -> None | str:
        if obj.status == Payment.Status.PENDING and obj.money_to_pay > 0:
            return obj.session_url
        return None


class PaymentListSerializer(PaymentSerializer):
    borrowing_id = serializers.CharField(source="borrowing.id", read_only=True)
    username = serializers.CharField(source="borrowing.user.__str__", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "type",
            "borrowing_id",
            "username",
            "book_title",
            "money_to_pay",
            "session_url",
            "created_at"
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    borrowing = serializers.PrimaryKeyRelatedField(
        queryset=Borrowing.objects.none(), required=True
    )

    class Meta:
        model = Payment
        fields = [
            "borrowing"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user is None or not user.is_authenticated:
            self.fields["borrowing"].queryset = Borrowing.objects.none()
            return

        if user.is_staff:
            queryset = Borrowing.objects.all()

        else:
            queryset = Borrowing.objects.filter(user=user)

        self.fields["borrowing"].queryset = queryset.select_related("book")

    def validate(self, attrs):
        user = self.context["request"].user
        borrowing = attrs["borrowing"]

        if borrowing.user != user and not user.is_staff:
            raise serializers.ValidationError(
                "You can create a payment only for your own issue."
            )

        existing_payment = Payment.objects.filter(
            borrowing__user=borrowing.user,
            borrowing__book=borrowing.book,
            status=Payment.Status.PENDING,
        ).first()

        if existing_payment:
            raise serializers.ValidationError(
                f"There is already an active payment for this book. "
                f"Payment ID: {existing_payment.id}"
            )

        return attrs

    def create(self, validated_data):
        borrowing = validated_data["borrowing"]

        with transaction.atomic():
            if Payment.objects.filter(
                    borrowing=borrowing,
                    status=Payment.Status.PENDING
            ).exists():
                raise serializers.ValidationError(
                    "Pending payment already exists for this borrowing."
                )

            actual_days = max(
                (borrowing.expected_return_date - borrowing.borrow_date).days, 1
            )
            rental_money = borrowing.book.daily_fee * actual_days

            payment = Payment.objects.create(
                borrowing=borrowing,
                money_to_pay=rental_money,
                type=Payment.Type.PAYMENT,
                status=Payment.Status.PENDING
            )

            overdue_days = max(
                0, (timezone.localdate() - borrowing.expected_return_date).days
            )

            if overdue_days > 0:
                fine_money = overdue_days * borrowing.book.daily_fee * Decimal("2")
                Payment.objects.create(
                    borrowing=borrowing,
                    money_to_pay=fine_money,
                    type=Payment.Type.FINE,
                    status=Payment.Status.PENDING
                )

        return payment


class BorrowingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = [
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "user"
        ]
        read_only_fields = ["id", "borrow_date", "actual_return_date"]


class BorrowingListSerializer(serializers.ModelSerializer):
    book = serializers.CharField(source="book.title", read_only=True)
    user = serializers.CharField(source="user.__str__", read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_borrowed = serializers.SerializerMethodField()

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "book",
            "user",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "is_active",
            "days_borrowed"
        ]

    def get_days_borrowed(self, obj: Borrowing) -> int:
        if obj.actual_return_date is not None:
            diff = (obj.actual_return_date - obj.borrow_date).days

        else:
            diff = (timezone.localdate() - obj.borrow_date).days

        return max(1, diff)



class BorrowingCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = [
            "book",
            "expected_return_date"
        ]

    def validate_expected_return_date(self, value):

        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Expected return date cannot be in the past"
            )
        return value


    def validate(self, attrs):

        user = self.context["request"].user
        book = attrs["book"]

        if Borrowing.objects.filter(
                book=book,
                user=user,
                actual_return_date__isnull=True
        ).exists():
            raise serializers.ValidationError(
                "User already has this book borrowed"
            )

        return attrs

    def create(self, validated_data):
        with transaction.atomic():

            book = Book.objects.select_for_update().get(
                id=validated_data["book"].id
            )

            if book.inventory <= 0:
                raise serializers.ValidationError(
                    f"Book {book.title} is not available"
                )

            book.inventory -= 1
            book.save()

            borrowing = Borrowing.objects.create(
                user=self.context["request"].user, **validated_data
            )
            send_borrowing_notification.delay(borrowing.id)

            return borrowing


class BorrowingReturnSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = ["id", "actual_return_date"]
        read_only_fields = ["id", "actual_return_date"]

    def validate(self, attrs):
        borrowing = self.instance

        if borrowing.actual_return_date is not None:
            raise serializers.ValidationError(
                "The book has already been returned."
            )

        request = self.context.get("request")
        unpaid_payments = Payment.objects.filter(
            borrowing=borrowing,
            status=Payment.Status.PENDING
        )

        if unpaid_payments.exists() and not request.user.is_staff:
            raise serializers.ValidationError(
                "You have unpaid invoices for this borrowing. "
                "Pay them before returning."
            )
        return attrs

    def update(self, instance, validated_data):

        current_date = timezone.localdate()
        request = self.context.get("request")

        has_pending_payments = Payment.objects.filter(
            borrowing=instance,
            status=Payment.Status.PENDING
        ).exists()

        if has_pending_payments and not request.user.is_staff:
            raise serializers.ValidationError(
                "The book cannot be returned: "
                "the invoice created must be paid."
            )

        existing_payments = Payment.objects.filter(borrowing=instance)

        if not existing_payments.exists():
            payment_serializer = PaymentCreateSerializer(
                data={"borrowing": instance.id},
                context={"request": request}
            )
            payment_serializer.is_valid(raise_exception=True)
            payment_serializer.save()

            StripeService.get_or_create_session_for_borrowing(instance, request)

        with transaction.atomic():

            book = Book.objects.select_for_update().get(id=instance.book_id)
            book.inventory += 1
            book.save()

            instance.actual_return_date = current_date
            instance.save()

        send_return_notification.delay(instance.id)

        return instance
