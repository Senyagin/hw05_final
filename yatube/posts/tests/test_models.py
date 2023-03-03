from django.test import TestCase

from ..models import Group, Post, Comment, Follow, User, SLICE_TEXT
from .const_for_test import (
    TEST_AUTHOR, TEST_GROUP, TEST_SLUG, TEST_DESCRIPTION, TEST_TEXT,
    ANOTHER_AUTHOR, TEST_ANOTHER_TEXT
)


class PostModelTest(TestCase):
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
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.second_user,
            text=TEST_ANOTHER_TEXT
        )
        cls.follow = Follow.objects.create(
            user=cls.second_user,
            author=cls.user,
        )
        cls.object_names = {
            PostModelTest.post: PostModelTest.post.text[:SLICE_TEXT],
            PostModelTest.group: PostModelTest.group.title,
            PostModelTest.comment: PostModelTest.comment.text[:SLICE_TEXT],
        }

    def test_models_have_correct_object_names_post_group(self):
        """Проверяем, что у моделей корректно работает __str__."""
        for object_name, field_name in self.object_names.items():
            with self.subTest(object_name=object_name):
                self.assertEqual(str(object_name), field_name)

    def test_models_have_correct_objects_names_group(self):
        """Проверяем, что у моделей корректно работает __str__."""
        follow = PostModelTest.follow
        expected_user = follow.user.username
        expected_author = follow.author.username
        self.assertEqual(
            f'{expected_user} подписан на {expected_author}',
            str(follow)
        )
