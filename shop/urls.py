from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("plagin/<slug:slug>/", views.plugin_detail, name="plugin"),
    path("sotib-olish/<slug:slug>/", views.buy, name="buy"),
    path("buyurtma/<int:pk>/", views.order_detail, name="order"),
    path("kabinet/", views.cabinet, name="kabinet"),
    path("kabinet/almashtirish/<int:pk>/", views.transfer, name="transfer"),
    path("kabinet/eski/", views.legacy_tz, name="legacy_tz"),
    path("kabinet/yuklab/<int:pk>/", views.download, name="download"),
    path("dastur/", views.app_page, name="app"),
    path("yordam/", views.help_page, name="help"),
    path("api/plaginlar.json", views.api_plugins, name="api_plugins"),
    path("boshqaruv-fayl/chek/<int:pk>/", views.staff_receipt, name="staff_receipt"),
]
