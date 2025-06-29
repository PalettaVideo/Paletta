"""
BACKEND/FRONTEND-READY: Views package for accounts app functionality.
MAPPED TO: Django URL routing and template rendering
USED BY: URL dispatcher and frontend templates

Provides comprehensive user management views including authentication,
registration, profile management, and admin operations.
"""

# Import views from individual files
from .login import CustomLoginView
from .signup import SignupView
from .forgot_password import ForgotPasswordView
from .home_view import HomeView, LogoutView
from .update_profile import ProfileView, ProfileUpdateView
from .admin_view import ManageAdministratorsView

# Import API views from a separate file
from .api_views import CustomAuthToken, UserViewSet, IsOwnerOrAdmin, check_user, make_admin, revoke_admin

# Export all views to make them available when importing from accounts.views
__all__ = [
    'CustomLoginView',
    'SignupView',
    'ForgotPasswordView',
    'HomeView',
    'LogoutView',
    'ProfileView',
    'ProfileUpdateView',
    'CustomAuthToken',
    'UserViewSet',
    'IsOwnerOrAdmin',
    'ManageAdministratorsView',
    'check_user',
    'make_admin',
    'revoke_admin'
] 