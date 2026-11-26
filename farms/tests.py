from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from farms.models import Farm


class FarmAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_login_refresh_and_profile(self):
        register_payload = {
            "name": "Fazenda Capril Sul",
            "owner_name": "Maria Silva",
            "email": "maria@capril.local",
            "password": "segredo123",
            "species_focus": "caprinos",
        }
        res_reg = self.client.post(reverse("farm-register"), register_payload, format="json")
        self.assertEqual(res_reg.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", res_reg.data)
        self.assertIn("refresh", res_reg.data)
        self.assertEqual(res_reg.data["farm"]["email"], "maria@capril.local")

        res_tok = self.client.post(
            reverse("token-obtain-pair"),
            {"email": "maria@capril.local", "password": "segredo123"},
            format="json",
        )
        self.assertEqual(res_tok.status_code, status.HTTP_200_OK)
        access = res_tok.data["access"]
        refresh = res_tok.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        res_me = self.client.get(reverse("farm-profile"))
        self.assertEqual(res_me.status_code, status.HTTP_200_OK)
        self.assertEqual(res_me.data["name"], "Fazenda Capril Sul")

        res_ref = self.client.post(reverse("token-refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(res_ref.status_code, status.HTTP_200_OK)
        self.assertIn("access", res_ref.data)

    def test_seed_farm_command_is_idempotent(self):
        out1 = StringIO()
        call_command("seed_farm", stdout=out1)
        self.assertEqual(Farm.objects.filter(email="demo@ovision.local").count(), 1)

        out2 = StringIO()
        call_command("seed_farm", stdout=out2)
        self.assertEqual(Farm.objects.filter(email="demo@ovision.local").count(), 1)
        farm = Farm.objects.get(email="demo@ovision.local")
        self.assertTrue(farm.check_password("ovision123"))
