from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from . import services as S
from .downloads import build_plugin_zip
from .forms import ReceiptForm, RequestCodeForm, TransferForm, TzClaimForm
from .models import HelpVideo, License, Order, Plugin

FAQ = [
    ("Plagin nechta kompyuterda ishlaydi?",
     "Bitta litsenziya — bitta kompyuter. Kod shu kompyuterning o'zgarmas belgisiga bog'lanadi."),
    ("Windows'ni qayta o'rnatsam nima bo'ladi?",
     "Kompyuter ID ona plataga bog'langan, Windows qayta o'rnatilganda odatda o'zgarmaydi. "
     "O'zgarsa — kabinetda «Kompyuterni almashtirish» (kuniga 1, jami 3 marta)."),
    ("Yangi kompyuter oldim, yana to'laymanmi?",
     "Yo'q. Kabinetda «Kompyuterni almashtirish» qilasiz va yangi kompyuterning so'rov kodini kiritasiz — "
     "kod to'lovsiz beriladi."),
    ("Qaysi CorelDRAW versiyalarida ishlaydi?",
     "Windows uchun CorelDRAW 2020 – 2026 (VBA o'rnatilgan bo'lishi kerak)."),
    ("To'lov qanday qilinadi?",
     "Kartaga o'tkazasiz va chek rasmini yuklaysiz. Admin tekshirgach kod kabinetingizda paydo bo'ladi."),
]


def home(request):
    return render(request, "shop/home.html", {
        "plugins": Plugin.objects.filter(active=True),
        "faq": FAQ,
    })


def plugin_detail(request, slug):
    plugin = get_object_or_404(Plugin, slug=slug, active=True)
    return render(request, "shop/plugin.html", {"plugin": plugin})


def app_page(request):
    return render(request, "shop/app.html")


def help_page(request):
    return render(request, "shop/help.html", {"videos": HelpVideo.objects.all(), "faq": FAQ})


@require_GET
def api_plugins(request):
    base = settings.SITE_URL
    data = [{
        "prefix": p.prefix,
        "name": p.name,
        "slug": p.slug,
        "tagline": p.tagline,
        "version": p.version,
        "price": p.price,
        "price_display": p.price_display,
        "corel_versions": p.corel_versions,
        "image": base + p.image.url if p.image else "",
        "url": base + reverse("plugin", args=[p.slug]),
        "buy_url": base + reverse("buy", args=[p.slug]),
    } for p in Plugin.objects.filter(active=True)]
    resp = JsonResponse({"site": base, "plugins": data}, json_dumps_params={"ensure_ascii": False})
    resp["Cache-Control"] = "public, max-age=300"
    return resp


def _need_profile(request):
    if not request.user.profile_complete:
        messages.info(request, "Davom etishdan oldin ismingiz va telefon raqamingizni kiriting.")
        return redirect(f"{reverse('profil')}?next={request.get_full_path()}")
    return None


@login_required
def buy(request, slug):
    plugin = get_object_or_404(Plugin, slug=slug, active=True)
    if (r := _need_profile(request)):
        return r
    key = f"buy:{plugin.pk}"
    step = request.POST.get("step")

    if request.method == "POST" and step == "pay":
        mid = request.session.get(key)
        if not mid:
            messages.error(request, "Avval so'rov kodini kiriting.")
            return redirect("buy", slug=slug)
        form = ReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            res = S.request_activation(request.user, plugin, mid)
            if res.kind in (S.CODE, S.BOUND, S.PENDING):
                # oraliqda holat o'zgargan (masalan bo'sh litsenziya bor) - to'lov kerak emas
                return render(request, "shop/buy_result.html", {"plugin": plugin, "res": res, "mid": mid})
            order = S.create_order(request.user, plugin, mid, form.cleaned_data["receipt"])
            request.session.pop(key, None)
            return redirect("order", pk=order.pk)
        return render(request, "shop/buy_result.html", {
            "plugin": plugin, "mid": mid, "res": S.ActivationResult(S.NEED_PAYMENT), "pay_form": form})

    form = RequestCodeForm(request.POST if step == "code" else None,
                           initial={"code": request.GET.get("kod", "")})
    if step == "code" and form.is_valid():
        mid, err = S.parse_request(form.cleaned_data["code"], plugin)
        if err:
            form.add_error("code", err)
        else:
            res = S.request_activation(request.user, plugin, mid)
            if res.kind in (S.NEED_PAYMENT, S.BLOCKED, S.ACTIVE_ELSEWHERE):
                request.session[key] = mid
            return render(request, "shop/buy_result.html", {
                "plugin": plugin, "res": res, "mid": mid, "pay_form": ReceiptForm()})
    return render(request, "shop/buy.html", {"plugin": plugin, "form": form})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("plugin", "license"), pk=pk, user=request.user)
    return render(request, "shop/order.html", {"order": order})


