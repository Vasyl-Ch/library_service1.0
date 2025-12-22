from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from library.models import (
    Author,
    Book,
    Borrowing,
    Payment
)
from library.permissions import IsAdminOrIfAuthenticatedReadOnly
from library.serializers import (
    AuthorSerializer,
    BookSerializer,
    BorrowingSerializer,
    PaymentSerializer, BookListSerializer, BorrowingCreateSerializer, BorrowingListSerializer,
    BorrowingReturnSerializer, PaymentListSerializer, PaymentCreateSerializer
)
from library.stripe_system import StripeService


class LibraryBaseViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAdminOrIfAuthenticatedReadOnly]
        return [permission() for permission in permission_classes]


class AuthorViewSet(LibraryBaseViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "surname"]
    ordering_fields = ["name", "surname"]
    ordering = ["name"]


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="is_active",
            type=str,
            description="Filtering by Return Status: 'true', 'false'",
            required=False,
        )
    ]
)
class BookViewSet(LibraryBaseViewSet):
    queryset = Book.objects.prefetch_related("authors")
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "authors__name", "authors__surname"]
    ordering_fields = ["title", "inventory", "daily_fee"]
    ordering = ["title"]

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        return BookSerializer

    def destroy(self, request, *args, **kwargs):

        instance = self.get_object()
        active_borrowings = instance.borrowings.filter(
            actual_return_date__isnull=True
        ).exists()

        if active_borrowings:
            return Response(
                {
                    "detail": f"Can't delete a book. "
                              f"There are {active_borrowings.count()} active borrowings."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)


class BorrowingViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ("book__title",)
    ordering_fields = ("borrow_date", "expected_return_date")
    ordering = ("borrow_date",)

    def get_queryset(self):
        user = self.request.user

        queryset = Borrowing.objects.select_related("book", "user")

        if not user.is_staff:
            queryset = queryset.filter(user=user)

        is_active = self.request.query_params.get("is_active", None)

        if is_active is not None:

            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)

            elif is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)

        return queryset.order_by("borrow_date")

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "create":
            return BorrowingCreateSerializer

        elif self.action == "return_book":
            return BorrowingReturnSerializer

        return BorrowingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        borrowing = serializer.instance
        return_serializer = BorrowingListSerializer(borrowing)

        return Response(return_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={200: BorrowingListSerializer},
        description="Method for returning the book (sets the actual return date)"
    )
    @action(detail=True, methods=["post"], url_path="return")
    def return_book(self, request, *args, **kwargs):
        borrowing = self.get_object()

        serializer = self.get_serializer(
            borrowing, data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        borrowing = serializer.save()

        return Response(
            {
                "detail": "The book has been successfully returned.",
                "borrowing": BorrowingListSerializer(borrowing).data,
            },
            status=status.HTTP_200_OK,
        )


class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ("borrowing__book__title",)
    ordering_fields = ("status", "created_at",)
    ordering = ("status","created_at",)

    def get_queryset(self):
        user = self.request.user

        queryset = Payment.objects.select_related(
            "borrowing",
            "borrowing__book",
            "borrowing__user"
        )

        if not user.is_staff:
            queryset = queryset.filter(borrowing__user=user)

        return queryset

    def get_serializer_class(self):

        if self.action == "list":
            return PaymentListSerializer

        if self.action in["create", "retrieve"]:
            return PaymentCreateSerializer

        return PaymentSerializer

    @extend_schema(
        responses={201: PaymentSerializer},
        description="Creates a payment and returns a Stripe payment link (session_url)"
    )
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        try:
            stripe_data = StripeService.get_or_create_session_for_borrowing(
                payment.borrowing, request
            )
            return Response(
                {
                    "message": "Payment session created/updated. Follow the link to pay.",
                    "session_url": stripe_data["session_url"] if stripe_data else payment.session_url,
                    "payment": PaymentSerializer(payment).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            payment.delete()
            return Response(
                {"error": f"Error when creating a payment: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=str,
                description="Stripe session ID for payment confirmation",
                required=True
            )
        ]
    )
    @action(detail=False, methods=["get"])
    def success(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "Session ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.filter(session_id=session_id).first()

            if not payment:
                return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

            if StripeService.is_session_paid(session_id):
                session = StripeService.retrieve_session(session_id)

                payment_ids_raw = session.metadata.get("payment_ids", "")
                payment_ids = [int(pid) for pid in payment_ids_raw.split(",") if pid.isdigit()]

                if not payment_ids:
                    payment_ids = list(Payment.objects.filter(session_id=session_id).values_list('id', flat=True))

                Payment.objects.filter(id__in=payment_ids).update(
                    status=Payment.Status.PAID
                )

                return Response({
                    "message": "Payment was successful!",
                    "payment_ids": payment_ids,
                    "status": "PAID",
                })

            return Response({"error": "Payment is not completed yet."}, status=status.HTTP_400_BAD_REQUEST)


        except Exception as e:
            return Response({"error": f"Payment processing error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def cancel(self, request):
        """
        Payment cancellation processing.
        Called when a user cancels a payment in Stripe.

        GET /payments/cancel/
        """
        return Response(
            {
                "message": "Payment canceled. You can try again later.",
                "note": "The payment remains in the PENDING status. "
                        "You can pay it through the payment list.",
            }
        )

    @extend_schema(
        responses={200: PaymentCreateSerializer(many=True)},
        description="List of all pending (PENDING) payments of the current user"
    )
    @action(detail=False, methods=["get"])
    def pending(self, request):

        queryset = self.get_queryset().filter(
            borrowing__user=request.user,
            status=Payment.Status.PENDING
        )

        serializer = PaymentCreateSerializer(queryset, many=True)

        return Response({"count": queryset.count(), "results": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status == Payment.Status.PAID:

            try:
                StripeService.get_or_create_session_for_borrowing(instance.borrowing, request)
                instance.refresh_from_db()

            except Exception as e:
                return Response(
                    {"error": f"Error updating payment link: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
