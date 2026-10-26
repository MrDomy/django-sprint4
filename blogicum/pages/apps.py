"""Pages application configuration."""
from django.apps import AppConfig


class PagesConfig(AppConfig):
    """Configuration for Pages application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'
    verbose_name = 'Страницы'