@login_required
def cabinet(request):
    if (r := _need_profile(request)):
        return r
    return render(request, "shop/cabinet.html", {
        "licenses": request.user.licenses.select_related("plugin").order_by("plugin__sort", "id"),
        "orders": request.user.orders.select_related("plugin").exclude(status=Order.TASDIQLANDI)[:10],
    })


@login_required
def transfer(request, pk):
    lic = get_object_or_404(License.objects.select_related("plugin"), pk=pk, user=request.user)
    problem = S.deact_check(lic)
    if problem == "limit":
        S.block(lic)
        S.notify_admins(f"Litsenziya #{lic.pk} bloklandi (ko'chirish limiti)", f"{request.user} - {lic.plugin.name}")
        lic.refresh_from_db()
    if problem:
        return render(request, "shop/transfer.html", {"lic": lic, "problem": problem})

    form = TransferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        no_code = form.cleaned_data["no_code"]
        if not no_code and not S.confirm_matches(lic, form.cleaned_data["confirm"]):
            form.add_error("confirm", "Tasdiq kodi noto'g'ri. Eski kompyuterdagi kodni aynan ko'chirib yozing.")
        else:
            done = S.deactivate(lic.pk, form.cleaned_data["reason"], confirmed=not no_code)
            if done is None:
                messages.error(request, "Almashtirib bo'lmadi: holat o'zgargan yoki bugungi limit tugagan.")
                return redirect("kabinet")
            messages.success(request, f"{lic.plugin.name} eski kompyuterdan bo'shatildi. Endi yangi kompyuterning "
                                      f"so'rov kodini kiriting — kod to'lovsiz beriladi.")
            return redirect("buy", slug=lic.plugin.slug)
    return render(request, "shop/transfer.html", {"lic": lic, "form": form})


@login_required
def legacy_tz(request):
    form = TzClaimForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        lic, err = S.claim_tz(request.user, form.cleaned_data["code"])
        if err:
            form.add_error("code", err)
        else:
            messages.success(request, "Eski litsenziyangiz o'tkazildi. Endi Tez-Tez'ning so'rov kodini kiriting — "
                                      "kod to'lovsiz beriladi.")
            return redirect("buy", slug=lic.plugin.slug)
    return render(request, "shop/legacy.html", {"form": form})


@login_required
def download(request, pk):
    lic = get_object_or_404(License.objects.select_related("plugin"), pk=pk, user=request.user)
    if lic.status == License.BLOKLANGAN or not lic.plugin.gms_file:
        raise Http404("Fayl mavjud emas")
    data, name = build_plugin_zip(lic.plugin)
    resp = HttpResponse(data, content_type="application/zip")
    resp["Content-Disposition"] = f'attachment; filename="{name}"'
    return resp


@staff_member_required
def staff_receipt(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return FileResponse(order.receipt.open("rb"), filename=order.receipt.name.rsplit("/", 1)[-1])
