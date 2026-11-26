from rest_framework import permissions, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from inferences.models import InferenceRecord
from inferences.serializers import InferenceRecordSerializer, InferenceUploadSerializer
from inferences.services.inference_service import (
    InvalidImageError,
    NoAnimalDetectedError,
    run_inference_for_farm,
)


class InferenceListCreateView(APIView):
    """
    GET /api/v1/inferences/: lista as inferências da fazenda autenticada.
    POST /api/v1/inferences/: recebe upload de imagem, executa YOLO Pose e retorna medidas + URL.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        queryset = InferenceRecord.objects.filter(farm=request.user).select_related("measurement")
        serializer = InferenceRecordSerializer(queryset, many=True, context={"request": request})
        return Response(
            {
                "count": len(serializer.data),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        upload_serializer = InferenceUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)
        validated = upload_serializer.validated_data

        try:
            record = run_inference_for_farm(
                farm=request.user,
                uploaded_file=validated["uploaded_file"],
                distance_cm=validated.get("distance_cm"),
                conf_threshold=validated.get("conf_threshold", 0.25),
                imgsz=validated.get("imgsz", 1280),
            )
        except InvalidImageError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except NoAnimalDetectedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        output = InferenceRecordSerializer(record, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class InferenceDetailView(RetrieveAPIView):
    """GET /api/v1/inferences/<uuid:pk>/: detalha uma inferência da fazenda autenticada."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InferenceRecordSerializer

    def get_queryset(self):
        return InferenceRecord.objects.filter(farm=self.request.user).select_related("measurement")
