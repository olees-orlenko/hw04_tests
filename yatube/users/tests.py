from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from http import HTTPStatus

User = get_user_model()


class UsersPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_signup_url_exists_at_desired_location(self):
        response = self.guest_client.get('/users/signup/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_logout_url_exists_at_desired_location(self):
        response = self.guest_client.get('/users/logout/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_login_url_exists_at_desired_location(self):
        response = self.guest_client.get('/users/login/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'users/signup.html': '/auth/signup/',
            'users/logged_out.html': '/auth/logout/',
            'users/login.html': '/auth/login/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)


class UsersPagesViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_signup_accessible_by_name(self):
        response = self.guest_client.get(reverse('users:signup'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_accessible_by_name(self):
        response = self.guest_client.get(reverse('users:login'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_accessible_by_name(self):
        response = self.guest_client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_uses_correct_template(self):
        templates_users_names = {
            'users/signup.html': reverse('users:signup'),
            'users/logged_out.html': reverse('users:logout'),
            'users/login.html': reverse('users:login'),
        }
        for template, reverse_name in templates_users_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_signup_show_correct_context(self):
        response = self.guest_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
