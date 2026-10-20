from django import template

register = template.Library()


@register.filter
def som(value):
    """150000 -> '150 000'"""
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return value
