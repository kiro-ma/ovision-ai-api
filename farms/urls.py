from django.urls import path

from .views import (
    FarmProfileView,
    FarmRegisterView,
    FarmTokenObtainPairView,
    FarmTokenRefreshView,
)

urlpatterns = [
    path("register/", FarmRegisterView.as_view(), name="farm-register"),
    path("token/", FarmTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", FarmTokenRefreshView.as_view(), name="token-refresh"),
    path("me/", FarmProfileView.as_view(), name="farm-profile"),
]
