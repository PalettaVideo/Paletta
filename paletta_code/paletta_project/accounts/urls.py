"""
BACKEND/FRONTEND-READY: URL routing configuration for accounts app.
MAPPED TO: /api/accounts/ namespace
USED BY: Django URL dispatcher and API clients

Provides REST API endpoints for user management, authentication, and admin operations.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.api_views import UserViewSet, CustomAuthToken, check_user, make_admin, revoke_admin

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomAuthToken.as_view(), name='token_obtain'),
    # User check, promotion, and revocation endpoints
    path('check-user/', check_user, name='check_user'),
    path('make-admin/', make_admin, name='make_admin'),
    path('revoke-administrator/<int:admin_id>/', revoke_admin, name='revoke_admin'),
] 