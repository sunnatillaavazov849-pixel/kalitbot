from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("royxat/", views.register, name="royxat"),
    path("kirish/", views.login_view, name="kirish"),
    path("chiqish/", views.logout_view, name="chiqish"),
    path("profil/", views.profile, name="profil"),
    # allauth'ning email kirish sahifalari o'rniga o'zimiznikiga yo'naltiramiz (Google kirish ishlayveradi)
    path("auth/login/", RedirectView.as_view(pattern_name="kirish")),
    path("auth/signup/", RedirectView.as_view(pattern_name="royxat")),
]
