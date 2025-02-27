from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages

class HomeView(TemplateView):
    """Home view that serves the appropriate home page based on user authentication."""
    
    def get(self, request, *args, **kwargs):
        """Serve the appropriate home page."""
        if request.user.is_authenticated:
            # determine which internal page to show based on user role
            if request.user.role in ['admin', 'owner']:
                return render(request, 'homepage_internal.html')
            elif request.user.role == 'contributor':
                return render(request, 'homepage_internal.html')  # TODO: create a specific contributor page
            else:
                return render(request, 'homepage_internal.html')  # TODO: create a specific customer page
        else:
            return render(request, 'homepage_external.html')

class LogoutView(TemplateView):
    """View to handle user logout."""
    
    def get(self, request, *args, **kwargs):
        """Log the user out and redirect to login page."""
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
