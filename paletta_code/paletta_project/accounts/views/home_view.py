from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from videos.models import ContentType
from libraries.models import Library
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)

def get_library_by_slug(slug):
    """
    BACKEND/FRONTEND-READY: Find library by URL slug.
    MAPPED TO: URL routing and library context
    USED BY: Middleware and URL processing
    
    Converts URL slug back to library object for context.
    """
    for library in Library.objects.all():
        if slugify(library.name) == slug:
            return library
    return None

class HomeView(TemplateView):
    """
    BACKEND/FRONTEND-READY: Main homepage with library-specific content.
    MAPPED TO: / and /home/ URLs
    USED BY: homepage.html template
    
    Displays library categories and content with authentication-based rendering.
    """
    
    def get(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Render homepage with library context.
        MAPPED TO: GET / and GET /home/
        USED BY: Main site navigation and homepage access
        
        Provides categorized content view with library-specific categories.
        """
        context = {}
        
        current_library = getattr(request, 'current_library', None)
        
        if not current_library:
            try:
                current_library = Library.objects.get(name='Paletta')
            except Library.DoesNotExist:
                current_library = None
                messages.error(request, 'Default Paletta library not found. Please contact administrator.')
        
        if request.user.is_authenticated:
            try:
                content_types = []
                
                if current_library:
                    library_content_types = ContentType.objects.filter(
                        library=current_library, 
                        is_active=True
                    ).order_by('subject_area')
                    
                    private_content_type = None
                    other_content_types = []
                    
                    for ct in library_content_types:
                        content_type_data = {
                            'id': ct.id,
                            'name': ct.display_name,
                            'display_name': ct.display_name,
                            'code': ct.subject_area,
                            'type': 'library_content_type',
                            'image_url': ct.image.url if ct.image else None,
                        }
                        
                        if ct.subject_area == 'private':
                            private_content_type = content_type_data
                        else:
                            other_content_types.append(content_type_data)
                    
                    if private_content_type:
                        content_types.insert(0, private_content_type)
                    content_types.extend(other_content_types)
                else:
                    content_types = []
                    
            except Exception as e:
                logger.error(f"Error loading content types: {str(e)}")
                content_types = []
            
            libraries = Library.objects.filter(is_active=True)
            
            # Add user role for permission checking
            user_role = 'user'  # Default role
            if request.user.is_superuser or request.user.role == 'owner':
                user_role = 'owner'
            elif request.user.role == 'admin':
                user_role = 'admin'
            
            context = {
                'content_types': content_types,
                'libraries': libraries,
                'current_library': current_library,
                'user_role': user_role,
                'all_libraries': libraries,  # For sidebar
            }
            
        else:
            messages.info(request, 'Please login to access the homepage.')
            return redirect('login')
        
        return render(request, 'homepage.html', context)

class StaticPageMixin:
    """
    BACKEND/FRONTEND-READY: Mixin for adding library context to static pages.
    MAPPED TO: Static page templates
    USED BY: About, Contact, Terms, Privacy, Q&A views
    
    Provides consistent library context across all static pages.
    """
    def get_context_data(self, **kwargs):
        """
        BACKEND/FRONTEND-READY: Add library context to static pages.
        MAPPED TO: Template context
        USED BY: All static page templates
        
        Ensures library branding consistency across static content.
        """
        context = super().get_context_data(**kwargs)
        library_id = self.request.session.get('current_library_id')
        if library_id:
            try:
                context['current_library'] = Library.objects.get(id=library_id)
            except Library.DoesNotExist:
                context['current_library'] = None
        else:
            context['current_library'] = None
        return context

class AboutUsView(StaticPageMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: About us page with library context.
    MAPPED TO: /about/ URL
    USED BY: about_us.html template
    
    Static page displaying company information with library branding.
    """
    template_name = 'about_us.html'

class ContactUsView(StaticPageMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Contact information page with form handling.
    MAPPED TO: /contact/ URL
    USED BY: contact_us.html template
    
    Handles contact form submissions and sends emails to the team.
    """
    template_name = 'contact_us.html'
    
    def post(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Process contact form submission.
        MAPPED TO: POST /contact/
        USED BY: contact_us.html form submission
        
        Validates form data and sends notification email to the team.
        Required fields: email, message
        """
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if not email or not message:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, self.template_name)
        
        try:
            # Send contact form notification to team
            self.send_contact_notification(email, message, request)
            
            messages.success(
                request, 
                'Thank you for your message! We will get back to you soon.'
            )
            
        except Exception as e:
            logger.error(f"Failed to send contact form notification: {str(e)}")
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
        
        return render(request, self.template_name)
    
    def send_contact_notification(self, email, message, request):
        """
        Send contact form notification to the team.
        
        Args:
            email: Sender's email address
            message: Contact message content
            request: HTTP request object
        """
        try:
            # Get manager email from settings (consistent with forgot password)
            manager_email = getattr(settings, 'MANAGER_EMAIL', 'niklaas@filmbright.com')
            sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@filmbright.com')
            
            # Prepare email content
            subject = f'New Contact Form Message - From: {email}'
            
            # Get sender's IP address
            ip_address = self.get_client_ip(request)
            
            # Create email body
            context = {
                'sender_email': email,
                'message': message,
                'ip_address': ip_address,
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'request_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # Render email template
            html_message = render_to_string('accounts/emails/contact_form_notification.html', context)
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
            
            logger.info(f"Contact form notification sent to manager from {email}")
            
        except Exception as e:
            logger.error(f"Failed to send contact form notification from {email}: {str(e)}")
            raise
    
    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class QAndAView(StaticPageMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Questions and answers page.
    MAPPED TO: /qa/ URL
    USED BY: q_and_a.html template
    
    FAQ page with library-specific context and branding.
    """
    template_name = 'q_and_a.html'

class TermsConditionsView(StaticPageMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Terms and conditions page.
    MAPPED TO: /terms/ URL
    USED BY: terms_conditions.html template
    
    Legal terms page with library context.
    """
    template_name = 'terms_conditions.html'

class PrivacyView(StaticPageMixin, TemplateView):
    """
    BACKEND/FRONTEND-READY: Privacy policy page.
    MAPPED TO: /privacy/ URL
    USED BY: privacy.html template
    
    Privacy policy with library-specific context.
    """
    template_name = 'privacy.html'

class LogoutView(TemplateView):
    """
    BACKEND/FRONTEND-READY: User logout functionality.
    MAPPED TO: /logout/ URL
    USED BY: Navigation logout links
    
    Handles user logout and redirects to login page.
    """
    def get(self, request, *args, **kwargs):
        """
        BACKEND/FRONTEND-READY: Process user logout.
        MAPPED TO: GET /logout/
        USED BY: Logout navigation and session termination
        
        Terminates user session and redirects to login page.
        """
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
