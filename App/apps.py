from django.apps import AppConfig


class SupplyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'App'

    def ready(self):
        import App.signals
