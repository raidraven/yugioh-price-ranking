import sys
from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cards'
    verbose_name = '遊戯王カード'

    def ready(self):
        # Only start scheduler in the main process (not during migrations/management commands)
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            from .scheduler import start
            start()
