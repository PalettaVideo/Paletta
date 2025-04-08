from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib import messages
from ..models import User

class ForgotPasswordView(TemplateView):
    """Custom forgot password view that serves the forget_password.html file."""
    
    def get(self, request, *args, **kwargs):
        """Serve the forget_password.html file."""
        return render(request, 'forget_password.html')
    
    def post(self, request, *args, **kwargs):
        """Handle forgot password form submission."""
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            # TODO: send a password reset email here
            messages.success(request, 'Password reset link has been sent to your email.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
        
        return render(request, 'forget_password.html')
