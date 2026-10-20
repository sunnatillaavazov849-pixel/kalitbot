from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("name", "phone", "email", "date_joined", "is_staff")
    search_fields = ("name", "phone", "email", "username")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("name", "phone", "email", "username", "password")}),
        ("Eski bot", {"fields": ("legacy_telegram_id",)}),
        ("Huquqlar", {"fields": ("is_active", "is_staff", "is_superuser", "groups"), "classes": ("collapse",)}),
        ("Sanalar", {"fields": ("last_login", "date_joined")}),
    )
