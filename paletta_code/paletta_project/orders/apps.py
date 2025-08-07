from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    BACKEND-READY: Django app configuration for orders management.
    MAPPED TO: Django app registry
    USED BY: Django application initialization
    
    Configures the orders app with proper field defaults and metadata.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = 'Orders'
    path = '/home/ssm-user/Paletta/paletta_code/paletta_project/orders' 