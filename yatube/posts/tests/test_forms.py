import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.forms import PostForm
from posts.models import Post, Comment
from posts.models import User, Group


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тест',
            slug='testslug',
            description='TestGroup'
        )
        cls.post = Post.objects.create(
            text='Текст для теста',
            author=FormsTest.user,
            group=FormsTest.group
        )
        cls.form = PostForm()
        obj = [
            Comment(
                post=FormsTest.post,
                author=FormsTest.user,
                text='TestComment')
            for e in range(13)
        ]
        Comment.objects.bulk_create(obj)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.form_data = {
            'text': 'Test Comment',
        }
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.post_id = FormsTest.post.id
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(FormsTest.user)

    def test_form_create_post(self):
        """Проверка создания нового поста."""
        count_before = Post.objects.count()

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Текст из формы',
            'group': FormsTest.group.id,
            'image': uploaded
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': FormsTest.user.username}))
        self.assertEqual(Post.objects.count(), count_before + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Текст из формы',
                author=FormsTest.user,
                image='posts/small.gif',
                group=FormsTest.group
            ).exists()
        )

    def test_form_post_edit(self):
        """Проверка что пост изменяется верно."""
        uploaded = SimpleUploadedFile(
            name='sma.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Измененный текст формы',
            'group': FormsTest.group.id,
            'image': uploaded
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post_id}))
        self.assertTrue(
            Post.objects.filter(
                id=self.post_id,
                text=form_data['text'],
                author=FormsTest.user,
                image='posts/sma.gif',
                group=FormsTest.group
            ).exists()
        )

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': FormsTest.user.id})
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_text_label(self):
        """Проверка текста verbose_name в форме."""
        text_label = FormsTest.form.fields['text'].label

        group_label = FormsTest.form.fields['group'].label

        self.assertEqual(text_label, 'Текст поста')
        self.assertEqual(group_label, 'Группа')

    def test_text_help_text(self):
        """Проверка текста help_text в форме."""
        text_help_text = FormsTest.form.fields['text'].help_text

        group_help_text = FormsTest.form.fields['group'].help_text

        self.assertEqual(text_help_text, 'Текст нового поста')
        self.assertEqual(
            group_help_text,
            'Группа, к которой будет относиться пост')

    def test_only_authorized_can_comments(self):

        response_guest = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': FormsTest.post.id}),
            data=self.form_data,
            follow=True
        )

        response_auth = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': FormsTest.post.id}),
            data=self.form_data,
            follow=True
        )

        self.assertRedirects(
            response_guest,
            f'/auth/login/?next=/posts/{FormsTest.post.id}/comment/'
        )
        self.assertEqual(response_auth.status_code, 200)

    def test_form_comment(self):

        before_comments = Comment.objects.filter(post=FormsTest.post).count()

        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': FormsTest.post.id}),
            data=self.form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': FormsTest.post.id}
            )
        )
        self.assertEqual(
            Comment.objects.filter(post=FormsTest.post).count(),
            before_comments + 1
        )
        self.assertTrue(
            Comment.objects.filter(
                post=FormsTest.post,
                text=self.form_data['text'],
                author=FormsTest.user
            ).exists()
        )
