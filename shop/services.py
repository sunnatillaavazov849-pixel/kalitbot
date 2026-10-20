"""Biznes mantiq: so'rov kodi -> to'lov -> litsenziya, kompyuter almashtirish, eski mijozlar.

Telegram botdagi (handlers/activation.py, transfer.py, db.py) tekshirilgan mantiq shu yerga ko'chirilgan.
"""
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from . import licensing as L
from .models import Deactivation, LegacyCustomer, LegacyTzOrder, License, Order, Plugin

# request_activation natijalari
CODE = "code"                       # shu kompyuterda faol - kod qayta ko'rsatiladi
BOUND = "bound"                     # bo'sh litsenziya shu kompyuterga to'lovsiz bog'landi
PENDING = "pending"                 # shu so'rov bo'yicha to'lov tekshirilmoqda
ACTIVE_ELSEWHERE = "elsewhere"      # boshqa kompyuterda faol - almashtirish yoki yangi xarid
BLOCKED = "blocked"                 # litsenziya bloklangan - yangi xarid mumkin
NEED_PAYMENT = "payment"            # to'lov kerak


@dataclass
class ActivationResult:
    kind: str
    license: License | None = None
    order: Order | None = None


def parse_request(text: str, plugin: Plugin) -> tuple[str | None, str | None]:
    """So'rov kodini tekshiradi. (mid, xato) qaytaradi."""
    parsed = L.parse_request_id(text, Plugin.objects.values_list("prefix", flat=True))
    if parsed is None:
        return None, "So'rov kodi noto'g'ri. U plagin belgisi va 8 ta belgidan iborat, masalan TT-K7QM-3XPA."
    prefix, mid = parsed
    if prefix != plugin.prefix:
        return None, f"Bu kod boshqa plagin ({prefix}) uchun. {plugin.name} kodi {plugin.prefix}- bilan boshlanadi."
    return mid, None


def activation_code(plugin: Plugin, mid: str) -> str:
    return L.activation_code(plugin.prefix, mid, plugin.secret)


@transaction.atomic
def request_activation(user, plugin: Plugin, mid: str) -> ActivationResult:
    lics = License.objects.select_for_update().filter(user=user, plugin=plugin)
    same = lics.filter(status=License.FAOL, mid=mid).first()
    if same:
        return ActivationResult(CODE, license=same)

    free = lics.filter(status=License.BOSH).order_by("id").first()
    if free:
        free.mid, free.code, free.status = mid, activation_code(plugin, mid), License.FAOL
        free.activated_at = timezone.now()
        free.save()
        return ActivationResult(BOUND, license=free)

    pending = Order.objects.filter(user=user, plugin=plugin, mid=mid, status=Order.KUTILMOQDA).first()
    if pending:
        return ActivationResult(PENDING, order=pending)

    other = lics.filter(status=License.FAOL).first()
    if other:
        return ActivationResult(ACTIVE_ELSEWHERE, license=other)
    if lics.filter(status=License.BLOKLANGAN).exists():
        return ActivationResult(BLOCKED)
    return ActivationResult(NEED_PAYMENT)


def create_order(user, plugin: Plugin, mid: str, receipt) -> Order:
    order = Order.objects.create(user=user, plugin=plugin, mid=mid, amount=plugin.price, receipt=receipt)
    notify_admins(
        f"Yangi to'lov #{order.pk}: {plugin.name}",
        f"{user} ({user.phone}) {plugin.name} uchun {plugin.price_display} to'ladi.\n"
        f"Kompyuter ID: {mid}\nTekshirish: {settings.SITE_URL}/boshqaruv/shop/order/{order.pk}/change/",
    )
    return order


@transaction.atomic
def approve_order(order_id: int) -> Order | None:
    """Tasdiqlaydi va litsenziya yaratadi. Allaqachon ko'rib chiqilgan bo'lsa None."""
    order = Order.objects.select_for_update().select_related("plugin").get(pk=order_id)
    if order.status != Order.KUTILMOQDA:
        return None
    lic = License.objects.create(
        user_id=order.user_id, plugin=order.plugin, mid=order.mid,
        code=activation_code(order.plugin, order.mid), status=License.FAOL, source=License.XARID,
        activated_at=timezone.now(),
    )
    order.status, order.license, order.decided_at = Order.TASDIQLANDI, lic, timezone.now()
    order.save()
    return order


@transaction.atomic
def reject_order(order_id: int, note: str = "") -> Order | None:
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status != Order.KUTILMOQDA:
        return None
    order.status, order.decided_at = Order.RAD_ETILDI, timezone.now()
    if note:
        order.admin_note = note[:200]
    order.save()
    return order


