from django.db import models
from django.contrib.auth import get_user_model

from core.models import CreatedModel
from .validators import validate_not_empty


User = get_user_model()


class Group(models.Model):
    """База данных групп.

    Хранит поля: title, slug, description.
    """

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    description = models.TextField()

    def __str__(self):
        return self.title


class Post(CreatedModel):
    """База данных постов.

    Хранит поля: text, pub_date, author, group.
    Связана с базой данных Group по полю group.
    """

    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Текст нового поста',
        validators=[validate_not_empty])

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        help_text='Группа, к которой будет относиться пост',
        verbose_name='Группа'
    )

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    text = models.TextField()

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        ordering = ('-author',)
        constraints = [
            models.UniqueConstraint(
                name='unique_following',
                fields=['user', 'author'])
        ]

    def __str__(self):
        return self.user.username
