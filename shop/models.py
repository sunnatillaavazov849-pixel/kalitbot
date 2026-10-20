import secrets

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import RegexValidator
from django.db import models
from django.utils.functional import LazyObject


class PrivateStorage(LazyObject):
    """Yopiq fayllar (cheklar, .gms): MEDIA dan tashqarida, faqat sayt orqali ruxsat bilan beriladi."""

    def _setup(self):
        self._wrapped = FileSystemStorage(location=settings.PRIVATE_ROOT, base_url=None)


private_storage = PrivateStorage()

SECRET_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789abcdefghjkmnpqrstuvwxyz"


def new_secret() -> str:
    return "".join(secrets.choice(SECRET_ALPHABET) for _ in range(32))


def format_som(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " so'm"


class Plugin(models.Model):
    prefix = models.CharField("belgi", max_length=4, unique=True,
                              validators=[RegexValidator(r"^[A-Z]{2,4}$", "2-4 ta katta lotin harfi, masalan TT")],
                              help_text="So'rov ID va kodlar boshida turadi (TT, MB...). Keyin o'zgartirib bo'lmaydi.")
    name = models.CharField("nomi", max_length=80)
    slug = models.SlugField("manzil", unique=True, help_text="Sayt manzili: /plagin/<manzil>/")
    tagline = models.CharField("qisqa tavsif", max_length=160, blank=True)
    description = models.TextField("to'liq tavsif", blank=True)
    price = models.PositiveIntegerField("narx (so'm)")
    image = models.ImageField("rasm", upload_to="plugins/", blank=True)
    gms_file = models.FileField("plagin fayli (.gms)", storage=private_storage, upload_to="gms/", blank=True)
    version = models.CharField("versiya", max_length=20, blank=True)
    corel_versions = models.CharField("CorelDRAW versiyalari", max_length=80, default="2020 – 2026")
    secret = models.CharField("maxfiy kalit", max_length=64, blank=True,
                              help_text="Bo'sh qoldirilsa avtomatik yaratiladi. Plagindagi SunatLicense.bas ga yoziladi.")
    active = models.BooleanField("sotuvda", default=True)
    sort = models.PositiveIntegerField("tartib", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "plagin"
        verbose_name_plural = "plaginlar"
        ordering = ["sort", "id"]

    def __str__(self):
        return f"{self.name} ({self.prefix})"

    def save(self, *args, **kwargs):
        self.prefix = self.prefix.upper()
        if not self.secret:
            self.secret = new_secret()
        super().save(*args, **kwargs)

    @property
    def price_display(self) -> str:
        return format_som(self.price)


class Order(models.Model):
    KUTILMOQDA, TASDIQLANDI, RAD_ETILDI = "kutilmoqda", "tasdiqlandi", "rad_etildi"
    STATUSES = [(KUTILMOQDA, "Tekshirilmoqda"), (TASDIQLANDI, "Tasdiqlandi"), (RAD_ETILDI, "Rad etildi")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="mijoz", on_delete=models.PROTECT,
                             related_name="orders")
    plugin = models.ForeignKey(Plugin, verbose_name="plagin", on_delete=models.PROTECT)
    mid = models.CharField("kompyuter ID", max_length=9)
    amount = models.PositiveIntegerField("summa (so'm)")
    receipt = models.FileField("to'lov cheki", storage=private_storage, upload_to="receipts/")
    status = models.CharField("holat", max_length=12, choices=STATUSES, default=KUTILMOQDA)
    license = models.ForeignKey("License", verbose_name="litsenziya", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="+")
    admin_note = models.CharField("admin izohi", max_length=200, blank=True,
                                  help_text="Rad etilsa mijozga ko'rsatiladi")
    created_at = models.DateTimeField("sana", auto_now_add=True)
    decided_at = models.DateTimeField("ko'rib chiqilgan", null=True, blank=True)

    class Meta:
        verbose_name = "buyurtma"
        verbose_name_plural = "buyurtmalar"
        ordering = ["-id"]

    def __str__(self):
        return f"#{self.pk} {self.plugin.prefix}-{self.mid}"


class LegacyCustomer(models.Model):
    """Eski Telegram bot mijozi. Saytda shu telefon bilan ro'yxatdan o'tsa, litsenziyalari unga o'tadi."""
    telegram_id = models.BigIntegerField("Telegram ID", unique=True)
    name = models.CharField("ism", max_length=80)
    phone = models.CharField("telefon", max_length=16, db_index=True)
    claimed_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="saytdagi akkaunt", null=True,
                                   blank=True, on_delete=models.SET_NULL, related_name="+")
    claimed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "eski mijoz (bot)"
        verbose_name_plural = "eski mijozlar (bot)"

    def __str__(self):
        return f"{self.name} {self.phone}"


class License(models.Model):
    FAOL, BOSH, BLOKLANGAN = "faol", "bosh", "bloklangan"
    STATUSES = [(FAOL, "Faol"), (BOSH, "Bo'sh (yangi kompyuterga beriladi)"), (BLOKLANGAN, "Bloklangan")]
    XARID, ESKI, ADMIN = "xarid", "eski", "admin"
    SOURCES = [(XARID, "Xarid"), (ESKI, "Eski tizimdan"), (ADMIN, "Admin bergan")]
    MAX_DEACT = 3

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="mijoz", null=True, blank=True,
                             on_delete=models.PROTECT, related_name="licenses")
    legacy_owner = models.ForeignKey(LegacyCustomer, verbose_name="eski mijoz", null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="licenses")
    plugin = models.ForeignKey(Plugin, verbose_name="plagin", on_delete=models.PROTECT, related_name="licenses")
    mid = models.CharField("kompyuter ID", max_length=9, blank=True)
    code = models.CharField("faollashtirish kodi", max_length=24, blank=True)
    status = models.CharField("holat", max_length=12, choices=STATUSES, default=BOSH)
    source = models.CharField("manba", max_length=8, choices=SOURCES, default=XARID)
    deact_count = models.PositiveSmallIntegerField("ko'chirishlar", default=0)
    last_deact_at = models.DateTimeField("oxirgi ko'chirish", null=True, blank=True)
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    activated_at = models.DateTimeField("faollashtirilgan", null=True, blank=True)

    class Meta:
        verbose_name = "litsenziya"
        verbose_name_plural = "litsenziyalar"
        ordering = ["-id"]

    def __str__(self):
        return f"#{self.pk} {self.plugin.prefix} {self.mid or '-'}"

    @property
    def transfers_left(self) -> int:
        return max(self.MAX_DEACT - self.deact_count, 0)


