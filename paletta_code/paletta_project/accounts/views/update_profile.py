from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from libraries.models import Library

class ProfileView(TemplateView):
    """View to handle user profile page."""
    template_name = 'my_profile.html'
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Render the profile page with user data and library context."""
        user = request.user

        # Get current library from session
        current_library = None
        current_library_id = request.session.get('current_library_id')
        if current_library_id:
            try:
                current_library = Library.objects.get(id=current_library_id)
            except Library.DoesNotExist:
                pass  # Library not found, so no context will be passed
        
        context = {
            'user_data': {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'institution': user.institution or '',
                'company': user.company or '',
                'role': user.role
            },
            'current_library': current_library
        }
        return render(request, self.template_name, context)

class CollectionView(LoginRequiredMixin, TemplateView):
    """View to handle user's collection page."""
    template_name = 'collection.html'

    def get_context_data(self, **kwargs):
        """Add library context to the collection page."""
        context = super().get_context_data(**kwargs)
        
        # Get current library from session
        current_library_id = self.request.session.get('current_library_id')
        if current_library_id:
            try:
                context['current_library'] = Library.objects.get(id=current_library_id)
            except Library.DoesNotExist:
                context['current_library'] = None
        else:
            context['current_library'] = None
            
        return context

class ProfileUpdateView(TemplateView):
    """View to handle user profile updates."""
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """Handle profile update form submission."""
        user = request.user
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        company = request.POST.get('company')
        institution = request.POST.get('institution')
        password = request.POST.get('password')
        
        # update user fields
        if email:
            user.email = email
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if company:
            user.company = company
        if institution:
            user.institution = institution
        
        # update password if provided
        if password:
            user.set_password(password)
            # save the user
            user.save()
            # log the user out
            logout(request)
            messages.success(request, 'Profile updated successfully. Please log in with your new password.')
            return redirect('login')
        
        # save the user
        user.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
