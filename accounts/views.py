from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from django.contrib.auth import authenticate
from shop.services import claim_legacy

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User

MAX_ATTEMPTS, WINDOW = 10, 15 * 60


def _next(request, default="kabinet"):
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}, request.is_secure()):
        return nxt
    return default


def _after_login(request, user):
    moved = claim_legacy(user)
    if moved:
        messages.success(request, f"Eski xaridlaringiz ({moved} ta litsenziya) akkauntingizga ulandi.")


def register(request):
    if request.user.is_authenticated:
        return redirect("kabinet")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        user = User.objects.create_user(username=d["phone"].lstrip("+"), password=d["password"],
                                        phone=d["phone"], name=d["name"].strip())
        login(request, user, backend="accounts.backends.PhoneBackend")
        messages.success(request, "Ro'yxatdan o'tdingiz. Xush kelibsiz!")
        _after_login(request, user)
        return redirect(_next(request))
    return render(request, "accounts/register.html", {"form": form, "next": _next(request, "")})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("kabinet")
    form = LoginForm(request.POST or None)
    ip = request.META.get("REMOTE_ADDR", "")
    key = f"login-fail:{ip}"
    if request.method == "POST":
        if cache.get(key, 0) >= MAX_ATTEMPTS:
            form.add_error(None, "Juda ko'p urinish. 15 daqiqadan keyin qayta urinib ko'ring.")
        elif form.is_valid():
            user = authenticate(request, phone=form.cleaned_data["phone"], password=form.cleaned_data["password"])
            if user is None:
                cache.set(key, cache.get(key, 0) + 1, WINDOW)
                form.add_error(None, "Telefon raqami yoki parol noto'g'ri.")
            else:
                cache.delete(key)
                login(request, user)
                _after_login(request, user)
                return redirect(_next(request))
    return render(request, "accounts/login.html", {"form": form, "next": _next(request, "")})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ma'lumotlaringiz saqlandi.")
        _after_login(request, request.user)
        return redirect(_next(request))
    return render(request, "accounts/profile.html", {"form": form, "next": _next(request, "")})
