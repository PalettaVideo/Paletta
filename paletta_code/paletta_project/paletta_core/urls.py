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

# health check view
def health_check(request):
    return HttpResponse("OK", content_type="text/plain")

# import views directly from their modules to avoid circular imports
from accounts.views.login import CustomLoginView
from accounts.views.signup import SignupView
from accounts.views.forgot_password import ForgotPasswordView
from accounts.views.home_view import HomeView, LogoutView, AboutUsView, ContactUsView, QAndAView, TermsConditionsView, PrivacyView
from accounts.views.update_profile import ProfileView, CollectionView
from accounts.views.admin_view import ManageAdministratorsView
from videos.views.clip_store_view import CategoryClipView
from videos.views.video_detail_view import VideoDetailView
from videos.views.video_management_views import VideoEditView, VideoDeleteView

from videos.views.page_views import UploadPageView
from videos.views.upload_view import UploadHistoryView
from orders.views import CartView, CheckoutView, OrdersListView, OrderDetailView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    
    # Include videos API URLs with API prefix
    path('api/', include('videos.api_urls')),
    
    # Include videos frontend URLs without API prefix for frontend pages
    path('videos/', include('videos.urls')),
    
    # Include libraries app URLs with API prefix
    path('api/libraries/', include('libraries.urls')),
    
    # Include orders app API URLs with API prefix for download requests
    path('api/orders/', include('orders.api_urls')),
    
    # HTML page routes
    path('', CustomLoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('home/', HomeView.as_view(), name='home'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # LIBRARY-SCOPED ROUTES
    # Library context is set by middleware and maintained through these routes
    path('library/<str:library_slug>/', HomeView.as_view(), name='library_home'),
    
    # Video Content & Navigation                                                            
    path('library/<str:library_slug>/category/clip-store/', CategoryClipView.as_view(), name='library_clip_store'),
    path('library/<str:library_slug>/category/<str:category_slug>/', CategoryClipView.as_view(), name='library_category'),
    path('library/<str:library_slug>/video/<int:video_id>/', VideoDetailView.as_view(), name='library_video_detail'),
    
    # Video Management                                                                      
    path('library/<str:library_slug>/videos/edit/<int:video_id>/', VideoEditView.as_view(), name='library_video_edit'),
    path('library/<str:library_slug>/videos/delete/<int:video_id>/', VideoDeleteView.as_view(), name='library_video_delete'),
    
    # Upload System                                                                         
    path('library/<str:library_slug>/upload/', UploadPageView.as_view(), name='library_upload'),
    path('library/<str:library_slug>/upload/history/', UploadHistoryView.as_view(), name='library_upload_history'),
    
    # User Profile & Collection                                                                
    path('library/<str:library_slug>/profile/', ProfileView.as_view(), name='library_profile'),
    path('library/<str:library_slug>/collection/', CollectionView.as_view(), name='library_collection'),
    
    # Commerce & Orders                                                                      
    path('library/<str:library_slug>/cart/', CartView.as_view(), name='library_cart'),
    path('library/<str:library_slug>/checkout/', CheckoutView.as_view(), name='library_checkout'),
    path('library/<str:library_slug>/orders/', OrdersListView.as_view(), name='library_orders_list'),
    path('library/<str:library_slug>/orders/<int:pk>/', OrderDetailView.as_view(), name='library_order_detail'),
    
    # order management frontend pages
    path('', include('orders.urls')),
    
    # additional page routes
    path('about/', AboutUsView.as_view(), name='about_us'),
    path('contact/', ContactUsView.as_view(), name='contact_us'),
    path('help/', QAndAView.as_view(), name='q_and_a'),
    path('terms/', TermsConditionsView.as_view(), name='terms_conditions'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    
    # library management routes
    path('libraries/create/', login_required(CreateLibraryView.as_view()), name='create_library'),
    path('libraries/manage/', login_required(ManageLibrariesView.as_view()), name='manage_libraries'),
    path('libraries/edit/', login_required(EditLibraryView.as_view()), name='edit_library'),
   
    # admin management routes
    path('admins/manage/', login_required(ManageAdministratorsView.as_view()), name='manage_administrators'),
    # contributor application route - TODO: discuss with the team if we need this! - currently unused
    path('contributor/apply/', TemplateView.as_view(template_name='contributor_form.html'), name='contributor_apply'),
    # health check endpoint
    path('healthcheck/', health_check, name='health_check'),
]

# serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Add this line to serve files from STATICFILES_DIRS as well
    for static_dir in settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=static_dir)
    
    # serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)