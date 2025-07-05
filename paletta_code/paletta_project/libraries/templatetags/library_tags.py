from django import template
from django.urls import reverse
from django.utils.text import slugify
from django.templatetags.static import static
from django.conf import settings
import time

register = template.Library()

@register.simple_tag(takes_context=True)
def library_specific_url(context, url_name, **kwargs):
    """
    FRONTEND-READY: Generate library-specific URLs with automatic slug injection.
    MAPPED TO: Django template system
    USED BY: All library templates for navigation links
    
    Automatically injects current library slug into URL generation.
    Usage: {% library_specific_url 'library_upload' %}
    """
    request = context['request']
    current_library = getattr(request, 'current_library', None)
    
    if current_library and 'library_slug' not in kwargs:
        kwargs['library_slug'] = slugify(current_library.name)
    
    try:
        return reverse(url_name, kwargs=kwargs)
    except Exception as e:
        print(f"Error generating library-specific URL for {url_name}: {e}")
        return '#'

@register.simple_tag(takes_context=True)
def current_library_slug(context):
    """
    FRONTEND-READY: Get current library slug for template usage.
    MAPPED TO: Django template system
    USED BY: Templates needing current library identification
    
    Returns URL-friendly slug of current library or 'paletta' as fallback.
    Usage: {% current_library_slug %}
    """
    request = context['request']
    current_library = getattr(request, 'current_library', None)
    return slugify(current_library.name) if current_library else 'paletta'

@register.filter
def library_slugify(value):
    """
    FRONTEND-READY: Convert library name to URL-friendly slug.
    MAPPED TO: Django template filter system
    USED BY: Templates for URL generation and CSS classes
    
    Converts any string to URL-safe format for library names.
    Usage: {{ library.name|library_slugify }}
    """
    return slugify(value)

@register.simple_tag(takes_context=True)
def library_title(context, page_title=""):
    """
    FRONTEND-READY: Generate contextual page titles with library branding.
    MAPPED TO: Django template system
    USED BY: All library templates for <title> tags
    
    Creates branded page titles with library name prefix.
    Usage: {% library_title "Upload" %} -> "Paletta - Upload"
    """
    request = context['request']
    current_library = getattr(request, 'current_library', None)
    
    library_name = current_library.name if current_library else 'Paletta'
    
    if page_title:
        return f"{library_name} - {page_title}"
    return library_name

@register.simple_tag
def versioned_static(path):
    """
    FRONTEND-READY: Generate cache-busting URLs for static files.
    MAPPED TO: Django template system and static file handling
    USED BY: All templates loading CSS/JS files
    
    Appends version parameter to static URLs to force cache invalidation.
    Usage: {% versioned_static 'js/homepage.js' %}
    """
    static_url = static(path)
    
    version = getattr(settings, 'STATIC_VERSION', None)
    if not version:
        version = str(int(time.time()))
    
    separator = '&' if '?' in static_url else '?'
    return f"{static_url}{separator}v={version}" 