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
        
        # current library from middleware
        current_library = getattr(request, 'current_library', None)
        
        # Fallback to Paletta if no current library
        if not current_library:
            try:
                current_library = Library.objects.get(name='Paletta')
            except Library.DoesNotExist:
                current_library = None
                messages.error(request, 'Default Paletta library not found. Please contact administrator.')
        
        if request.user.is_authenticated:
            try:
                # get categories - ONLY load library-specific Category objects
                categories = []
                
                if current_library:
                    library_categories = Category.objects.filter(
                        library=current_library, 
                        is_active=True
                    ).order_by('subject_area')
                    
                    # private category to show it first
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
                    
                    # add Private category first (pinned), then other categories
                    if private_category:
                        categories.insert(0, private_category)
                    categories.extend(other_categories)
                else:
                    # no library context, show default categories
                    categories = []
                    
            except Exception as e:
                logger.error(f"Error loading categories: {str(e)}")
                categories = []
            
            # get all libraries for the sidebar
            libraries = Library.objects.filter(is_active=True)
            context = {
                'categories': categories,
                'libraries': libraries,
                'current_library': current_library,
            }
            
        else:
            # user not authenticated, force user to login
            messages.info(request, 'Please login to access the homepage.')
            return redirect('login')
        
        # return the single homepage template with the context
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

class TermsConditionsView(StaticPageMixin, TemplateView):
    template_name = 'terms_conditions.html'

class PrivacyView(StaticPageMixin, TemplateView):
    template_name = 'privacy.html'

class LogoutView(TemplateView):
    def get(self, request, *args, **kwargs):
        """Log the user out and redirect to login page."""
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
