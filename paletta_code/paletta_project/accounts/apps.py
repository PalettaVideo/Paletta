from django.apps import AppConfig

class AccountsConfig(AppConfig):
    # default auto field for the accounts app
    default_auto_field = 'django.db.models.BigAutoField'
    # name of the accounts app (used in the Django admin panel)
    name = 'accounts'
