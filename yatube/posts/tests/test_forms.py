import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Group, Post, User, Comment
from .const_for_test import (
    TEST_AUTHOR, ANOTHER_AUTHOR, TEST_GROUP, TEST_SLUG, GROUP,
    TEST_DESCRIPTION, TEST_ANOTHER_GROUP, TEST_ANOTHER_DESCRIPTION,
    TEST_ANOTHER_TEXT, TEST_ANOTHER_SLUG, TEST_TEXT, TEST_GIF, TEXT,
    USERNAME_ROUTE, EDIT_ROUTE, POST_CREATE_ROUTE, DETAIL_ROUTE,
    CREATE_REDIRECT_URL, IMAGE, COMMENT_ROUTE, LOGIN_ROUTE
)


POST_CREATE_URL = reverse(POST_CREATE_ROUTE)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
LOGIN_URL = reverse(LOGIN_ROUTE)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_AUTHOR)
        cls.author = User.objects.create_user(username=ANOTHER_AUTHOR)
        cls.group = Group.objects.create(
            title=TEST_GROUP,
            slug=TEST_SLUG,
            description=TEST_DESCRIPTION
        )
        cls.yet_another_group = Group.objects.create(
            title=TEST_ANOTHER_GROUP,
            slug=TEST_ANOTHER_SLUG,
            description=TEST_ANOTHER_DESCRIPTION,
        )
        cls.form = PostForm()

        cls.original_post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text=TEST_TEXT)

        cls.USERNAME_URL = reverse(
            USERNAME_ROUTE,
            kwargs={'username': cls.author}
        )
        cls.DETAIL_URL = reverse(
            DETAIL_ROUTE,
            kwargs={'post_id': cls.original_post.id}
        )
        cls.EDIT_URL = reverse(
            EDIT_ROUTE,
            kwargs={'post_id': cls.original_post.id}
        )
        cls.COMMENT_URL = reverse(
            COMMENT_ROUTE,
            kwargs={'post_id': cls.original_post.id}
        )

    def setUp(self):
        self.guest_client = Client()
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_post_create_form(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = TEST_GIF
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            GROUP: self.group.pk,
            TEXT: TEST_TEXT,
            IMAGE: uploaded,
        }
        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.latest('id')
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(
            response, self.USERNAME_URL
        )
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.text, form_data[TEXT])
        self.assertEqual(post.group.pk, form_data[GROUP])
        self.assertTrue(post.image)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_post_edit_form(self):
        """Валидная форма при редактировании меняет связанный пост."""
        form_data = {
            GROUP: self.yet_another_group.pk,
            TEXT: TEST_TEXT
        }
        response = self.authorized_client.post(
            self.EDIT_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.latest('id')
        self.assertRedirects(response, self.DETAIL_URL,)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.text, form_data[TEXT])
        self.assertEqual(post.group.pk, form_data[GROUP])

    def test_post_create_by_guest_form(self):
        """Гость не может создать запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            GROUP: self.group.pk,
            TEXT: TEST_ANOTHER_TEXT,
        }
        response = self.guest_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data[TEXT],
                group=form_data[GROUP],
            ).exists()
        )
        self.assertRedirects(
            response,
            CREATE_REDIRECT_URL
        )

    def test_post_edit_by_guest_form(self):
        """Гость не может отредактировать запись в Post."""
        form_data = {
            TEXT: TEST_ANOTHER_TEXT,
            GROUP: self.yet_another_group.pk,
        }
        self.guest_client.post(
            self.EDIT_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.latest('id')
        self.assertEqual(self.original_post.text, post.text)
        self.assertEqual(self.original_post.group.pk, post.group.pk)
        self.assertEqual(self.original_post.author, post.author)

    def test_post_edit_by_different_user_form(self):
        """Пользователь не может отредактировать чужую запись в Post."""
        form_data = {
            TEXT: TEST_ANOTHER_TEXT,
            GROUP: self.yet_another_group.pk,
        }
        self.user_client.post(
            self.EDIT_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.latest('id')
        self.assertEqual(post.author, self.original_post.author)
        self.assertEqual(post.text, self.original_post.text)
        self.assertEqual(post.group.pk, self.original_post.group.pk)

    def test_create_comment(self):
        """Добавление комментария авторизованным пользователем."""
        comments_count = Comment.objects.count()
        comment_dic = {
            TEXT: TEST_TEXT,
        }
        response = self.authorized_client.post(
            self.COMMENT_URL,
            data=comment_dic,
            follow=True
        )
        self.assertRedirects(response, self.DETAIL_URL)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
    
    def test_add_comment_by_not_authorized_client(self):
        """Неавторизованный пользователь не может создать комментарий,
        происходит редирект на страницу авторизации."""
        comments_count = Comment.objects.count()
        comment_dic = {
            TEXT: TEST_TEXT
        }
        response = self.guest_client.post(
            self.COMMENT_URL,
            data=comment_dic,
            follow=True
        )
        redirect_address = LOGIN_URL + '?next=' + self.COMMENT_URL

        self.assertRedirects(response, redirect_address)
        self.assertEqual(Comment.objects.count(), comments_count)
