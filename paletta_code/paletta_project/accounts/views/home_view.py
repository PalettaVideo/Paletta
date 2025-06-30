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
    """
    BACKEND/FRONTEND-READY: Find library by URL slug.
    MAPPED TO: URL routing and library context
    USED BY: Middleware and URL processing
    
    Converts URL slug back to library object for context.
    """
    for library in Library.objects.all():
        if slugify(library.name) == slug:
            return library
    return None

class HomeView(TemplateView):
    """
    BACKEND/FRONTEND-READY: Main homepage with library-specific content.
    MAPPED TO: / and /home/ URLs
    USED BY: homepage.html template
    
    Displays library categories and content with authentication-based rendering.
    """
    
    def get(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Render homepage with library context.
        MAPPED TO: GET / and GET /home/
        USED BY: Main site navigation and homepage access
        
        Provides categorized content view with library-specific categories.
        """
        context = {}
        
        current_library = getattr(request, 'current_library', None)
        
        if not current_library:
            try:
                current_library = Library.objects.get(name='Paletta')
            except Library.DoesNotExist:
                current_library = None
                messages.error(request, 'Default Paletta library not found. Please contact administrator.')
        
        if request.user.is_authenticated:
            try:
                categories = []
                
                if current_library:
                    library_categories = Category.objects.filter(
                        library=current_library, 
                        is_active=True
                    ).order_by('subject_area')
                    
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
                    
                    if private_category:
                        categories.insert(0, private_category)
                    categories.extend(other_categories)
                else:
                    categories = []
                    
            except Exception as e:
                logger.error(f"Error loading categories: {str(e)}")
                categories = []
            
            libraries = Library.objects.filter(is_active=True)
            context = {
                'categories': categories,
                'libraries': libraries,
                'current_library': current_library,
            }
            
        else:
            messages.info(request, 'Please login to access the homepage.')
            return redirect('login')
        
        return render(request, 'homepage.html', context)

class StaticPageMixin:
    """
    BACKEND/FRONTEND-READY: Mixin for adding library context to static pages.
    MAPPED TO: Static page templates
    USED BY: About, Contact, Terms, Privacy, Q&A views
    
    Provides consistent library context across all static pages.
    """
    def get_context_data(self, **kwargs):
        """
        BACKEND/FRONTEND-READY: Add library context to static pages.
        MAPPED TO: Template context
        USED BY: All static page templates
        
        Ensures library branding consistency across static content.
        """
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
    """
    BACKEND/FRONTEND-READY: About us page with library context.
    MAPPED TO: /about/ URL
    USED BY: about_us.html template
    
    Static page displaying company information with library branding.
    """
    template_name = 'about_us.html'

class ContactUsView(StaticPageMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Contact information page.
    MAPPED TO: /contact/ URL
    USED BY: contact_us.html template
    
    Static page with contact details and library context.
    """
    template_name = 'contact_us.html'

class QAndAView(StaticPageMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Questions and answers page.
    MAPPED TO: /qa/ URL
    USED BY: q_and_a.html template
    
    FAQ page with library-specific context and branding.
    """
    template_name = 'q_and_a.html'

class TermsConditionsView(StaticPageMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Terms and conditions page.
    MAPPED TO: /terms/ URL
    USED BY: terms_conditions.html template
    
    Legal terms page with library context.
    """
    template_name = 'terms_conditions.html'

class PrivacyView(StaticPageMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Privacy policy page.
    MAPPED TO: /privacy/ URL
    USED BY: privacy.html template
    
    Privacy policy with library-specific context.
    """
    template_name = 'privacy.html'

class LogoutView(TemplateView):
    """
    BACKEND/FRONTEND-READY: User logout functionality.
    MAPPED TO: /logout/ URL
    USED BY: Navigation logout links
    
    Handles user logout and redirects to login page.
    """
    def get(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Process user logout.
        MAPPED TO: GET /logout/
        USED BY: Logout navigation and session termination
        
        Terminates user session and redirects to login page.
        """
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
