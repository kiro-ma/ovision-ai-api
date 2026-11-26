from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Animal, Farm, Herd


@admin.register(Farm)
class FarmAdmin(UserAdmin):
    model = Farm
    list_display = ("email", "name", "owner_name", "species_focus", "is_staff", "created_at")
    search_fields = ("email", "name", "owner_name")
    ordering = ("-created_at",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados da Fazenda", {"fields": ("name", "owner_name", "species_focus")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "owner_name", "species_focus", "password1", "password2"),
            },
        ),
    )


@admin.register(Herd)
class HerdAdmin(admin.ModelAdmin):
    list_display = ("name", "farm", "species", "created_at")
    search_fields = ("name", "farm__name")


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("code_tag", "herd", "species", "sex", "created_at")
    search_fields = ("code_tag",)
