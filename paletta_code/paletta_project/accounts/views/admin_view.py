from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from ..models import User

class ManageAdministratorsView(LoginRequiredMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Administrator management interface.
    MAPPED TO: /admin/manage-administrators/ URL
    USED BY: manage_admin.html template
    
    Displays administrator list with role-based access control.
    PERMISSIONS: Only users with Owner level (superuser) can manage administrators.
    """
    template_name = 'manage_admin.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Check if user has Owner level permissions before allowing access.
        """
        if not (request.user.is_superuser or request.user.role == 'owner'):
            messages.error(request, 'Only users with Owner level access can manage administrators.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        BACKEND/FRONTEND-READY: Prepare administrator data for template.
        MAPPED TO: Template context
        USED BY: manage_admin.html template
        
        Provides admin list with permission validation for owner users only.
        """
        context = super().get_context_data(**kwargs)
        
        # ONLY allow owner-level users to access this view - already checked in dispatch
        if not (self.request.user.is_superuser or self.request.user.role == 'owner'):
            context['permission_error'] = True
            return context
        
        # Get all administrators
        admins = User.objects.filter(role='admin')
        context['admins'] = admins
        
        return context 