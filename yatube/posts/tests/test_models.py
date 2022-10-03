from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        task_group = PostModelTest.group

        act_group = str(task_group)

        result_group = task_group.title

        self.assertEquals(
            act_group,
            result_group,
            'Не корректная работа метода __str__ Group')

        task_post = PostModelTest.post

        act_post = str(task_post)

        result_post = task_post.text[:15]

        self.assertEquals(
            act_post,
            result_post,
            'Не корректная работа метода __str__ Post')