# ------------------------------------------------------------------ kompyuter almashtirish

def deact_check(lic: License) -> str | None:
    """Almashtirish mumkinmi. Mumkin bo'lsa None, aks holda: 'holat', 'bugun' (kuniga 1), 'limit' (3 tadan oshdi)."""
    if lic.status != License.FAOL:
        return "holat"
    if lic.last_deact_at and timezone.localdate(lic.last_deact_at) == timezone.localdate():
        return "bugun"
    if lic.deact_count >= License.MAX_DEACT:
        return "limit"
    return None


def confirm_matches(lic: License, text: str) -> bool:
    code = L.normalize_machine_code(text)
    return code is not None and code == L.deact_confirm(lic.code, lic.mid)


@transaction.atomic
def deactivate(license_id: int, reason: str, confirmed: bool) -> License | None:
    lic = License.objects.select_for_update().get(pk=license_id)
    if deact_check(lic) is not None:
        return None
    Deactivation.objects.create(license=lic, mid=lic.mid, reason=reason[:500], confirmed=confirmed)
    old_mid = lic.mid
    lic.mid, lic.code, lic.status = "", "", License.BOSH
    lic.deact_count += 1
    lic.last_deact_at = timezone.now()
    lic.save()
    notify_admins(
        f"Kompyuter almashtirildi: litsenziya #{lic.pk}",
        f"{lic.user} - {lic.plugin.name}, eski kompyuter {old_mid} ({lic.deact_count}/{License.MAX_DEACT}).\n"
        f"Sabab: {reason}\n{'Tasdiq kodi bilan' if confirmed else 'Tasdiq kodisiz (kompyuter ishlamaydi deb)'}",
    )
    return lic


def block(lic: License):
    License.objects.filter(pk=lic.pk).update(status=License.BLOKLANGAN)


def unblock(license_id: int) -> bool:
    return License.objects.filter(pk=license_id, status=License.BLOKLANGAN).update(
        status=License.BOSH, mid="", code="", deact_count=0) == 1


# ------------------------------------------------------------------ eski mijozlar

@transaction.atomic
def claim_legacy(user) -> int:
    """Telefon raqami mos keladigan eski bot mijozining litsenziyalarini userga o'tkazadi. Nechtasini qaytaradi."""
    if not user.phone:
        return 0
    moved = 0
    for lc in LegacyCustomer.objects.select_for_update().filter(phone=user.phone, claimed_by__isnull=True):
        moved += License.objects.filter(legacy_owner=lc, user__isnull=True).update(user=user, legacy_owner=None)
        lc.claimed_by, lc.claimed_at = user, timezone.now()
        lc.save()
        if user.legacy_telegram_id is None:
            user.legacy_telegram_id = lc.telegram_id
            user.save(update_fields=["legacy_telegram_id"])
    return moved


@transaction.atomic
def claim_tz(user, text: str) -> tuple[License | None, str]:
    """Eski TZ- parol bilan sotib olingan Tez-Tez'ni yangi tizimga o'tkazadi."""
    mc = L.normalize_machine_code(text)
    if mc is None:
        return None, "Kod noto'g'ri. U 8 ta belgidan iborat, masalan K7QM-3XPA."
    tz = LegacyTzOrder.objects.select_for_update().filter(machine_code=mc).order_by("-id").first()
    if tz is None:
        return None, "Bu kod bo'yicha eski xarid topilmadi. Admin bilan bog'laning."
    if tz.license_id:
        return None, "Bu xarid allaqachon yangi tizimga o'tkazilgan."
    plugin = Plugin.objects.filter(prefix="TT").first()
    if plugin is None:
        return None, "Tez-Tez plagini saytda hali yo'q. Admin bilan bog'laning."
    lic = License.objects.create(user=user, plugin=plugin, status=License.BOSH, source=License.ESKI)
    tz.license = lic
    tz.save()
    notify_admins(f"Eski TZ- litsenziya o'tkazildi: #{lic.pk}",
                  f"{user} ({user.phone}) eski kod {mc} (eski mijoz: {tz.name}, {tz.phone}).")
    return lic, ""


# ------------------------------------------------------------------ xabarnoma

def notify_admins(subject: str, body: str):
    if not settings.ADMIN_EMAILS:
        return
    try:
        send_mail("[Sunat.cc] " + subject, body, settings.DEFAULT_FROM_EMAIL, settings.ADMIN_EMAILS,
                  fail_silently=True)
    except Exception:
        pass
