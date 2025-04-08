from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from videos.models import Category
from videos.serializers import CategorySerializer
from libraries.models import Library
from django.http import Http404
from django.utils.text import slugify

def get_library_slug(library_name):
    """Convert a library name to a URL-friendly slug."""
    return slugify(library_name)

def get_library_by_slug(slug):
    """Get a library by its slug."""
    for library in Library.objects.all():
        if get_library_slug(library.name) == slug:
            return library
    return None

class HomeView(TemplateView):
    """Home view that serves the unified home page with conditional content based on authentication."""
    
    def get(self, request, *args, **kwargs):
        """Serve the home page with appropriate context."""
        context = {}
        
        # Get the default Paletta library
        try:
            paletta_library = Library.objects.get(name='Paletta')
        except Library.DoesNotExist:
            paletta_library = None
            messages.error(request, 'Default Paletta library not found. Please contact administrator.')
        
        # Check if we have a library slug in the URL (new style)
        library_slug = kwargs.get('library_slug')
        
        # Get the current library from URL parameters (either by slug or id)
        if library_slug:
            # New URL format - get library by slug
            current_library = get_library_by_slug(library_slug)
            if not current_library:
                current_library = paletta_library
                messages.error(request, f'Library with slug "{library_slug}" not found. Defaulting to Paletta.')
            else:
                # Update session with current library for compatibility
                request.session['current_library_id'] = current_library.id
        else:
            # Legacy URL format - get by library_id parameter
            library_id = request.GET.get('library_id')
            
            # If no library_id in URL and we're at the root home URL, clear the session
            if not library_id and request.path == '/home/':
                request.session.pop('current_library_id', None)
                current_library = paletta_library
            elif library_id:
                try:
                    current_library = Library.objects.get(id=library_id)
                    # Update session with current library
                    request.session['current_library_id'] = library_id
                except Library.DoesNotExist:
                    current_library = paletta_library
                    messages.error(request, f'Library with ID {library_id} not found. Defaulting to Paletta.')
            else:
                current_library_id = request.session.get('current_library_id')
                if current_library_id:
                    try:
                        current_library = Library.objects.get(id=current_library_id)
                    except Library.DoesNotExist:
                        current_library = paletta_library
                else:
                    current_library = paletta_library
        
        if request.user.is_authenticated:
            try:
                # Get categories that belong to the current library
                categories = Category.objects.filter(library=current_library).order_by('name')
            except Exception as e:
                categories = []
                messages.error(request, f'Error fetching categories: {str(e)}')
            
            # Use the serializer to get proper image URLs
            serializer = CategorySerializer(categories, many=True, context={'request': request})
            
            # Get all libraries for the sidebar
            libraries = Library.objects.filter(is_active=True).exclude(id=paletta_library.id if paletta_library else None)
            
            # Add slugs to context for building URLs
            context = {
                'categories': serializer.data,
                'libraries': libraries,
                'current_library': current_library,
                'library_slug': get_library_slug(current_library.name) if current_library else None
            }
        
        # Return the single homepage template with the context
        return render(request, 'homepage.html', context)

class LogoutView(TemplateView):
    """View to handle user logout."""
    
    def get(self, request, *args, **kwargs):
        """Log the user out and redirect to login page."""
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
