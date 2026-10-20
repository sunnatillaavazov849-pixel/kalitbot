from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAdapter(DefaultSocialAccountAdapter):
    """Google orqali kirganda ismni Google profilidan oladi."""

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        full = " ".join(x for x in (data.get("first_name"), data.get("last_name")) if x)
        user.name = (full or data.get("name") or "")[:80]
        return user
