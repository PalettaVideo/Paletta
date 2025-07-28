def library_context(request):
    """
    BACKEND/FRONTEND-READY: Global context processor for library information.
    MAPPED TO: TEMPLATES setting in settings.py
    USED BY: All Django templates
    
    Provides current_library, all_libraries, and user_role context to all templates.
    Required middleware: LibraryContextMiddleware
    """
    context = {
        'current_library': getattr(request, 'current_library', None),
        'all_libraries': getattr(request, 'all_libraries', []),
    }
    
    # Add user role for permission checking across all templates
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_role = 'contributor'  # Default role
        
        if request.user.is_superuser or request.user.role == 'owner':
            user_role = 'owner'
        elif request.user.role == 'admin':
            user_role = 'admin'
        elif request.user.role == 'contributor':
            user_role = 'contributor'
        
        context['user_role'] = user_role
        
        # Check if user owns any libraries (for sidebar admin buttons)
        user_owns_libraries = request.user.owned_libraries.filter(is_active=True).exists()
        context['user_owns_libraries'] = user_owns_libraries
    else:
        context['user_role'] = 'user'  # For unauthenticated users
        context['user_owns_libraries'] = False
    
    return context 