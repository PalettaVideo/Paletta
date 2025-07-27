from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from ..models import User
import logging

logger = logging.getLogger(__name__)

class ForgotPasswordView(TemplateView):
    """
    BACKEND/FRONTEND-READY: Password reset request interface.
    MAPPED TO: /forgot-password/ URL
    USED BY: forgot_password.html template
    
    Handles password reset requests by notifying the manager instead of sending emails to users.
    This works around AWS SES sandbox limitations.
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
        
        Validates email and sends notification to manager for manual password reset.
        Required fields: email
        """
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Send notification to manager instead of user
            self.send_manager_notification(user, request)
            
            messages.success(
                request, 
                'Your password reset request has been submitted. Our team will contact you shortly to help you reset your password.'
            )
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
        
        return render(request, 'forgot_password.html')
    
    def send_manager_notification(self, user, request):
        """
        Send password reset notification to manager.
        
        Args:
            user: User object requesting password reset
            request: HTTP request object
        """
        try:
            # Get manager email from settings
            manager_email = getattr(settings, 'MANAGER_EMAIL', 'vvomifares@gmail.com')
            sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@filmbright.com')
            
            # Prepare email content
            subject = f'Password Reset Request - User: {user.email}'
            
            # Get user's IP address
            ip_address = self.get_client_ip(request)
            
            # Create email body
            context = {
                'user_email': user.email,
                'user_name': user.get_full_name() or user.email,
                'user_institution': user.institution or 'Not specified',
                'user_company': user.company or 'Not specified',
                'user_role': user.get_role_display(),
                'ip_address': ip_address,
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'request_date': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # Render email template
            html_message = render_to_string('accounts/emails/password_reset_notification.html', context)
            plain_message = strip_tags(html_message)
            
            # Send email to manager
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=sender_email,
                recipient_list=[manager_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Password reset notification sent to manager for user {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send password reset notification for user {user.email}: {str(e)}")
            raise
    
    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
