from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from videos.models import Category, PalettaCategory
from videos.serializers import CategorySerializer
from libraries.models import Library
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)

def get_library_by_slug(slug):
    """Get a library by its slug."""
    for library in Library.objects.all():
        if slugify(library.name) == slug:
            return library
    return None

class HomeView(TemplateView):
    """Home view that serves the unified home page with conditional content based on authentication."""
    
    def get(self, request, *args, **kwargs):
        """Serve the home page with appropriate context."""
        context = {}
        
        # Debug logging for library context
        url_library_slug = getattr(request, 'url_library_slug', None)
        logger.debug(f"[HomePage Debug] URL library slug: {url_library_slug}")
        logger.debug(f"[HomePage Debug] Request path: {request.path}")
        
        # Use current library from middleware (this is already set by LibraryContextMiddleware)
        current_library = getattr(request, 'current_library', None)
        logger.debug(f"[HomePage Debug] Current library from middleware: {current_library.name if current_library else 'None'}")
        
        # Fallback to Paletta if no current library
        if not current_library:
            try:
                current_library = Library.objects.get(name='Paletta')
                logger.debug("[HomePage Debug] Fallback to Paletta library")
            except Library.DoesNotExist:
                current_library = None
                messages.error(request, 'Default Paletta library not found. Please contact administrator.')
                logger.error("[HomePage Debug] Paletta library not found!")
        
        if request.user.is_authenticated:
            try:
                # Get categories based on library type
                categories = []
                
                if current_library and current_library.uses_paletta_categories:
                    # For Paletta libraries, get PalettaCategory objects
                    paletta_categories = PalettaCategory.objects.filter(is_active=True).order_by('code')
                    for pc in paletta_categories:
                        categories.append({
                            'id': f'paletta_{pc.id}',
                            'name': pc.display_name,
                            'display_name': pc.display_name,
                            'code': pc.code,
                            'type': 'paletta_category',
                            'image_url': pc.image_url() if hasattr(pc, 'image_url') else None,
                        })
                
                # ALWAYS add library-specific categories (including Private) for ALL libraries
                if current_library:
                    library_categories = Category.objects.filter(
                        library=current_library, 
                        is_active=True
                    ).order_by('subject_area')
                    
                    # Separate Private category to show it first
                    private_category = None
                    other_categories = []
                    
                    for lc in library_categories:
                        cat_data = {
                            'id': lc.id,
                            'name': lc.display_name,
                            'display_name': lc.display_name,
                            'code': lc.subject_area,
                            'type': 'library_category',
                            'image_url': lc.image.url if lc.image else None,
                        }
                        
                        if lc.subject_area == 'private':
                            private_category = cat_data
                        else:
                            other_categories.append(cat_data)
                    
                    # Add Private category first (pinned), then other categories
                    if private_category:
                        categories.insert(0, private_category)  # Insert at beginning
                    categories.extend(other_categories)
                else:
                    # For no library context, show default categories
                    categories = []
                    
                print(f"Loaded {len(categories)} categories for homepage")
                if categories:
                    print(f"First category: {categories[0]['name']}")
                
            except Exception as e:
                print(f"Error loading categories: {str(e)}")
                categories = []
            
            # Get all libraries for the sidebar
            libraries = Library.objects.filter(is_active=True)
            
            # CLEAN APPROACH: Let middleware handle library context
            # No need to manually add library_slug to context
            context = {
                'categories': categories,
                'libraries': libraries,
                'current_library': current_library,
            }
            
            logger.debug(f"[HomePage Debug] Context categories count: {len(categories)}")
        else:
            logger.debug("[HomePage Debug] User not authenticated")
        
        # Return the single homepage template with the context
        return render(request, 'homepage.html', context)

class StaticPageMixin:
    """A mixin to add the current library context to a static page view."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        library_id = self.request.session.get('current_library_id')
        if library_id:
            try:
                context['current_library'] = Library.objects.get(id=library_id)
            except Library.DoesNotExist:
                context['current_library'] = None
        else:
            context['current_library'] = None
        return context

class AboutUsView(StaticPageMixin, TemplateView):
    template_name = 'about_us.html'

class ContactUsView(StaticPageMixin, TemplateView):
    template_name = 'contact_us.html'

class QAndAView(StaticPageMixin, TemplateView):
    template_name = 'q_and_a.html'

class LogoutView(TemplateView):
    """View to handle user logout."""
    
    def get(self, request, *args, **kwargs):
        """Log the user out and redirect to login page."""
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
