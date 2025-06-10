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
from django.http import HttpResponse
from libraries.views import CreateLibraryView, ManageLibrariesView, EditLibraryView

# Health check view
def health_check(request):
    return HttpResponse("OK", content_type="text/plain")

# Import views directly from their modules to avoid circular imports
from accounts.views.login import CustomLoginView
from accounts.views.signup import SignupView
from accounts.views.forgot_password import ForgotPasswordView
from accounts.views.home_view import HomeView, LogoutView
from accounts.views.update_profile import ProfileView, ProfileUpdateView, CollectionView
from accounts.views.admin_view import ManageAdministratorsView
from videos.views.clip_store_view import CategoryClipView
from videos.views.video_detail_view import VideoDetailView
from videos.views.thumbnail_view import VideoThumbnailAPIView

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
    
    # Include videos app URLs at various paths
    path('api/videos/', include('videos.urls')),
    path('videos/', include('videos.urls')),  # Include without the api/ prefix
    
    # Direct access to thumbnail API endpoint
    path('api/clip/<int:clip_id>/thumbnail/', VideoThumbnailAPIView.as_view(), name='api_clip_thumbnail_direct'),
    
    path('api/libraries/', include('libraries.urls')),
    
    # HTML page routes
    path('', CustomLoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('home/', HomeView.as_view(), name='home'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # New user-friendly URLs for libraries and categories
    path('library/<str:library_slug>/', HomeView.as_view(), name='library_detail'),
    path('library/<str:library_slug>/category/clip-store/', CategoryClipView.as_view(), name='library_clip_store'),
    path('library/<str:library_slug>/category/<str:category_slug>/', CategoryClipView.as_view(), name='library_category'),
    
    # User profile and account pages
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('collection/', CollectionView.as_view(), name='collection'),
    
    # Order management routes - include the orders app URLs
    path('', include('orders.urls')),
    
    # Additional page routes
    path('about/', TemplateView.as_view(template_name='about_us.html'), name='about_us'),
    path('contact/', TemplateView.as_view(template_name='contact_us.html'), name='contact_us'),
    path('help/', TemplateView.as_view(template_name='q_and_a.html'), name='q_and_a'),
    
    # Video detail route
    path('clip/<int:video_id>/', VideoDetailView.as_view(), name='clip_detail'),
    
    # Library management routes
    path('libraries/create/', login_required(CreateLibraryView.as_view()), name='create_library'),
    path('libraries/manage/', login_required(ManageLibrariesView.as_view()), name='manage_libraries'),
    path('libraries/edit/', login_required(EditLibraryView.as_view()), name='edit_library'),
    path('libraries/<str:library_name>/view/', TemplateView.as_view(template_name='library_view.html'), name='library_view'),
    
    # Admin management routes
    path('admins/manage/', login_required(ManageAdministratorsView.as_view()), name='manage_administrators'),
    
    # Contributor application route
    path('contributor/apply/', TemplateView.as_view(template_name='contributor_form.html'), name='contributor_apply'),
    
    # Health check endpoint
    path('healthcheck/', health_check, name='health_check'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Add this line to serve files from STATICFILES_DIRS as well
    for static_dir in settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=static_dir)
    
    # Serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)