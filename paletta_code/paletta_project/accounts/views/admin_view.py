from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from ..models import User

class ManageAdministratorsView(LoginRequiredMixin, TemplateView):
    """View for managing administrators."""
    template_name = 'manage_admin.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ONLY allow admin or owner users to access this view
        if self.request.user.role not in ['admin', 'owner']:
            context['permission_error'] = True
            return context
        
        # Get all administrators
        admins = User.objects.filter(role='admin')
        context['admins'] = admins
        
        return context 