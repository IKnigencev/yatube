from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CreatForm


class SignUp(CreateView):
    """Страница регистрации."""
    form_class = CreatForm

    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'
