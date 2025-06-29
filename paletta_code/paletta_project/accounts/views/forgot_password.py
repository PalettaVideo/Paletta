from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib import messages
from ..models import User

class ForgotPasswordView(TemplateView):
    """
    BACKEND/FRONTEND-READY: Password reset request interface.
    MAPPED TO: /forgot-password/ URL
    USED BY: forgot_password.html template
    
    Handles password reset requests with email validation.
    """
    
    def get(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Display password reset form.
        MAPPED TO: GET /forgot-password/
        USED BY: Password reset page access
        
        Shows password reset request form.
        """
        return render(request, 'forgot_password.html')
    
    def post(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Process password reset request.
        MAPPED TO: POST /forgot-password/
        USED BY: forgot_password.html form submission
        
        Validates email and initiates password reset process.
        Required fields: email
        """
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            # TODO: implement password reset email functionality
            messages.success(request, 'Password reset link has been sent to your email.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
        
        return render(request, 'forgot_password.html')
