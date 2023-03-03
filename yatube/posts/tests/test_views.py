import shutil
import tempfile
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Group, Post, User, Follow
from .const_for_test import (
    TEST_AUTHOR, TEST_GROUP, TEST_SLUG, TEST_DESCRIPTION, TEST_TEXT,
    POSTS_COUNT, INDEX_ROUTE, USERNAME_ROUTE, EDIT_ROUTE, DETAIL_ROUTE,
    GROUP_LIST_ROUTE, POST_CREATE_ROUTE, TEST_GIF, PROFILE_FOLLOW_ROUTE,
    ANOTHER_AUTHOR, FOLLOW_ROUTE, UNFOLLOW_ROUTE
)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
INDEX_URL = reverse(INDEX_ROUTE)
POST_CREATE_URL = reverse(POST_CREATE_ROUTE)
FOLLOW_URL = reverse(FOLLOW_ROUTE)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_AUTHOR)
        cls.group = Group.objects.create(
            title=TEST_TEXT,
            slug=TEST_SLUG,
            description=TEST_DESCRIPTION,
        )

        cls.small_gif = TEST_GIF
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text=TEST_TEXT,
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.POST_DETAIL_URL = reverse(
            DETAIL_ROUTE,
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL = reverse(
            EDIT_ROUTE,
            kwargs={'post_id': cls.post.id}
        )
        cls.GROUP_LIST_URL = reverse(
            GROUP_LIST_ROUTE,
            kwargs={'slug': cls.group.slug}
        )
        cls.USERNAME_URL = reverse(
            USERNAME_ROUTE,
            kwargs={'username': cls.user.username}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(INDEX_URL)
        field = list(Post.objects.all()[:POSTS_COUNT])
        self.assertEqual(list(response.context['page_obj']), field)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get(self.GROUP_LIST_URL))
        field = list(Post.objects.select_related('group', 'author').filter(
            group=self.group)[:POSTS_COUNT])
        self.assertEqual(list(response.context['page_obj']), field)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.USERNAME_URL)
        field = list(Post.objects.filter(author_id='1')[:POSTS_COUNT])
        self.assertEqual(list(response.context['page_obj']), field)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.POST_DETAIL_URL)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(POST_CREATE_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.POST_EDIT_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_show_correct(self):
        """Созданный пост появлется на нужных страницах"""
        pages_names = (
            INDEX_URL,
            self.GROUP_LIST_URL,
            self.USERNAME_URL,
        )
        for page in pages_names:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertIn(self.post, response.context['page_obj'])

    def test_cache(self):
        """Проверка работы кэширования на главной странице."""
        test_post = Post.objects.create(
            group=self.group,
            author=self.user,
            text=TEST_TEXT
        )
        response_1 = self.guest_client.get(INDEX_URL)
        test_post.delete()
        response_2 = self.guest_client.get(INDEX_URL)
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.guest_client.get(INDEX_URL)
        self.assertNotEqual(response_1.content, response_3.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_AUTHOR)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title=TEST_GROUP,
            slug=TEST_SLUG,
            description=TEST_DESCRIPTION
        )

        cls.INDEX_URL = reverse(INDEX_ROUTE)
        cls.GROUP_LIST_URL = reverse(
            GROUP_LIST_ROUTE,
            kwargs={'slug': cls.group.slug}
        )
        cls.USERNAME_URL = reverse(
            USERNAME_ROUTE,
            kwargs={'username': cls.user.username}
        )

        posts = (Post(
            text=f'{TEST_TEXT} {i}',
            author=cls.user,
            group=cls.group) for i in range(13)
        )
        cls.post = Post.objects.bulk_create(posts)
        cls.second_page = Post.objects.count() % POSTS_COUNT

    def setUp(self):
        cache.clear()

    def test_context_with_paginator(self):
        """Тест контекст с Paginator."""
        first_page_posts = POSTS_COUNT
        total_posts = Post.objects.count()
        second_page_posts = total_posts - first_page_posts
        test_addresses = [
            INDEX_URL,
            self.GROUP_LIST_URL,
            self.USERNAME_URL
        ]
        page_numbers = {
            1: first_page_posts,
            2: second_page_posts
        }
        for address in test_addresses:
            with self.subTest(address=address):
                for page_number, page in page_numbers.items():
                    response = self.client.get(
                        address, {'page': page_number}
                    )
                    self.assertEqual(len(
                        response.context['page_obj']), page
                    )
      

class FollowTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username=TEST_AUTHOR)

        cls.PROFILE_FOLLOW_URL = reverse(
            PROFILE_FOLLOW_ROUTE,
            kwargs={'username': cls.user}
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_follow(self):
        """Авторизованный пользователь может подписаться
        на других пользователей."""
        author_user = User.objects.create_user(username=ANOTHER_AUTHOR)
        test_count_1 = Follow.objects.filter(
            user=FollowTests.user, author=author_user).count()
        self.authorized_client.get(
            reverse(
                PROFILE_FOLLOW_ROUTE,
                args=(author_user.username,)
            )
        )
        test_count_2 = Follow.objects.filter(
            user=FollowTests.user, author=author_user).count()
        self.assertEqual(test_count_1 + 1, test_count_2)

    def test_unfollow(self):
        """Авторизованный пользователь может
        отписаться от других пользователей."""
        author_user = User.objects.create_user(username=ANOTHER_AUTHOR)
        Follow.objects.create(user=FollowTests.user, author=author_user)
        test_count_1 = Follow.objects.filter(
            user=FollowTests.user, author=author_user).count()
        self.authorized_client.get(
            reverse(
                UNFOLLOW_ROUTE,
                args=(author_user.username,)
            )
        )
        test_count_2 = Follow.objects.filter(
            user=FollowTests.user, author=author_user).count()
        self.assertEqual(test_count_1 - 1, test_count_2)

    def test_subscription_feed(self):
        """Новая запись пользователя появляется
        в ленте тех, кто на него подписан."""
        author_user = User.objects.create_user(username=ANOTHER_AUTHOR)
        test_post = Post.objects.create(
            author=author_user,
            text=TEST_TEXT
        )
        Follow.objects.create(user=FollowTests.user, author=author_user)
        response = self.authorized_client.get(FOLLOW_URL)
        self.assertIn(test_post, response.context['page_obj'])

    def test_not_subscription_feed(self):
        """Новая запись пользователя не появляется
        в ленте тех, кто на него не подписан."""
        author_user = User.objects.create_user(username=ANOTHER_AUTHOR)
        test_post = Post.objects.create(
            author=author_user,
            text=TEST_TEXT
        )
        response = self.authorized_client.get(FOLLOW_URL)
        self.assertNotIn(test_post, response.context['page_obj'])

    def test_follow_yourself(self):
        """Авторизованный пользователь не может
        подписаться на самого себя."""
        author_user = User.objects.create_user(username=ANOTHER_AUTHOR)
        self.authorized_client.force_login(author_user)
        test_count_1 = Follow.objects.filter(
            user=author_user, author=author_user).count()
        self.authorized_client.get(self.PROFILE_FOLLOW_URL)
        test_count_2 = Follow.objects.filter(
            user=author_user, author=author_user).count()
        self.assertEqual(test_count_1, test_count_2)
