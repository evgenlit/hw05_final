from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth_user')

        cls.author = User.objects.create_user(username='author_user')

        cls.group = Group.objects.create(
            title='Новая группа 1',
            slug='new-group-1',
            description='Это новая группа 1'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст поста 1',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

        self.public_url_names = [
            'index',
            'group_list',
            'profile',
            'post_detail',
        ]

        self.private_url_names = [
            'post_edit',
            'post_create'
        ]

        self.unexist_url_names = ['unexisting_page']

        self.templates_pages_names = {
            'index': {
                'url': '/',
                'template': 'posts/index.html',
                'status': HTTPStatus.OK
            },
            'group_list': {
                'url': f'/group/{self.group.slug}/',
                'template': 'posts/group_list.html',
                'status': HTTPStatus.OK
            },
            'profile': {
                'url': f'/profile/{self.author.username}/',
                'template': 'posts/profile.html',
                'status': HTTPStatus.OK
            },
            'post_detail': {
                'url': f'/posts/{self.post.id}/',
                'template': 'posts/post_detail.html',
                'status': HTTPStatus.OK
            },
            'post_edit': {
                'url': f'/posts/{self.post.id}/edit/',
                'template': 'posts/create_post.html',
                'status': HTTPStatus.OK
            },
            'post_create': {
                'url': '/create/',
                'template': 'posts/create_post.html',
                'status': HTTPStatus.OK
            },
            'unexisting_page': {
                'url': '/unexisting_page/',
                'template': None,
                'status': HTTPStatus.NOT_FOUND
            }
        }

    def get_url_name(self, name):
        url = self.templates_pages_names[name]['url']
        return str(url)

    def test_public_url_names_correct_response_code(self):
        """Проверяем доступность URL-адресов для любого пользователя."""
        for url in self.public_url_names:
            address = self.templates_pages_names[url]['url']
            status = self.templates_pages_names[url]['status']
            response = self.client.get(address)
            self.assertEqual(response.status_code, status)

        for url in self.unexist_url_names:
            address = self.templates_pages_names[url]['url']
            status = self.templates_pages_names[url]['status']
            response = self.client.get(address)
            self.assertEqual(response.status_code, status)

    def test_posts_edit_url_exists_for_author(self):
        """Страница /posts/<post_id>/edit/ доступна автору поста."""
        url = self.get_url_name('post_edit')
        response_auth_author = self.authorized_client_author.get(url)
        self.assertEqual(response_auth_author.status_code, HTTPStatus.OK)

    def test_posts_edit_redirect_for_non_author(self):
        """Страница /posts/<post_id>/edit/ отдаёт редирект
           авторизованному пользователю (не автору).
        """
        url = self.get_url_name('post_edit')
        response_auth_user = self.authorized_client.get(url, follow=True)
        self.assertRedirects(response_auth_user, f'/posts/{self.post.id}/')

    def test_create_page_url_exists_for_auth_user(self):
        """Страница /create/ доступна авторизованным пользователям."""
        url = self.get_url_name('post_create')
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_redirect_for_quest_user(self):
        """Страница /create/ отдаёт редирект
           не авторизованному пользователю.
        """
        url = self.get_url_name('post_create')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_public_urls_uses_correct_template(self):
        """Общедоступный URL-адрес использует соответствующий шаблон."""
        for url in self.public_url_names:
            address = self.templates_pages_names[url]['url']
            template = self.templates_pages_names[url]['template']
            response = self.client.get(address)
            self.assertTemplateUsed(response, template)

    def test_private_urls_uses_correct_template(self):
        """Приватный URL-адрес использует соответствующий шаблон."""
        for url in self.private_url_names:
            address = self.templates_pages_names[url]['url']
            template = self.templates_pages_names[url]['template']
            response = self.authorized_client_author.get(address)
            self.assertTemplateUsed(response, template)
