"""
Tests for Library API custom logic
Level: Junior
Only testing areas with potential issues
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.exceptions import ValidationError
from datetime import date, timedelta

from library.models import Book, Author, Borrowing
from library.serializers import (
    BorrowingCreateSerializer,
    BorrowingReturnSerializer
)

User = get_user_model()


class BorrowingModelTests(TestCase):
    """Test custom is_active property"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email="test@test.com",
            password="pass123",
            first_name="Test",
            last_name="User"
        )

        author = Author.objects.create(name="John", surname="Doe")

        self.book = Book.objects.create(
            title="Test Book",
            cover=Book.CoverType.SOFT,
            inventory=5,
            daily_fee=2.00
        )
        self.book.authors.add(author)

    def test_is_active_true_when_not_returned(self):
        """Test 1: is_active returns True when book is not returned"""
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=7),
            actual_return_date=None
        )

        self.assertTrue(borrowing.is_active)

    def test_is_active_false_when_returned(self):
        """Test 2: is_active returns False when book is returned"""
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=7),
            actual_return_date=date.today()
        )

        self.assertFalse(borrowing.is_active)


class BorrowingCreateSerializerTests(TestCase):
    """Test borrowing creation and validation"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            password="pass123",
            first_name="Test",
            last_name="User"
        )

        author = Author.objects.create(name="Author", surname="Test")

        self.book = Book.objects.create(
            title="Available Book",
            cover=Book.CoverType.SOFT,
            inventory=3,
            daily_fee=1.50
        )
        self.book.authors.add(author)

    def _get_mock_request(self, user):
        """Helper method to create mock request"""

        class MockRequest:
            def __init__(self, user):
                self.user = user

            def build_absolute_uri(self, path):
                """Mock method to generate URL"""
                return f"http://testserver{path}"

        return MockRequest(user)

    def test_create_borrowing_decreases_inventory(self):
        """Test 3: Creating borrowing decreases book inventory by 1"""
        initial_inventory = self.book.inventory

        data = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=5)
        }

        serializer = BorrowingCreateSerializer(
            data=data,
            context={"request": self._get_mock_request(self.user)}
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory - 1)

    def test_cannot_borrow_book_with_zero_inventory(self):
        """Test 4: Cannot borrow book with zero inventory"""
        self.book.inventory = 0
        self.book.save()

        data = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=5)
        }

        serializer = BorrowingCreateSerializer(
            data=data,
            context={"request": self._get_mock_request(self.user)}
        )

        self.assertTrue(serializer.is_valid())

        with self.assertRaises(ValidationError):
            serializer.save()

    def test_user_cannot_borrow_same_book_twice(self):
        """Test 5: User cannot borrow the same book twice"""
        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=7),
            actual_return_date=None
        )

        data = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=5)
        }

        serializer = BorrowingCreateSerializer(
            data=data,
            context={"request": self._get_mock_request(self.user)}
        )

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_expected_return_date_cannot_be_in_past(self):
        """Test 6: Expected return date cannot be in the past"""
        past_date = timezone.now().date() - timedelta(days=1)

        data = {
            "book": self.book.id,
            "expected_return_date": past_date
        }

        serializer = BorrowingCreateSerializer(
            data=data,
            context={"request": self._get_mock_request(self.user)}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("expected_return_date", serializer.errors)
        self.assertEqual(
            str(serializer.errors["expected_return_date"][0]),
            "Expected return date cannot be in the past"
        )


class BorrowingReturnSerializerTests(TestCase):
    """Test book return functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            password="pass123",
            first_name="Test",
            last_name="User"
        )

        author = Author.objects.create(name="Author", surname="Test")

        self.book = Book.objects.create(
            title="Book to Return",
            cover=Book.CoverType.SOFT,
            inventory=2,
            daily_fee=2.00
        )
        self.book.authors.add(author)

        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=3),
            actual_return_date=None
        )

    def _get_mock_request(self, user):
        """Helper method to create mock request"""

        class MockRequest:
            def __init__(self, user):
                self.user = user

            def build_absolute_uri(self, path):
                return f"http://testserver{path}"

        return MockRequest(user)

    def test_return_increases_inventory(self):
        """Test 7: Returning book increases inventory by 1"""
        initial_inventory = self.book.inventory

        serializer = BorrowingReturnSerializer(
            instance=self.borrowing,
            data={},
            context={"request": self._get_mock_request(self.user)}
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory + 1)

    def test_cannot_return_book_twice(self):
        """Test 8: Cannot return book twice"""
        self.borrowing.actual_return_date = date.today()
        self.borrowing.save()

        serializer = BorrowingReturnSerializer(
            instance=self.borrowing,
            data={},
            context={"request": self._get_mock_request(self.user)}
        )

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


class BorrowingViewSetTests(TestCase):
    """Test filtering and permissions"""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass123",
            first_name="Regular",
            last_name="User"
        )

        author = Author.objects.create(name="Author", surname="Test")

        self.book = Book.objects.create(
            title="Test Book",
            cover=Book.CoverType.SOFT,
            inventory=10,
            daily_fee=1.00
        )
        self.book.authors.add(author)

        self.client.force_authenticate(user=self.user)

    def test_filter_is_active_true_shows_only_unreturned(self):
        """Test 9: is_active=true filter shows only unreturned books"""
        active = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=5),
            actual_return_date=None
        )

        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=5),
            actual_return_date=date.today()
        )

        url = reverse("library:borrowing-list")
        response = self.client.get(url, {"is_active": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], active.id)

    def test_user_sees_only_own_borrowings(self):
        """Test 10: Regular users can only see their own borrowings"""
        other_user = User.objects.create_user(
            email="other@test.com",
            password="pass123",
            first_name="Other",
            last_name="User"
        )

        own = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=5)
        )

        Borrowing.objects.create(
            book=self.book,
            user=other_user,
            expected_return_date=date.today() + timedelta(days=5)
        )

        url = reverse("library:borrowing-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], own.id)
