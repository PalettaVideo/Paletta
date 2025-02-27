# Import views from individual files
from .login import CustomLoginView
from .signup import SignupView
from .forgot_password import ForgotPasswordView
from .home_view import HomeView, LogoutView
from .update_profile import ProfileView, ProfileUpdateView

# Import API views from a separate file
from .api_views import CustomAuthToken, UserViewSet, IsOwnerOrAdmin

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
    'IsOwnerOrAdmin'
] 