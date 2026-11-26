from django.core.files.storage import default_storage
from rest_framework import serializers

from inferences.models import BiometricMeasurement, InferenceRecord


class InferenceUploadSerializer(serializers.Serializer):
    """Valida os parâmetros de entrada (multipart/form-data) para inferência por imagem."""

    image = serializers.FileField(required=False)
    file = serializers.FileField(required=False)
    distance_cm = serializers.FloatField(required=False, allow_null=True, min_value=10.0, max_value=1000.0)
    conf_threshold = serializers.FloatField(required=False, default=0.25, min_value=0.01, max_value=1.0)
    imgsz = serializers.IntegerField(required=False, default=1280, min_value=320, max_value=2560)

    def validate_imgsz(self, value: int) -> int:
        if value % 32 != 0:
            raise serializers.ValidationError("O parâmetro 'imgsz' deve ser múltiplo de 32.")
        return value

    def validate(self, attrs):
        uploaded_file = attrs.get("image") or attrs.get("file")
        if uploaded_file is None:
            raise serializers.ValidationError(
                {"file": "Envie uma imagem no campo 'image' ou 'file'."}
            )
        attrs["uploaded_file"] = uploaded_file
        return attrs


class BiometricMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricMeasurement
        fields = (
            "id",
            "peso_kg",
            "altura_cernelha",
            "altura_garupa",
            "comprimento",
            "circ_torax",
            "grossura_pescoco",
            "raw_keypoints",
        )


class InferenceRecordSerializer(serializers.ModelSerializer):
    measurement = BiometricMeasurementSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = InferenceRecord
        fields = (
            "id",
            "farm_id",
            "animal_id",
            "original_filename",
            "image_url",
            "distance_cm",
            "model_tag",
            "conf_threshold",
            "imgsz",
            "created_at",
            "measurement",
        )

    def get_image_url(self, obj: InferenceRecord) -> str:
        url = default_storage.url(obj.image_path) if obj.image_path else obj.image_url
        request = self.context.get("request")
        if request is not None and url and not url.startswith(("http://", "https://")):
            return request.build_absolute_uri(url)
        return url
