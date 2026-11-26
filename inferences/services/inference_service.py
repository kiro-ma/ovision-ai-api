import re
import threading
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from ultralytics import YOLO

from inferences.models import BiometricMeasurement, InferenceRecord
from inferences.services.pipeline import (
    DEFAULT_MODEL_PATH,
    executar_inferencia_imagem,
    resolver_modelo_padrao,
)

_MODEL_CACHE: dict[str, YOLO] = {}
_MODEL_LOCK = threading.Lock()


class InvalidImageError(Exception):
    """Erro levantado quando o arquivo enviado não é uma imagem válida."""


class NoAnimalDetectedError(Exception):
    """Erro levantado quando o modelo não detecta um animal válido na imagem."""


def get_cached_yolo_model(model_path: Optional[str] = None) -> tuple[YOLO, str]:
    """Carrega e mantém o modelo YOLO Pose em cache por processo de forma thread-safe."""
    preferred = model_path or getattr(settings, "OVISION_MODEL_PATH", DEFAULT_MODEL_PATH)
    resolved_path = resolver_modelo_padrao(preferred, base_dir=settings.BASE_DIR)

    with _MODEL_LOCK:
        model = _MODEL_CACHE.get(resolved_path)
        if model is None:
            model = YOLO(resolved_path)
            _MODEL_CACHE[resolved_path] = model

    return model, resolved_path


def _sanitize_stem(filename: str) -> str:
    stem = Path(filename or "image").stem
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    return cleaned[:80] or "image"


def _round_optional(value: Optional[float], digits: int = 2) -> Optional[float]:
    return round(float(value), digits) if value is not None else None


def run_inference_for_farm(
    farm,
    uploaded_file,
    distance_cm: Optional[float] = None,
    conf_threshold: float = 0.25,
    imgsz: int = 1280,
    model_path: Optional[str] = None,
) -> InferenceRecord:
    """
    Executa inferência YOLO Pose em uma imagem enviada por upload, salva a imagem anotada
    no storage configurado (MEDIA_ROOT/MEDIA_URL) e persiste InferenceRecord + BiometricMeasurement.
    """
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    if not raw_bytes:
        raise InvalidImageError("O arquivo de imagem enviado está vazio.")

    np_buffer = np.frombuffer(raw_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise InvalidImageError("Não foi possível decodificar o arquivo como uma imagem válida.")

    original_filename = getattr(uploaded_file, "name", None) or "upload.jpg"
    model, resolved_model_path = get_cached_yolo_model(model_path=model_path)

    result = executar_inferencia_imagem(
        img_bgr=img_bgr,
        original_filename=original_filename,
        model_path=resolved_model_path,
        dist_cm=distance_cm,
        conf_thresh=conf_threshold,
        imgsz=imgsz,
        model=model,
        render_image=True,
        verbose=False,
        base_dir=settings.BASE_DIR,
    )
    if result is None:
        raise NoAnimalDetectedError(
            "Nenhum animal com keypoints suficientes foi detectado na imagem enviada."
        )

    img_anotada = result.get("img_anotada")
    success, encoded = cv2.imencode(".jpg", img_anotada, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not success:
        raise InvalidImageError("Falha ao codificar a imagem anotada gerada.")

    safe_stem = _sanitize_stem(original_filename)
    tag_modelo = result["tag_modelo"]
    rel_path = f"inferences/{farm.id}/pose_{safe_stem}_{tag_modelo}_{uuid.uuid4().hex[:8]}.jpg"
    saved_path = default_storage.save(rel_path, ContentFile(encoded.tobytes()))
    storage_url = default_storage.url(saved_path)

    estimativas = result["estimativas"] or {}

    with transaction.atomic():
        record = InferenceRecord.objects.create(
            farm=farm,
            animal=None,
            original_filename=original_filename,
            image_url=storage_url,
            image_path=saved_path,
            distance_cm=float(result["distancia_cm"]),
            model_tag=f"{result['nome_run_modelo']} ({tag_modelo})",
            conf_threshold=float(conf_threshold),
            imgsz=int(imgsz),
        )
        BiometricMeasurement.objects.create(
            inference=record,
            peso_kg=_round_optional(estimativas.get("peso_estimado_kg")),
            altura_cernelha=_round_optional(estimativas.get("altura_cernelha_cm")),
            altura_garupa=_round_optional(estimativas.get("altura_garupa_cm")),
            comprimento=_round_optional(estimativas.get("comprimento_cm")),
            circ_torax=_round_optional(estimativas.get("circ_torax_cm")),
            grossura_pescoco=_round_optional(estimativas.get("grossura_pescoco_cm")),
            raw_keypoints=result.get("raw_keypoints"),
        )

    return InferenceRecord.objects.select_related("measurement").get(pk=record.pk)
