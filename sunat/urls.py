from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Sunat.cc boshqaruv"
admin.site.site_title = "Sunat.cc"
admin.site.index_title = "Boshqaruv paneli"

urlpatterns = [
    path("boshqaruv/", admin.site.urls),
    path("", include("accounts.urls")),
    path("auth/", include("allauth.urls")),
    path("", include("shop.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
