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
from accounts.views.home_view import HomeView, LogoutView, AboutUsView, ContactUsView, QAndAView, TermsConditionsView, PrivacyView
from accounts.views.update_profile import ProfileView, ProfileUpdateView, CollectionView
from accounts.views.admin_view import ManageAdministratorsView
from videos.views.clip_store_view import CategoryClipView
from videos.views.video_detail_view import VideoDetailView
from videos.views.thumbnail_view import VideoThumbnailAPIView
from videos.views.page_views import UploadPageView
from videos.views.upload_view import UploadHistoryView
from orders.views import CartView, CheckoutView, OrdersListView, OrderDetailView

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
    
    # Library-specific URLs (with library context)
    path('library/<str:library_slug>/', HomeView.as_view(), name='library_detail'),
    path('library/<str:library_slug>/category/clip-store/', CategoryClipView.as_view(), name='library_clip_store'),
    path('library/<str:library_slug>/category/<str:category_slug>/', CategoryClipView.as_view(), name='library_category'),
    path('library/<str:library_slug>/clip/<int:video_id>/', VideoDetailView.as_view(), name='library_clip_detail'),
    path('library/<str:library_slug>/upload/', UploadPageView.as_view(), name='library_upload'),
    path('library/<str:library_slug>/upload/history/', UploadHistoryView.as_view(), name='library_upload_history'),
    path('library/<str:library_slug>/profile/', ProfileView.as_view(), name='library_profile'),
    path('library/<str:library_slug>/collection/', CollectionView.as_view(), name='library_collection'),
    path('library/<str:library_slug>/cart/', CartView.as_view(), name='library_cart'),
    path('library/<str:library_slug>/checkout/', CheckoutView.as_view(), name='library_checkout'),
    path('library/<str:library_slug>/orders/', OrdersListView.as_view(), name='library_orders_list'),
    path('library/<str:library_slug>/orders/<int:pk>/', OrderDetailView.as_view(), name='library_order_detail'),
    
    # Order management routes - include the orders app URLs
    path('', include('orders.urls')),
    
    # Additional page routes
    path('about/', AboutUsView.as_view(), name='about_us'),
    path('contact/', ContactUsView.as_view(), name='contact_us'),
    path('help/', QAndAView.as_view(), name='q_and_a'),
    path('terms/', TermsConditionsView.as_view(), name='terms_conditions'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    
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