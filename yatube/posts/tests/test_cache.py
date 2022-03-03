from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class PostCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='auth_user')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCacheTests.author)

        self.templates_pages_names = {
            'index': {
                'name': 'posts:index',
                'template': 'posts/index.html',
                'kwargs': None
            }
        }

    def get_revers_name(self, name):
        template = self.templates_pages_names[name]['name']
        kwargs = self.templates_pages_names[name]['kwargs']
        reverse_name = reverse(template, kwargs=kwargs)
        return str(reverse_name)

    def test_index_page_with_cache(self):
        """Проверка отображения главной страницы
           с использованием кеша."""
        post = Post.objects.create(
            text='Пост для проверки кеша',
            author=PostCacheTests.author,
        )
        reverse_name = self.get_revers_name('index')

        response_with_one_post = self.authorized_client.get(reverse_name)
        post.delete()
        response_after_del_post = self.authorized_client.get(reverse_name)

        self.assertEqual(
            response_with_one_post.content,
            response_after_del_post.content
        )

    def test_index_page_without_cache(self):
        """Проверка отображения главной страницы
           без использования кеша."""
        post = Post.objects.create(
            text='Пост для проверки кеша',
            author=PostCacheTests.author,
        )
        reverse_name = self.get_revers_name('index')

        response_with_one_post = self.authorized_client.get(reverse_name)
        post.delete()
        cache.clear()
        response_after_del_post = self.authorized_client.get(reverse_name)

        self.assertNotEqual(
            response_with_one_post.content,
            response_after_del_post.content
        )
