import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User
from posts.tests.constants import (
    GROUP_DESCRIPTION,
    GROUP_SLUG,
    GROUP_TITLE,
    POST_CREATE_URL_NAME,
    POST_DETAIL_URL_NAME,
    PROFILE_URL_NAME,
    POST_EDIT_URL_NAME,
    POST_EDIT_TEXT,
    POST_TEXT,
    USER_USERNAME,
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=USER_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.form_data = {'text': POST_TEXT, 'group': cls.group.id}
        cls.form_data_edit = {'text': POST_EDIT_TEXT, 'group': cls.group.id}
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text=POST_TEXT,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """При отправке валидной формы создаётся новая запись."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.form_data = {
            'title': GROUP_TITLE,
            'text': POST_TEXT,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse(POST_CREATE_URL_NAME), data=self.form_data, follow=True
        )
        self.assertRedirects(
            response, reverse(PROFILE_URL_NAME, kwargs={
                              'username': self.post.author})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text=POST_TEXT).exists())
        self.assertTrue(Post.objects.filter(group=self.group).exists())
        self.assertTrue(Post.objects.filter(author=self.author).exists())
        self.assertTrue(Post.objects.filter(image='posts/small.gif').exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """При отправке валидной формы редактирования изменяется пост."""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse(POST_EDIT_URL_NAME, kwargs={'post_id': self.post.id}),
            data=self.form_data_edit,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(POST_DETAIL_URL_NAME,
                              kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text=POST_EDIT_TEXT).exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)