class Deactivation(models.Model):
    license = models.ForeignKey(License, verbose_name="litsenziya", on_delete=models.CASCADE,
                                related_name="deactivations")
    mid = models.CharField("eski kompyuter ID", max_length=9)
    reason = models.CharField("sabab", max_length=500)
    confirmed = models.BooleanField("tasdiq kodi bilan", default=False)
    created_at = models.DateTimeField("sana", auto_now_add=True)

    class Meta:
        verbose_name = "kompyuter almashtirish"
        verbose_name_plural = "kompyuter almashtirishlar"
        ordering = ["-id"]


class LegacyTzOrder(models.Model):
    """Eski TZ- parol tizimidagi tasdiqlangan xarid. Kabinetda eski kompyuter kodi bilan o'tkaziladi."""
    machine_code = models.CharField("eski kompyuter kodi", max_length=9, db_index=True)
    name = models.CharField("ism", max_length=80)
    phone = models.CharField("telefon", max_length=32)
    telegram_id = models.BigIntegerField("Telegram ID", null=True, blank=True)
    password = models.CharField("TZ- parol", max_length=24, blank=True)
    created_at = models.CharField("sana", max_length=20, blank=True)
    license = models.OneToOneField(License, null=True, blank=True, on_delete=models.SET_NULL,
                                   verbose_name="o'tkazilgan litsenziya")

    class Meta:
        verbose_name = "eski TZ- xarid"
        verbose_name_plural = "eski TZ- xaridlar"


class HelpVideo(models.Model):
    title = models.CharField("sarlavha", max_length=120)
    youtube_url = models.URLField("YouTube havola", blank=True)
    file = models.FileField("video fayl", upload_to="videos/", blank=True)
    sort = models.PositiveIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "yordam videosi"
        verbose_name_plural = "yordam videolari"
        ordering = ["sort", "id"]

    def __str__(self):
        return self.title

    @property
    def youtube_embed(self) -> str:
        import re
        m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})", self.youtube_url or "")
        return f"https://www.youtube-nocookie.com/embed/{m.group(1)}" if m else ""
