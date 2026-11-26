import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import FarmManager


class Farm(AbstractBaseUser, PermissionsMixin):
    """Entidade FARM do DER: conta autenticável da fazenda/criação."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Fazenda / Criação", max_length=150)
    owner_name = models.CharField("Responsável", max_length=150)
    email = models.EmailField("E-mail", unique=True)
    species_focus = models.CharField("Espécie foco", max_length=100, default="caprinos")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FarmManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "owner_name"]

    class Meta:
        verbose_name = "Fazenda"
        verbose_name_plural = "Fazendas"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.email})"


class Herd(models.Model):
    """Entidade HERD do DER (Fase 2: agrupamento de animais por lote/rebanho)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="herds")
    name = models.CharField("Nome do rebanho", max_length=120)
    species = models.CharField("Espécie", max_length=80, default="caprino")
    notes = models.TextField("Observações", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rebanho"
        verbose_name_plural = "Rebanhos"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} - {self.farm.name}"


class Animal(models.Model):
    """Entidade ANIMAL do DER (Fase 2: identificação individual no rebanho)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    herd = models.ForeignKey(
        Herd,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="animals",
    )
    code_tag = models.CharField("Brinco / identificação", max_length=80)
    species = models.CharField("Espécie", max_length=80, default="caprino")
    sex = models.CharField("Sexo", max_length=20, blank=True)
    birth_date = models.DateField("Data de nascimento", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Animal"
        verbose_name_plural = "Animais"
        ordering = ["code_tag"]

    def __str__(self) -> str:
        return f"{self.code_tag} ({self.species})"
