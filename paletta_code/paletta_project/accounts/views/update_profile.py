from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from libraries.models import Library

class ProfileView(TemplateView):
    """
    BACKEND/FRONTEND-READY: User profile display and management.
    MAPPED TO: /profile/ URL
    USED BY: my_profile.html template
    
    Shows user profile information with library context.
    """
    template_name = 'my_profile.html'
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Display user profile page.
        MAPPED TO: GET /profile/
        USED BY: Profile page access and navigation
        
        Renders profile page with user data and current library context.
        """
        user = request.user

        # get current library from session
        current_library = None
        current_library_id = request.session.get('current_library_id')
        if current_library_id:
            try:
                current_library = Library.objects.get(id=current_library_id)
            except Library.DoesNotExist:
                pass  # library not found, so no context will be passed
        
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

class FavouritesView(LoginRequiredMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: User's video favourites display.
    MAPPED TO: /favourites/ URL
    USED BY: favourites.html template
    
    Shows user's uploaded videos with library context.
    """
    template_name = 'favourites.html'

    def get_context_data(self, **kwargs):
        """
        BACKEND/FRONTEND-READY: Add library context to favourites page.
        MAPPED TO: Template context
        USED BY: favourites.html template
        
        Provides current library context for user's video favourites.
        """
        context = super().get_context_data(**kwargs)
        
        # get current library from session
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
    """
    BACKEND/FRONTEND-READY: User profile update processing.
    MAPPED TO: /profile/update/ URL
    USED BY: Profile edit forms
    
    Handles profile updates with password change and logout flow.
    """
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Process profile update form submission.
        MAPPED TO: POST /profile/update/
        USED BY: my_profile.html form submission
        
        Updates user profile fields with password handling and session management.
        Optional fields: email, first_name, last_name, company, institution, password
        """
        user = request.user
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        company = request.POST.get('company')
        institution = request.POST.get('institution')
        password = request.POST.get('password')
        
        # update user fields if provided
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
        
        # save the user and show success message
        user.save()
        messages.success(request, 'Profile updated successfully.')
        
        # Determine redirect URL based on library context
        current_library_id = request.session.get('current_library_id')
        if current_library_id:
            try:
                current_library = Library.objects.get(id=current_library_id)
                # Redirect to library-specific profile page
                return redirect('library_profile', library_slug=current_library.name.lower().replace(' ', '-'))
            except Library.DoesNotExist:
                pass
        
        # Fallback to general profile page
        return redirect('profile')