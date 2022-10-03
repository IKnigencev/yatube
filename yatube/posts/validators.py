"""Файл с функциями для валидации полей модели."""
from django import forms


def validate_not_empty(value):
    """Валидация формы, заполнено ли поле."""

    if len(value) == 0:

        raise forms.ValidationError(
            'А кто поле будет заполнять, Пушкин?',
            params={'value': value},
        )
