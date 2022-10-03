from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма создания нового поста и редактирования."""

    class Meta:
        model = Post

        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """Форма создания нового комментария."""
    class Meta:
        model = Comment

        fields = ('text',)
