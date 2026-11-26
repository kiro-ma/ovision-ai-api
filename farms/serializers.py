from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Farm


class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ("id", "name", "owner_name", "email", "species_focus", "created_at")
        read_only_fields = ("id", "created_at")


class FarmRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Farm
        fields = ("id", "name", "owner_name", "email", "password", "species_focus", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        password = validated_data.pop("password")
        return Farm.objects.create_user(password=password, **validated_data)


class FarmTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Retorna os tokens JWT acompanhados dos dados básicos da fazenda."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["farm"] = FarmSerializer(self.user).data
        return data
