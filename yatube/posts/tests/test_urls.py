from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User
from posts.tests.constants import (
    GROUP_DESCRIPTION,
    GROUP_LIST_TEMPLATE,
    GROUP_SLUG,
    GROUP_TITLE,
    INDEX_TEMPLATE,
    POST_CREATE_TEMPLATE,
    POST_DETAIL_TEMPLATE,
    PROFILE_TEMPLATE,
    POST_EDIT_TEMPLATE,
    POST_TEXT,
    USER_USERNAME,
)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=USER_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text=POST_TEXT,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_url_exists_at_desired_location(self):
        """Проверка доступности адресов."""
        pages_url = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.author}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, http_status in pages_url.items():
            with self.subTest(address=address):
                response = Client().get(address)
                self.assertEqual(response.status_code, http_status)

    def test_post_edit_url_exists_at_desired_location(self):
        """Проверка доступности адреса /posts/1/edit/."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_url_exists_at_desired_location(self):
        """Проверка доступности адреса /create/."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """Проверка шаблона для адресов."""
        templates_url_names = {
            '': INDEX_TEMPLATE,
            f'/group/{GROUP_SLUG}/': GROUP_LIST_TEMPLATE,
            f'/profile/{USER_USERNAME}/': PROFILE_TEMPLATE,
            f'/posts/{self.post.id}/': POST_DETAIL_TEMPLATE,
            f'/posts/{self.post.id}/edit/': POST_EDIT_TEMPLATE,
            '/create/': POST_CREATE_TEMPLATE,
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
