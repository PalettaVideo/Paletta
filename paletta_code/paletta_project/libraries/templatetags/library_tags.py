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
    Generate library-specific URLs with automatic library slug injection.
    This is the main function for generating library-aware URLs.
    
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
    Get the slug for the current library on-demand.
    Usage: {% current_library_slug %}
    """
    request = context['request']
    current_library = getattr(request, 'current_library', None)
    return slugify(current_library.name) if current_library else 'paletta'

@register.filter
def library_slugify(value):
    """
    Convert a library name to a URL-friendly slug.
    Usage: {{ library.name|library_slugify }}
    """
    return slugify(value)

@register.simple_tag(takes_context=True)
def library_title(context, page_title=""):
    """
    Generate page title with library context.
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
    Generate versioned static file URLs to force cache invalidation.
    Usage: {% versioned_static 'js/homepage.js' %}
    """
    # Get the static URL
    static_url = static(path)
    
    # Add version parameter based on settings or current timestamp
    version = getattr(settings, 'STATIC_VERSION', None)
    if not version:
        # Fallback to timestamp for development
        version = str(int(time.time()))
    
    # Add version parameter
    separator = '&' if '?' in static_url else '?'
    return f"{static_url}{separator}v={version}" 