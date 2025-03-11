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