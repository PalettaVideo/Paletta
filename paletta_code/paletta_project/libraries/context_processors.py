def library_context(request):
    """
    BACKEND/FRONTEND-READY: Global context processor for library information.
    MAPPED TO: TEMPLATES setting in settings.py
    USED BY: All Django templates
    
    Provides current_library and all_libraries context to all templates.
    Required middleware: LibraryContextMiddleware
    """
    context = {
        'current_library': getattr(request, 'current_library', None),
        'all_libraries': getattr(request, 'all_libraries', []),
    }
    
    return context 