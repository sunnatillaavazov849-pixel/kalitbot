import os

from django import forms

RECEIPT_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".pdf"}
RECEIPT_MAX = 10 * 1024 * 1024


class RequestCodeForm(forms.Form):
    code = forms.CharField(label="So'rov kodi", max_length=40,
                           widget=forms.TextInput(attrs={"placeholder": "TT-K7QM-3XPA", "autocomplete": "off",
                                                         "spellcheck": "false", "class": "mono"}))


class ReceiptForm(forms.Form):
    receipt = forms.FileField(label="To'lov cheki (rasm yoki PDF)")

    def clean_receipt(self):
        f = self.cleaned_data["receipt"]
        if os.path.splitext(f.name)[1].lower() not in RECEIPT_EXT:
            raise forms.ValidationError("Chekni rasm (JPG, PNG) yoki PDF ko'rinishida yuklang.")
        if f.size > RECEIPT_MAX:
            raise forms.ValidationError("Fayl juda katta (10 MB gacha).")
        return f


class TransferForm(forms.Form):
    reason = forms.CharField(label="Nima bo'ldi?", max_length=500,
                             widget=forms.TextInput(attrs={"placeholder": "Masalan: Windows qayta o'rnatildi"}))
    confirm = forms.CharField(label="Tasdiq kodi", max_length=20, required=False,
                              widget=forms.TextInput(attrs={"placeholder": "AB3K-7QMX", "class": "mono",
                                                            "autocomplete": "off"}))
    no_code = forms.BooleanField(label="Eski kompyuter ishlamayapti — tasdiq kodi yo'q", required=False)

    def clean_reason(self):
        reason = self.cleaned_data["reason"].strip()
        if len(reason) < 3:
            raise forms.ValidationError("Sababni bir necha so'z bilan yozing.")
        return reason

    def clean(self):
        data = super().clean()
        if not data.get("no_code") and not (data.get("confirm") or "").strip():
            self.add_error("confirm", "Eski kompyuterdagi tasdiq kodini kiriting yoki pastdagi belgini qo'ying.")
        return data


class TzClaimForm(forms.Form):
    code = forms.CharField(label="Eski kompyuter kodi", max_length=20,
                           widget=forms.TextInput(attrs={"placeholder": "K7QM-3XPA", "class": "mono"}))
