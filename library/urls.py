from django.urls import path, include
from rest_framework.routers import DefaultRouter
from library.views import (
    PaymentViewSet,
    BorrowingViewSet,
    AuthorViewSet,
    BookViewSet
)

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")
router.register("borrowings", BorrowingViewSet, basename="borrowing")
router.register("authors", AuthorViewSet, basename="author")
router.register("books", BookViewSet, basename="book")


urlpatterns = [
    path("", include(router.urls)),
]

app_name = "library"
