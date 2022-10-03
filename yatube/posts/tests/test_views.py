from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Group, Post, User, Follow


class TestViews(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.user = User.objects.create_user(username='Testuser')
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.another_author = User.objects.create_user(username='AnotherAuthor')
        cls.group = Group.objects.create(
            title='Тест',
            slug='testslug',
            description='TestGroup'
        )
        Group.objects.create(
            title='Тест',
            slug='test_slug',
            description='TestGroup'
        )
        objs = [
            Post(
                text='Тестовый текст',
                author=TestViews.user,
                group=TestViews.group)
            for e in range(13)
        ]
        Post.objects.bulk_create(objs)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(TestViews.user)
        self.authorized_client_another = Client()
        self.authorized_client_another.force_login(TestViews.another_author)
        self.before_follow = Follow.objects.filter(
            user=TestViews.user).count()
        self.response_follow = self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TestViews.author.username}),
            follow=True
        )
        self.template_url = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'testslug'}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': TestViews.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': TestViews.user.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': TestViews.user.id}
            ): 'posts/create_post.html'
        }

    def test_follow_index(self):
        """Тестирование index_follow.

        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.
        """
        post = Post.objects.create(
            text='ididi',
            author=TestViews.author
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )

        last_post_follow = response.context['page_obj'].object_list[0]
        self.assertEqual(post, last_post_follow)

        response_another_user = self.authorized_client_another.get(
            reverse('posts:follow_index')
        )
        last_post_unfollow = response_another_user.context[
            'page_obj'
        ].object_list
        self.assertEqual(len(last_post_unfollow), 0)

    def test_follow_and_unfollow(self):
        """Тестирование follow и unfollow.

        Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок
        """
        self.assertEqual(
            Follow.objects.filter(user=TestViews.user).count(),
            self.before_follow + 1
        )
        response_unfollow = self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': TestViews.author.username})
        )
        self.assertEqual(
            Follow.objects.filter(user=TestViews.user).count(),
            self.before_follow
        )
        address_dict = {
            self.response_follow: reverse(
                'posts:profile',
                kwargs={'username': TestViews.author.username}
            ),
            response_unfollow: reverse(
                'posts:profile',
                kwargs={'username': TestViews.author.username}
            )
        }
        for respon, redir in address_dict.items():
            with self.subTest(address=redir):
                self.assertRedirects(respon, redir)

    def test_cahce_index(self):
        """Тестирование эширования главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='TestPost',
            author=TestViews.user
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_namespace_and_name_pattern(self):
        """URL-адрес использует соответствующий шаблон."""

        for reverse_name, template in self.template_url.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_paginator_on_pages(self):
        """Тестирование пагинатора на стрицах: index, group_list, profile."""

        url_for_page = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'testslug'}),
            reverse(
                'posts:profile',
                kwargs={'username': TestViews.user.username})
        }

        for reverse_name in url_for_page:
            with self.subTest(address=reverse_name):
                response = self.authorized_client.get(reverse_name)
                response_page_2 = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 10)
                self.assertEqual(len(response_page_2.context['page_obj']), 3)
