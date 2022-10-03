from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Group, Post, User


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.user = User.objects.create_user(username='testUser')

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=URLTests.user
        )

        Group.objects.create(
            title='TestGroup',
            slug='test',
            description='TestGroup'
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

        self.post_id = URLTests.user.id

        self.no_author = User.objects.create_user(username='noauthorTest')
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.no_author)

        self.authorized_client = Client()
        self.authorized_client.force_login(URLTests.user)
        self.template_url = {
            '/': 'posts/index.html',
            '/group/test/': 'posts/group_list.html',
            '/profile/testUser/': 'posts/profile.html',
            f'/posts/{self.post_id}/': 'posts/post_detail.html',
            f'/posts/{self.post_id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': ''
        }

    def test_all_page(self):
        """Тестируем все страницы для доступа."""

        for address in self.template_url.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                if address == '/unexisting_page/':
                    response = self.authorized_client.get(address)
                    self.assertEqual(response.status_code, 404)
                elif address == '/create/':
                    self.assertEqual(response.status_code, 302)
                elif address == f'/posts/{self.post_id}/edit/':
                    response = self.authorized_client_no_author.get(address)
                    self.assertEqual(response.status_code, 302)
                else:
                    self.assertEqual(response.status_code, 200)

    def test_url_use_correct_template(self):
        """Тестируем что страницы возвращают правильные шаблоны."""

        for address, template in self.template_url.items():
            with self.subTest(address=address):
                if address == '/unexisting_page/':
                    response = self.authorized_client.get(address)
                    self.assertEqual(response.status_code, 404)
                else:
                    response = self.authorized_client.get(address)
                    self.assertTemplateUsed(response, template)
