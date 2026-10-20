from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Mijoz. Telefon + parol bilan yoki Google orqali kiradi."""
    phone = models.CharField("telefon", max_length=16, unique=True, null=True, blank=True)
    name = models.CharField("ism", max_length=80, blank=True)
    legacy_telegram_id = models.BigIntegerField("eski Telegram ID", null=True, blank=True)

    class Meta:
        verbose_name = "mijoz"
        verbose_name_plural = "mijozlar"

    def __str__(self):
        return self.name or self.phone or self.username

    @property
    def profile_complete(self) -> bool:
        return bool(self.phone and self.name)
