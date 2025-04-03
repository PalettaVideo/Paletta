import os
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def static_exists(static_path):
    """
    Check if a static file exists.
    Usage: {% if 'path/to/file.jpg'|static_exists %}
    """
    for static_dir in settings.STATICFILES_DIRS:
        full_path = os.path.join(static_dir, static_path)
        if os.path.exists(full_path):
            return True
    return False

@register.filter
def divide(value, arg):
    """
    Divide the value by the argument
    """
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def modulo(value, arg):
    """
    Return the value modulo the argument
    """
    try:
        return int(value) % int(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def divisibleby(value, arg):
    """
    Check if value is divisible by argument
    """
    try:
        return int(value) % int(arg) == 0
    except (ValueError, ZeroDivisionError):
        return False 