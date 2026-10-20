from django.contrib import admin, messages
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from . import services as S
from .models import Deactivation, HelpVideo, LegacyCustomer, LegacyTzOrder, License, Order, Plugin


@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = ("name", "prefix", "price_display", "version", "active", "has_file", "licenses_count")
    list_editable = ("active",)
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "prefix", "slug", "tagline", "description", "price", "image", "active", "sort")}),
        ("Fayl", {"fields": ("gms_file", "version", "corel_versions")}),
        ("Maxfiy", {"fields": ("secret",), "classes": ("collapse",),
                    "description": "Bu kalit plagindagi SunatLicense.bas (LIC_SECRET) ga yoziladi. Hech kimga bermang."}),
    )

    def get_readonly_fields(self, request, obj=None):
        return ("prefix", "secret") if obj else ()

    @admin.display(description="narx")
    def price_display(self, obj):
        return obj.price_display

    @admin.display(description="fayl", boolean=True)
    def has_file(self, obj):
        return bool(obj.gms_file)

    @admin.display(description="litsenziyalar")
    def licenses_count(self, obj):
        return obj.licenses.count()


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "user", "user_phone", "plugin", "mid", "amount_display", "status",
                    "receipt_link")
    list_filter = ("status", "plugin")
    search_fields = ("user__name", "user__phone", "mid")
    readonly_fields = ("user", "plugin", "mid", "amount", "receipt_preview", "status", "license", "created_at",
                       "decided_at")
    fields = ("receipt_preview", "user", "plugin", "mid", "amount", "status", "license", "admin_note",
              "created_at", "decided_at")
    actions = ("approve", "reject")
    change_form_template = "admin/shop/order/change_form.html"

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "plugin")

    @admin.display(description="telefon")
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description="summa")
    def amount_display(self, obj):
        return f"{obj.amount:,}".replace(",", " ")

    @admin.display(description="chek")
    def receipt_link(self, obj):
        return format_html('<a href="{}" target="_blank">ko\'rish</a>', reverse("staff_receipt", args=[obj.pk]))

    @admin.display(description="to'lov cheki")
    def receipt_preview(self, obj):
        url = reverse("staff_receipt", args=[obj.pk])
        if obj.receipt.name.lower().endswith(".pdf"):
            return format_html('<a href="{}" target="_blank">PDF chekni ochish</a>', url)
        return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-width:420px;max-height:520px;'
                           'border-radius:8px;border:1px solid #ddd"></a>', url)

    @admin.action(description="Tanlanganlarni TASDIQLASH (litsenziya beriladi)")
    def approve(self, request, queryset):
        done = sum(1 for o in queryset if S.approve_order(o.pk))
        self.message_user(request, f"{done} ta buyurtma tasdiqlandi.", messages.SUCCESS)

    @admin.action(description="Tanlanganlarni RAD ETISH")
    def reject(self, request, queryset):
        done = sum(1 for o in queryset if S.reject_order(o.pk))
        self.message_user(request, f"{done} ta buyurtma rad etildi.", messages.WARNING)

    def response_change(self, request, obj):
        if "_approve" in request.POST:
            if S.approve_order(obj.pk):
                self.message_user(request, f"Buyurtma #{obj.pk} tasdiqlandi, litsenziya berildi.", messages.SUCCESS)
            else:
                self.message_user(request, "Bu buyurtma allaqachon ko'rib chiqilgan.", messages.ERROR)
            return self.response_post_save_change(request, obj)
        if "_reject" in request.POST:
            if S.reject_order(obj.pk, request.POST.get("admin_note", "")):
                self.message_user(request, f"Buyurtma #{obj.pk} rad etildi.", messages.WARNING)
            else:
                self.message_user(request, "Bu buyurtma allaqachon ko'rib chiqilgan.", messages.ERROR)
            return self.response_post_save_change(request, obj)
        return super().response_change(request, obj)


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "legacy_owner", "plugin", "mid", "status", "deact_count", "source", "created_at")
    list_filter = ("status", "plugin", "source")
    search_fields = ("user__name", "user__phone", "mid", "code", "legacy_owner__phone")
    raw_id_fields = ("user", "legacy_owner")
    readonly_fields = ("code", "activated_at", "last_deact_at", "created_at")
    actions = ("block_selected", "unblock_selected")
    inlines = []

    def save_model(self, request, obj, form, change):
        # admin qo'lda kompyuter ID kiritsa - kod avtomatik hisoblanadi
        if obj.mid and obj.status == License.FAOL:
            obj.code = S.activation_code(obj.plugin, obj.mid)
            obj.activated_at = obj.activated_at or timezone.now()
        if obj.status != License.FAOL:
            obj.mid, obj.code = "", ""
        if not change:
            obj.source = obj.source or License.ADMIN
        super().save_model(request, obj, form, change)

    @admin.action(description="Bloklash")
    def block_selected(self, request, queryset):
        n = queryset.update(status=License.BLOKLANGAN)
        self.message_user(request, f"{n} ta litsenziya bloklandi.")

    @admin.action(description="Blokdan chiqarish (ko'chirishlar 0 ga tushadi)")
    def unblock_selected(self, request, queryset):
        n = sum(1 for lic in queryset if S.unblock(lic.pk))
        self.message_user(request, f"{n} ta litsenziya blokdan chiqarildi.")


@admin.register(Deactivation)
class DeactivationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "license", "mid", "reason", "confirmed")
    list_filter = ("confirmed",)

    def has_add_permission(self, request):
        return False


@admin.register(LegacyCustomer)
class LegacyCustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "telegram_id", "claimed_by", "claimed_at")
    search_fields = ("name", "phone")
    raw_id_fields = ("claimed_by",)


@admin.register(LegacyTzOrder)
class LegacyTzOrderAdmin(admin.ModelAdmin):
    list_display = ("machine_code", "name", "phone", "created_at", "license")
    search_fields = ("machine_code", "name", "phone")


@admin.register(HelpVideo)
class HelpVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "youtube_url", "sort")
    list_editable = ("sort",)
