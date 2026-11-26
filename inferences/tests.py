import tempfile
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from farms.models import Farm
from inferences.models import BiometricMeasurement, InferenceRecord


def _make_dummy_jpeg(name: str = "010-dist160-v3.jpg") -> SimpleUploadedFile:
    img = np.zeros((120, 160, 3), dtype=np.uint8)
    img[:, :] = (40, 120, 80)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return SimpleUploadedFile(name, buf.tobytes(), content_type="image/jpeg")


def _fake_inference_result(**kwargs):
    img = np.full((120, 160, 3), 200, dtype=np.uint8)
    dist = kwargs.get("dist_cm") or 160.0
    return {
        "estimativas": {
            "peso_estimado_kg": 44.25,
            "altura_cernelha_cm": 74.1,
            "altura_garupa_cm": 75.3,
            "comprimento_cm": 71.8,
            "circ_torax_cm": 94.48,
            "grossura_pescoco_cm": 19.6,
        },
        "raw_keypoints": [{"index": 0, "name": "left_eye", "x": 10.0, "y": 20.0, "conf": 0.99}],
        "bbox": [10.0, 10.0, 140.0, 110.0],
        "box_conf": 0.91,
        "img_anotada": img,
        "dados_validacao": None,
        "tag_modelo": "strict-clean",
        "nome_run_modelo": "caprine-bovidae-v4-strict-clean",
        "model_path": "runs/pose/ovision-yolo/caprine-bovidae-v4-strict-clean/weights/best.pt",
        "distancia_cm": float(dist),
        "conf_thresh": 0.25,
        "imgsz": 1280,
    }


class InferenceApiTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.override.enable()
        self.addCleanup(self._cleanup_media)

        self.farm_a = Farm.objects.create_user(
            email="farm_a@ovision.local",
            password="password123",
            name="Fazenda Alfa",
            owner_name="João",
        )
        self.farm_b = Farm.objects.create_user(
            email="farm_b@ovision.local",
            password="password123",
            name="Fazenda Beta",
            owner_name="Ana",
        )
        self.client = APIClient()

    def _cleanup_media(self):
        self.override.disable()
        self.temp_media.cleanup()

    def _auth_as(self, farm: Farm):
        res = self.client.post(
            reverse("token-obtain-pair"),
            {"email": farm.email, "password": "password123"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_requires_authentication(self):
        res_get = self.client.get(reverse("inference-list-create"))
        self.assertEqual(res_get.status_code, status.HTTP_401_UNAUTHORIZED)

        res_post = self.client.post(reverse("inference-list-create"), {}, format="multipart")
        self.assertEqual(res_post.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_and_invalid_image_return_400(self):
        self._auth_as(self.farm_a)

        res_missing = self.client.post(reverse("inference-list-create"), {}, format="multipart")
        self.assertEqual(res_missing.status_code, status.HTTP_400_BAD_REQUEST)

        bad_file = SimpleUploadedFile("bad.jpg", b"not-an-image", content_type="image/jpeg")
        res_bad = self.client.post(
            reverse("inference-list-create"),
            {"file": bad_file},
            format="multipart",
        )
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("inferences.services.inference_service.get_cached_yolo_model", return_value=(object(), "mock.pt"))
    @patch("inferences.services.inference_service.executar_inferencia_imagem", return_value=None)
    def test_no_animal_detected_returns_422(self, _mock_exec, _mock_model):
        self._auth_as(self.farm_a)
        res = self.client.post(
            reverse("inference-list-create"),
            {"image": _make_dummy_jpeg()},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch("inferences.services.inference_service.get_cached_yolo_model", return_value=(object(), "mock.pt"))
    @patch("inferences.services.inference_service.executar_inferencia_imagem")
    def test_upload_supports_image_and_file_fields_and_farm_isolation(self, mock_exec, _mock_model):
        mock_exec.side_effect = lambda **kw: _fake_inference_result(dist_cm=kw.get("dist_cm") or 160.0)

        # Upload via 'image' na Fazenda A (distância explícita)
        self._auth_as(self.farm_a)
        res_a = self.client.post(
            reverse("inference-list-create"),
            {"image": _make_dummy_jpeg("caprino.jpg"), "distance_cm": "185"},
            format="multipart",
        )
        self.assertEqual(res_a.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_a.data["distance_cm"], 185.0)
        self.assertEqual(res_a.data["measurement"]["peso_kg"], 44.25)
        self.assertIn("/media/inferences/", res_a.data["image_url"])

        # Upload via 'file' na Fazenda B
        self._auth_as(self.farm_b)
        res_b = self.client.post(
            reverse("inference-list-create"),
            {"file": _make_dummy_jpeg("007-dist160-v1.jpg")},
            format="multipart",
        )
        self.assertEqual(res_b.status_code, status.HTTP_201_CREATED)

        # Listagem da Fazenda B mostra somente o registro dela
        list_b = self.client.get(reverse("inference-list-create"))
        self.assertEqual(list_b.status_code, status.HTTP_200_OK)
        self.assertEqual(list_b.data["count"], 1)
        self.assertEqual(list_b.data["results"][0]["id"], res_b.data["id"])

        # Fazenda B não pode acessar detalhe da Fazenda A
        detail_forbidden = self.client.get(reverse("inference-detail", args=[res_a.data["id"]]))
        self.assertEqual(detail_forbidden.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(InferenceRecord.objects.count(), 2)
        self.assertEqual(BiometricMeasurement.objects.count(), 2)

    def test_real_yolo_inference_and_media_serving(self):
        sample_path = Path(settings.BASE_DIR) / "inputs" / "010-dist160-v3.jpg"
        if not sample_path.exists():
            self.skipTest("Imagem de exemplo inputs/010-dist160-v3.jpg não encontrada.")

        self._auth_as(self.farm_a)
        with sample_path.open("rb") as f:
            upload = SimpleUploadedFile(sample_path.name, f.read(), content_type="image/jpeg")

        res = self.client.post(
            reverse("inference-list-create"),
            {"image": upload},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data["distance_cm"], 160.0)
        self.assertGreater(res.data["measurement"]["peso_kg"], 0.0)
        self.assertGreater(res.data["measurement"]["altura_cernelha"], 0.0)
        self.assertEqual(len(res.data["measurement"]["raw_keypoints"]), 17)

        record = InferenceRecord.objects.get(pk=res.data["id"])
        saved_file = Path(self.temp_media.name) / record.image_path
        self.assertTrue(saved_file.exists())
        self.assertGreater(saved_file.stat().st_size, 0)
