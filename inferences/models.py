import uuid

from django.conf import settings
from django.db import models


class InferenceRecord(models.Model):
    """Entidade INFERENCE_RECORD do DER: histórico de inferências por fazenda (e por animal na Fase 2)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inferences",
    )
    animal = models.ForeignKey(
        "farms.Animal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inferences",
    )
    original_filename = models.CharField("Arquivo original", max_length=255)
    image_url = models.CharField("URL da imagem inferida", max_length=1000)
    image_path = models.CharField("Caminho no storage", max_length=500)
    distance_cm = models.FloatField("Distância da câmera (cm)")
    model_tag = models.CharField("Modelo / pesos", max_length=120)
    conf_threshold = models.FloatField("Limiar de confiança", default=0.25)
    imgsz = models.IntegerField("Resolução de inferência", default=1280)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Inferência"
        verbose_name_plural = "Registros de Inferência"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.original_filename} ({self.model_tag}) - {self.farm.name}"


class BiometricMeasurement(models.Model):
    """Entidade BIOMETRIC_MEASUREMENT do DER: medidas biométricas 1:1 da inferência."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inference = models.OneToOneField(
        InferenceRecord,
        on_delete=models.CASCADE,
        related_name="measurement",
    )
    peso_kg = models.FloatField("Peso estimado (kg)", null=True, blank=True)
    altura_cernelha = models.FloatField("Altura da cernelha (cm)", null=True, blank=True)
    altura_garupa = models.FloatField("Altura da garupa (cm)", null=True, blank=True)
    comprimento = models.FloatField("Comprimento corporal (cm)", null=True, blank=True)
    circ_torax = models.FloatField("Circunferência torácica (cm)", null=True, blank=True)
    grossura_pescoco = models.FloatField("Grossura do pescoço (cm)", null=True, blank=True)
    raw_keypoints = models.JSONField("Keypoints brutos (auditoria)", null=True, blank=True)

    class Meta:
        verbose_name = "Medição Biométrica"
        verbose_name_plural = "Medições Biométricas"

    def __str__(self) -> str:
        return f"Medição {self.inference_id} ({self.peso_kg} kg)"
