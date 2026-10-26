"""Views for pages application."""
from django.shortcuts import render
from django.views.generic import TemplateView


class AboutView(TemplateView):
    """View for about page."""

    template_name = 'pages/about.html'


class RulesView(TemplateView):
    """View for rules page."""

    template_name = 'pages/rules.html'


def csrf_failure(request, reason=''):
    """Custom 403 CSRF failure handler."""
    return render(request, 'pages/403csrf.html', status=403)


def page_not_found(request, exception):
    """Custom 404 error handler."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Custom 500 error handler."""
    return render(request, 'pages/500.html', status=500)
