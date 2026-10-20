from django.contrib.auth.backends import ModelBackend

from .models import User
from .phone import normalize_phone


class PhoneBackend(ModelBackend):
    """Telefon raqami + parol bilan kirish."""

    def authenticate(self, request, phone=None, password=None, **kwargs):
        phone = normalize_phone(phone or "")
        if not phone or not password:
            return None
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            User().set_password(password)  # vaqt bo'yicha farqni yashirish
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
