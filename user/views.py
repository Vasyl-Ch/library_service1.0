from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from user.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserDetailSerializer
)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()

    def get_serializer_class(self):

        if self.action == "create":
            return UserCreateSerializer

        elif self.action == "me":
            return UserDetailSerializer

        return UserSerializer

    def get_permissions(self):

        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=["get", "put", "patch"],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user

        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method in ["PUT", "PATCH"]:
            serializer = UserDetailSerializer(
                user,
                data=request.data,
                partial=(request.method == "PATCH")
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    def list(self, request, *args, **kwargs):

        if not request.user.is_staff:
            return Response(
                {
                    "detail":
                        "You do not have privileges "
                        "to view the list of users."
                },
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):

        if not request.user.is_staff:
            return Response(
                {"detail": "You don't have rights to see other users."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().retrieve(request, *args, **kwargs)
