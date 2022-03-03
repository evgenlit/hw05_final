from django.test import TestCase

from ..models import Group, Post, User


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
            text='Тестовый пост и не важно какой длины текст',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей
           корректно работает __str__.
        """
        self.assertEqual(str(self.post), PostModelTest.post.text[:15])
        self.assertEqual(str(self.group), PostModelTest.group.title)
