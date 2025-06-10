from django.apps import AppConfig


class LibrariesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'libraries'

    def ready(self):
        """
        Import signals when the app is ready.
        """
        import libraries.private_category
