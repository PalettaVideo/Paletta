from django.utils.text import slugify
from .models import Library

def library_context(request):
    """
    Context processor to make library context available in all templates.
    This ensures consistent library information across all pages.
    
    improved approach: only provide current_library object.
    Library slug is generated on-demand via template tags or helper functions.
    """
    context = {
        'current_library': None,
        'available_libraries': [],
    }
    
    # Get library context from middleware
    if hasattr(request, 'current_library'):
        context['current_library'] = request.current_library
        
    if hasattr(request, 'available_libraries'):
        context['available_libraries'] = request.available_libraries
    
    return context 