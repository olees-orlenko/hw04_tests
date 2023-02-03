from http import HTTPStatus

from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post, User
from posts.tests.constants import (
    COMMENT_TEXT,
    GROUP_DESCRIPTION,
    GROUP_LIST_TEMPLATE,
    GROUP_LIST_URL_NAME,
    GROUP_SLUG,
    GROUP_TITLE,
    HTTP404_HTML_TEMPLATE,
    INDEX_TEMPLATE,
    INDEX_URL_NAME,
    POST_CREATE_TEMPLATE,
    POST_CREATE_URL_NAME,
    POST_DETAIL_COMMENT_URL_NAME,
    POST_DETAIL_TEMPLATE,
    POST_DETAIL_URL_NAME,
    POST_FOLLOW_URL_NAME,
    PROFILE_TEMPLATE,
    PROFILE_URL_NAME,
    POST_EDIT_TEMPLATE,
    POST_EDIT_URL_NAME,
    POST_TEXT,
    USER_USERNAME,
)

QUANTITY = 10


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=USER_USERNAME)
        cls.user = User.objects.create_user(username='NoName')
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
        cls.comment = Comment.objects.create(
            author=cls.author,
            text=COMMENT_TEXT,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_error_page(self):
        """Страница 404 отдаёт кастомный шаблон."""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, HTTP404_HTML_TEMPLATE)

    def test_posts_uses_correct_template(self):
        """URL-адреса используют корректные шаблон."""
        templates_posts_names = {
            reverse(INDEX_URL_NAME): INDEX_TEMPLATE,
            reverse(GROUP_LIST_URL_NAME, kwargs={'slug': GROUP_SLUG}):
            GROUP_LIST_TEMPLATE,
            reverse(PROFILE_URL_NAME, kwargs={'username': USER_USERNAME}):
            PROFILE_TEMPLATE,
            reverse(POST_DETAIL_URL_NAME, kwargs={'post_id':
                                                  PostViewTests.post.id}):
            POST_DETAIL_TEMPLATE,
            reverse(POST_EDIT_URL_NAME, kwargs={'post_id': '1'}):
            POST_EDIT_TEMPLATE,
            reverse(POST_CREATE_URL_NAME): POST_CREATE_TEMPLATE,
        }
        for reverse_name, template in templates_posts_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_uses_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(INDEX_URL_NAME))
        expected = list(Post.objects.all())
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                GROUP_LIST_URL_NAME,
                kwargs={'slug': self.group.slug}
            )
        )
        expected = list(Post.objects.filter(group=self.group))
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(PROFILE_URL_NAME, kwargs={'username': self.post.author})
        )
        expected = list(Post.objects.filter(author_id=self.author.id))
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(POST_DETAIL_URL_NAME, kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)

    def test_post_create_show_correct_context(self):
        """Шаблон создания нового поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(POST_CREATE_URL_NAME))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, field_type in form_fields.items():
            with self.subTest(value=value, type=field_type):
                self.assertIsInstance(response.context['form'], PostForm)

    def test_post_edit_show_correct_context(self):
        """Шаблон редактирования поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(POST_EDIT_URL_NAME, kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_added_to_correct_pages(self):
        """Пост отображается на нужных страницах"""
        form_fields = {
            reverse(INDEX_URL_NAME): Post.objects.get(group=self.post.group),
            reverse(
                GROUP_LIST_URL_NAME, kwargs={'slug': self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                PROFILE_URL_NAME, kwargs={'username': self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_post_not_added_to_wrong_group(self):
        """Пост не попал в группу, для которой не был предназначен"""
        form_fields = {
            reverse(
                GROUP_LIST_URL_NAME, kwargs={'slug': self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)

    def test_comment_correct_context(self):
        """Комментарий появляется на странице поста"""
        comments_count = Comment.objects.count()
        form_data = {'text': COMMENT_TEXT}
        response = self.authorized_client.post(
            reverse(
                POST_DETAIL_COMMENT_URL_NAME,
                kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                POST_DETAIL_URL_NAME, kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(text=COMMENT_TEXT).exists())

    def test_cache_index(self):
        """Проверка работы кэша для index."""
        response = self.guest_client.get(reverse(INDEX_URL_NAME))
        response_1 = response.content
        Post.objects.get(id=1).delete()
        response2 = self.guest_client.get(reverse(INDEX_URL_NAME))
        response_2 = response2.content
        self.assertEqual(response_1, response_2)

    def test_follow_page(self):
        """Проверка подписки и отписки на автора"""
        response = self.authorized_client.get(reverse(POST_FOLLOW_URL_NAME))
        self.assertEqual(len(response.context['posts']), 0)
        count_follow = Follow.objects.count()
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.author).exists()
        )

        author = self.user
        not_follower = self.authorized_client.get(
            reverse(
                POST_FOLLOW_URL_NAME
            )
        )
        self.assertNotIn(self.post, not_follower.context['posts'])
        Follow.objects.all().delete()
        self.assertEqual(count_follow, 0)
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=author).exists()
        )


class PaginatorViewsTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username=USER_USERNAME)
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.group = Group.objects.create(title=GROUP_TITLE,
                                          slug=GROUP_SLUG)
        bulk_post: list = []
        for i in range(13):
            bulk_post.append(Post(text=f'POST_TEXT{i}',
                                  group=self.group,
                                  author=self.author))
        Post.objects.bulk_create(bulk_post)

    def test_correct_number_of_pages_contains(self):
        """Корректное количество постов на первых двух страницах шаблонов."""
        NUMBER_OF_POSTS_1ST_PAGE = 10
        NUMBER_OF_POSTS_2ND_PAGE = 3
        pages = (
            (1, NUMBER_OF_POSTS_1ST_PAGE),
            (2, NUMBER_OF_POSTS_2ND_PAGE)
        )
        pages_url = (
            (INDEX_URL_NAME, INDEX_TEMPLATE, None),
            (GROUP_LIST_URL_NAME, GROUP_LIST_TEMPLATE, (self.group.slug,)),
            (PROFILE_URL_NAME, PROFILE_TEMPLATE, (self.author,)),
        )
        for url, _, args in pages_url:
            for page_num, posts_count in pages:
                with self.subTest(url=url, page_num=page_num):
                    response = self.guest_client.get(
                        reverse(url, args=args),
                        {'page': page_num}
                    )
                    self.assertEqual(
                        len(response.context.get('page_obj').object_list),
                        posts_count
                    )
