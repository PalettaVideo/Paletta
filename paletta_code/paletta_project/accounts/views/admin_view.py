from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from ..models import User

class ManageAdministratorsView(LoginRequiredMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Administrator management interface.
    MAPPED TO: /admin/manage-administrators/ URL
    USED BY: manage_admin.html template
    
    Displays administrator list with role-based access control.
    """
    template_name = 'manage_admin.html'
    
    def get_context_data(self, **kwargs):
        """
        BACKEND/FRONTEND-READY: Prepare administrator data for template.
        MAPPED TO: Template context
        USED BY: manage_admin.html template
        
        Provides admin list with permission validation for admin/owner users only.
        """
        context = super().get_context_data(**kwargs)
        
        # ONLY allow admin or owner users to access this view
        if self.request.user.role not in ['admin', 'owner']:
            context['permission_error'] = True
            return context
        
        # Get all administrators
        admins = User.objects.filter(role='admin')
        context['admins'] = admins
        
        return context 