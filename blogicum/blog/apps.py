"""Blog application configuration."""
from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Configuration for Blog application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'Блог'
