from django import forms
from django.contrib.auth import password_validation

from .models import User
from .phone import normalize_phone

PHONE_HELP = "Masalan: +998 90 123 45 67"


class PhoneField(forms.CharField):
    def clean(self, value):
        value = super().clean(value)
        phone = normalize_phone(value)
        if not phone:
            raise forms.ValidationError("Telefon raqami noto'g'ri. " + PHONE_HELP)
        return phone


class RegisterForm(forms.Form):
    name = forms.CharField(label="Ismingiz", max_length=80)
    phone = PhoneField(label="Telefon raqamingiz", help_text=PHONE_HELP)
    password = forms.CharField(label="Parol", widget=forms.PasswordInput, min_length=6,
                               help_text="Kamida 6 ta belgi")
    password2 = forms.CharField(label="Parolni takrorlang", widget=forms.PasswordInput)

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Bu raqam bilan allaqachon ro'yxatdan o'tilgan. Kirish sahifasidan kiring.")
        return phone

    def clean(self):
        data = super().clean()
        if data.get("password") and data.get("password") != data.get("password2"):
            self.add_error("password2", "Parollar bir xil emas.")
        elif data.get("password"):
            try:
                password_validation.validate_password(data["password"])
            except forms.ValidationError as e:
                self.add_error("password", e)
        return data


class LoginForm(forms.Form):
    phone = PhoneField(label="Telefon raqamingiz", help_text=PHONE_HELP)
    password = forms.CharField(label="Parol", widget=forms.PasswordInput)


class ProfileForm(forms.ModelForm):
    phone = PhoneField(label="Telefon raqamingiz", help_text=PHONE_HELP)

    class Meta:
        model = User
        fields = ["name", "phone"]
        labels = {"name": "Ismingiz"}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("Ismingizni yozing.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu raqam boshqa akkauntga bog'langan. Admin bilan bog'laning.")
        return phone
