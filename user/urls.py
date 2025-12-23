from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user.views import UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "user"
