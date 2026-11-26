from django.contrib import admin

from .models import BiometricMeasurement, InferenceRecord


@admin.register(InferenceRecord)
class InferenceRecordAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "farm", "distance_cm", "model_tag", "created_at")
    list_filter = ("model_tag", "created_at")
    search_fields = ("original_filename", "farm__name", "farm__email")


@admin.register(BiometricMeasurement)
class BiometricMeasurementAdmin(admin.ModelAdmin):
    list_display = ("inference", "peso_kg", "altura_cernelha", "altura_garupa", "comprimento")
