from django.conf import settings


def site(request):
    pending = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_staff and request.path.startswith("/boshqaruv"):
        from .models import Order
        pending = Order.objects.filter(status=Order.KUTILMOQDA).count()
    return {
        "PENDING_ORDERS": pending,
        "SITE_URL": settings.SITE_URL,
        "CARD_NUMBER": settings.CARD_NUMBER,
        "CARD_OWNER": settings.CARD_OWNER,
        "APP_PORTABLE_URL": settings.APP_PORTABLE_URL,
        "APP_SETUP_URL": settings.APP_SETUP_URL,
        "CONTACT_TELEGRAM": settings.CONTACT_TELEGRAM,
        "CONTACT_INSTAGRAM": settings.CONTACT_INSTAGRAM,
        "CONTACT_PHONE": settings.CONTACT_PHONE,
        "GOOGLE_LOGIN": bool(settings.GOOGLE_CLIENT_ID),
    }
