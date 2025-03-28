"""
URL configuration for paletta_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

# Import views directly from their modules to avoid circular imports
from accounts.views.login import CustomLoginView
from accounts.views.signup import SignupView
from accounts.views.forgot_password import ForgotPasswordView
from accounts.views.home_view import HomeView, LogoutView
from accounts.views.update_profile import ProfileView, ProfileUpdateView
from videos.views.upload_view import UploadView, UploadHistoryView
from videos.views.clip_store_view import ClipStoreView, CategoryClipView

# Create a class for category views
class CategoryView(TemplateView):
    template_name = 'inside_category.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = kwargs.get('category', '')
        return context

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/videos/', include('videos.urls')),
    path('api/libraries/', include('libraries.urls')),
    
    # HTML page routes
    path('', CustomLoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('home/', HomeView.as_view(), name='home'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('upload/history/', UploadHistoryView.as_view(), name='upload_history'),
    
    # User profile and account pages
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('collection/', TemplateView.as_view(template_name='collection.html'), name='collection'),
    path('cart/', TemplateView.as_view(template_name='cart.html'), name='cart'),
    path('order/', TemplateView.as_view(template_name='my_order.html'), name='order'),
    
    # Additional page routes
    path('about/', TemplateView.as_view(template_name='about_us.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact_us.html'), name='contact'),
    path('clip-store/', ClipStoreView.as_view(), name='clip_store'),
    path('category/<str:category>/', CategoryClipView.as_view(), name='category'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Add this line to serve files from STATICFILES_DIRS as well
    for static_dir in settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=static_dir)
    
    # Serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

