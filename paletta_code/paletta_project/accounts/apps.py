from django.apps import AppConfig

class AccountsConfig(AppConfig):
    """
    BACKEND-READY: Django app configuration for accounts management.
    MAPPED TO: Django app registry
    USED BY: Django application initialization
    
    Configures the accounts app with proper field defaults and metadata.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
