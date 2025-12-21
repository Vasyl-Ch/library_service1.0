from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="__str__", read_only=True)
    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "is_staff"
        ]
        read_only_fields = ["id", "is_staff"]


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8
    )

    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm"
        ]

    def validate(self, attrs):

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        return User.objects.create_user(**validated_data)


class UserDetailSerializer(serializers.ModelSerializer):

    borrowings_count = serializers.SerializerMethodField()
    active_borrowings = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "date_joined",
            "borrowings_count",
            "active_borrowings"
        ]
        read_only_fields = ["id", "is_staff", "date_joined"]

    def get_borrowings_count(self, obj: User) -> int:
        return getattr(obj, "borrowings_count", obj.borrowings.count())

    def get_active_borrowings(self, obj: User) -> int:
        return getattr(
            obj,
            "active_borrowings",
            obj.borrowings.filter(actual_return_date__isnull=True).count()
        )