from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from library.models import Author, Book, Borrowing, Payment


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "surname"]
        read_only_fields = ["id"]


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True)
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
                new_authors = []
                for author_data in authors_data:
                    author, _ = Author.objects.get_or_create(**author_data)
                    new_authors.append(author)
                instance.authors.set(new_authors)

        instance.save()
        return instance

    def validate_inventory(self, value):
        if value < 0:
            raise serializers.ValidationError("Inventory cannot be negative")
        return value

    def validate_daily_fee(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("Daily fee cannot be negative")
        return value


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




