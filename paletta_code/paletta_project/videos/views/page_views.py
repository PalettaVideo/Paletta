from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings
from libraries.models import Library, UserLibraryRole
from django.db.models import Q

@method_decorator(login_required, name='dispatch')
class UploadPageView(TemplateView):
    """
    Renders the main video upload page.
    This view's primary responsibility is to inject necessary configuration,
    like the API Gateway URL, into the template context for the frontend.
    """
    template_name = 'upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all libraries where user has access (owned + contributor/admin roles)
        user_owned_libraries = Q(owner=self.request.user)
        user_role_libraries = Q(user_roles__user=self.request.user, 
                               user_roles__role__in=['contributor', 'admin'])
        
        user_libraries = Library.objects.filter(
            user_owned_libraries | user_role_libraries
        ).distinct().filter(is_active=True)
        
        context['user_libraries'] = user_libraries
        
        # Determine the current library from the session
        current_library_id = self.request.session.get('current_library_id')
        current_library = None
        if current_library_id:
            current_library = user_libraries.filter(id=current_library_id).first()
        
        # Fallback to the first library if none is in the session
        if not current_library and user_libraries.exists():
            current_library = user_libraries.first()
            
        context['current_library'] = current_library
        
        # Inject the API Gateway URL from settings into the template (optional)
        context['API_GATEWAY_URL'] = getattr(settings, 'API_GATEWAY_URL', '')
        return context 