from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    FarmRegisterSerializer,
    FarmSerializer,
    FarmTokenObtainPairSerializer,
)


class FarmRegisterView(APIView):
    """Cadastro simples de fazenda/usuário para testes e onboarding inicial."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = FarmRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        farm = serializer.save()

        refresh = RefreshToken.for_user(farm)
        return Response(
            {
                "farm": FarmSerializer(farm).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class FarmTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FarmTokenObtainPairSerializer


class FarmTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class FarmProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(FarmSerializer(request.user).data, status=status.HTTP_200_OK)
