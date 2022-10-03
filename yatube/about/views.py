from django.views.generic import TemplateView


class AboutAuthorView(TemplateView):
    """Страница информации об авторе."""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Страница информации об технологиях использованых в проекте."""
    template_name = 'about/tech.html'
