from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from posts.models import Group, Post, User
from .const_for_test import (
    TEST_AUTHOR, ANOTHER_AUTHOR, TEST_GROUP, GROUP_LIST_ROUTE,
    TEST_SLUG, TEST_DESCRIPTION, TEST_TEXT, DETAIL_ROUTE, LOGIN_ROUTE,
    INDEX_ROUTE, USERNAME_ROUTE, EDIT_ROUTE, POST_CREATE_ROUTE,
    INDEX_TEMPLATE, GROUP_TEMPLATE, USERNAME_TEMPLATE,
    POST_DETAIL_TEMPLATE, POST_EDIT_TEMPLATE, POST_CREATE_TEMPLATE, UNKNOWN_URL,
    COMMENT_ROUTE, FOLLOW_ROUTE, PROFILE_FOLLOW_ROUTE, FOLLOW_TEMPLATE, UNKNOWN_TEMPLATE
)


INDEX_URL = reverse(INDEX_ROUTE)
POST_CREATE_URL = reverse(POST_CREATE_ROUTE)
LOGIN_URL = reverse(LOGIN_ROUTE)
FOLLOW_URL = reverse(FOLLOW_ROUTE)

class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_AUTHOR)
        cls.second_user = User.objects.create_user(username=ANOTHER_AUTHOR)
        cls.group = Group.objects.create(
            title=TEST_GROUP,
            slug=TEST_SLUG,
            description=TEST_DESCRIPTION,
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text=TEST_TEXT,
        )

        cls.EDIT_REDIRECT_URL = f'/auth/login/?next=/posts/{cls.post.pk}/edit/'

        cls.GROUP_LIST_URL = reverse(
            GROUP_LIST_ROUTE,
            kwargs={'slug': cls.group.slug}
        )
        cls.USERNAME_URL = reverse(
            USERNAME_ROUTE,
            kwargs={'username': cls.user}
        )
        cls.DETAIL_URL = reverse(
            DETAIL_ROUTE,
            kwargs={'post_id': cls.post.id}
        )
        cls.EDIT_URL = reverse(
            EDIT_ROUTE,
            kwargs={'post_id': cls.post.id}
        )
        cls.COMMENT_URL = reverse(
            COMMENT_ROUTE,
            kwargs={'post_id': cls.post.id}
        )
        cls.PROFILE_FOLLOW_URL = reverse(
            PROFILE_FOLLOW_ROUTE,
            kwargs={'username': cls.user}
        )

        cls.templates_redirect_urls = {
            cls.EDIT_URL: LOGIN_URL + '?next=' + cls.EDIT_URL,
            POST_CREATE_URL: LOGIN_URL + '?next=' + POST_CREATE_URL
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_second_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_second_client.force_login(self.second_user)

    def test_names_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        template_urls_names = {
            INDEX_URL: INDEX_TEMPLATE,
            self.GROUP_LIST_URL: GROUP_TEMPLATE,
            self.USERNAME_URL: USERNAME_TEMPLATE,
            self.DETAIL_URL: POST_DETAIL_TEMPLATE,
            self.EDIT_URL: POST_EDIT_TEMPLATE,
            POST_CREATE_URL: POST_CREATE_TEMPLATE,
        }
        for adress, template in template_urls_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_access_for_all(self):
        """Доступ неавторизированного пользователя к страницам"""
        pages_all = (
            INDEX_URL,
            self.GROUP_LIST_URL,
            self.USERNAME_URL,
            self.DETAIL_URL,
        )
        for page in pages_all:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'недоступна страница {page}'
                )

        response = self.guest_client.get(UNKNOWN_URL)
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            'внезапно стала доступна страница unknown'
        )
        self.assertTemplateUsed(response, UNKNOWN_TEMPLATE)
    def test_access_for_autorized(self):
        """Доступ авторизированного пользователя к страницам"""
        response = self.authorized_client.get(POST_CREATE_URL)
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'страница create недоступна '
            + 'авторизированному пользователю'
        )

        response = self.authorized_client.get(self.EDIT_URL)
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'страница редактирования недоступна автору'
        )

        response = self.authorized_second_client.get(
            self.EDIT_URL,
            follow=True
        )
        self.assertRedirects(response, self.DETAIL_URL)

    def test_private_urls_redirect_guest(self):
        """Неавторизованный пользователь перенаправляется на другую страницу"""
        for address, redirect_address in self.templates_redirect_urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_add_comment_by_authorized_client(self):
        """Добавление комментария доступно авторизованному пользователю ."""
        response = self.authorized_second_client.get(self.COMMENT_URL, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, self.DETAIL_URL)

    def test_add_comment_by_not_authorized_client(self):
        "Неавторизованный пользователь не может добавить комментарий."
        address = self.COMMENT_URL
        redirect_address = LOGIN_URL + '?next=' + self.COMMENT_URL
        response = self.guest_client.get(address, follow=True)
        self.assertRedirects(response, redirect_address)

    def test_follow_index_url_correct_template(self):
        """Адрес follow_index доступен авторизованному пользователю
        и используют соответствующий шаблон."""
        address = FOLLOW_URL
        response = self.authorized_client.get(address)
        self.assertTemplateUsed(response, FOLLOW_TEMPLATE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_url_redirect_guest(self):
        """Адрес follow не доступен для неавторизованных пользователей,
         ведет на редиректную страницу"""
        address = self.PROFILE_FOLLOW_URL
        redirect_address = LOGIN_URL + '?next=' + self.PROFILE_FOLLOW_URL
        response = self.guest_client.get(address, follow=True)
        self.assertRedirects(response, redirect_address)