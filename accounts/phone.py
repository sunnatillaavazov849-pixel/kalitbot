import re


def normalize_phone(text: str) -> str | None:
    """'90 123 45 67', '+998901234567', '998 90 123-45-67' -> '+998901234567'. Noto'g'ri bo'lsa None."""
    digits = re.sub(r"\D", "", text or "")
    if len(digits) == 9:
        digits = "998" + digits
    if not 11 <= len(digits) <= 15:
        return None
    return "+" + digits
