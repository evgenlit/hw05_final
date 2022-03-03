import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import ImageFieldFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User
from ..views import POSTS_COUNT

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.author = User.objects.create_user(username='author_user2')

        cls.group = Group.objects.create(
            title='Новая группа 2',
            slug='new-group-2',
            description='Это новая группа 2'
        )

        cls.group_second = Group.objects.create(
            title='Новая группа 3',
            slug='new-group-3',
            description='Это новая группа 3'
        )

        cls.post = Post.objects.create(
            text='Текст поста 2',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.templates_pages_names = {
            'index': {
                'name': 'posts:index',
                'template': 'posts/index.html',
                'kwargs': None
            },
            'group_list': {
                'name': 'posts:group_list',
                'template': 'posts/group_list.html',
                'kwargs': {'slug': PostViewTests.group.slug}
            },
            'group_list_second': {
                'name': 'posts:group_list',
                'template': 'posts/group_list.html',
                'kwargs': {'slug': PostViewTests.group_second.slug}
            },
            'profile': {
                'name': 'posts:profile',
                'template': 'posts/profile.html',
                'kwargs': {'username': PostViewTests.author.username}
            },
            'post_detail': {
                'name': 'posts:post_detail',
                'template': 'posts/post_detail.html',
                'kwargs': {'post_id': PostViewTests.post.id}
            },
            'post_edit': {
                'name': 'posts:post_edit',
                'template': 'posts/create_post.html',
                'kwargs': {'post_id': PostViewTests.post.id}
            },
            'post_create': {
                'name': 'posts:post_create',
                'template': 'posts/create_post.html',
                'kwargs': None
            },
        }

    def check_context(self, data):
        self.assertEqual(data['text'], PostViewTests.post.text)
        self.assertEqual(data['author'], PostViewTests.author)
        self.assertEqual(data['group'], PostViewTests.group)
        self.assertIsInstance(data['image'], ImageFieldFile)

    def check_form_fields(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def get_revers_name(self, name):
        template = self.templates_pages_names[name]['name']
        kwargs = self.templates_pages_names[name]['kwargs']
        reverse_name = reverse(template, kwargs=kwargs)
        return str(reverse_name)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for name, attr in self.templates_pages_names.items():
            reverse_name = reverse(attr['name'], kwargs=attr['kwargs'])
            response = self.authorized_client.get(reverse_name)
            self.assertTemplateUsed(response, attr['template'])

    def test_index_page_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        reverse_name = self.get_revers_name('index')
        response = self.authorized_client.get(reverse_name)

        self.assertIn('page_obj', response.context)

        first_object = response.context['page_obj'][0]
        text = first_object.text
        author = first_object.author
        group = first_object.group
        image = first_object.image

        data = {
            "text": text,
            'author': author,
            'group': group,
            'image': image
        }

        self.check_context(data)

    def test_group_list_page_context(self):
        """Шаблон posts/group_list.html сформирован с правильным контекстом."""
        reverse_name = self.get_revers_name('group_list')
        response = self.authorized_client.get(reverse_name)

        self.assertIn('page_obj', response.context)

        text = response.context['page_obj'][0].text
        author = response.context['page_obj'][0].author
        group = response.context['group']
        image = response.context['page_obj'][0].image

        data = {
            "text": text,
            'author': author,
            'group': group,
            'image': image
        }

        self.check_context(data)

    def test_post_not_in_other_group(self):
        """Проверка, что пост не попал в другую группу."""
        reverse_name = self.get_revers_name('group_list_second')
        response = self.authorized_client.get(reverse_name)

        self.assertNotIn(PostViewTests.post, response.context['page_obj'])

    def test_profile_page_context(self):
        """Шаблон posts/profile.html сформирован с правильным контекстом."""
        reverse_name = self.get_revers_name('profile')
        response = self.authorized_client.get(reverse_name)

        self.assertIn('page_obj', response.context)

        author = response.context['author']
        text = response.context['page_obj'][0].text
        group = response.context['page_obj'][0].group
        image = response.context['page_obj'][0].image

        data = {
            "text": text,
            'author': author,
            'group': group,
            'image': image
        }

        self.check_context(data)

    def test_post_detail_page_context(self):
        """Шаблон posts/post_detail.html
           сформирован с правильным контекстом.
        """
        reverse_name = self.get_revers_name('post_detail')
        response = self.authorized_client.get(reverse_name)

        text_from_context = response.context.get('post').text
        text_from_created_post = PostViewTests.post.text
        author_from_context = response.context.get('post').author
        author_from_created_post = PostViewTests.post.author
        group_from_context = response.context.get('post').group
        group_from_created_post = PostViewTests.post.group
        image_from_context = response.context.get('post').image
        image_from_created_post = PostViewTests.post.image

        self.assertEqual(text_from_context, text_from_created_post)
        self.assertEqual(author_from_context, author_from_created_post)
        self.assertEqual(group_from_context, group_from_created_post)
        self.assertEqual(image_from_context, image_from_created_post)

    def test_create_post_page_show_correct_context(self):
        """Шаблон posts/create_post.html
           сформирован с правильным контекстом (создание поста).
        """
        reverse_name = self.get_revers_name('post_create')
        response = self.authorized_client.get(reverse_name)
        form = response.context.get('form')

        self.assertIsInstance(form, PostForm)

        self.check_form_fields(response)

        self.assertIsNone(response.context.get('is_edit'))

    def test_post_edit_page_show_correct_context(self):
        """Шаблон posts/create_post.html
           сформирован с правильным контекстом (редактирование поста).
        """
        reverse_name = self.get_revers_name('post_edit')
        response = self.authorized_client.get(reverse_name)
        form = response.context.get('form')

        self.assertIsInstance(form, PostForm)

        self.check_form_fields(response)

        self.assertTrue(response.context.get('is_edit'))


class PostPaginatorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author_user')

        cls.group = Group.objects.create(
            title='Новая группа',
            slug='new-group',
            description='Это новая группа'
        )

        cls.number_of_posts = 13
        posts = (Post(
            text='Текст поста %s' % i,
            author=cls.author,
            group=cls.group) for i in range(
                PostPaginatorViewTests.number_of_posts)
        )
        Post.objects.bulk_create(posts, PostPaginatorViewTests.number_of_posts)

    def test_index_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице index равно 10."""
        response = self.client.get(reverse('posts:index'))
        posts_count_on_first_page = len(response.context['page_obj'])
        self.assertEqual(posts_count_on_first_page, POSTS_COUNT)

    def test_index_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице index равно 3."""
        response = self.client.get(reverse('posts:index'), {'page': 2})
        posts_count_from_context = len(response.context['page_obj'])
        posts_on_second_page = Post.objects.count() % POSTS_COUNT
        self.assertEqual(posts_count_from_context, posts_on_second_page)

    def test_group_list_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице
           posts/group_list.html равно 10.
        """
        response = self.client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostPaginatorViewTests.group.slug}))
        posts_count_on_first_page = len(response.context['page_obj'])
        self.assertEqual(posts_count_on_first_page, POSTS_COUNT)

    def test_group_list_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице
           posts/group_list.html равно 3.
        """
        response = self.client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostPaginatorViewTests.group.slug}), {'page': 2})
        posts_count_from_context = len(response.context['page_obj'])
        posts_on_second_page = Post.objects.count() % POSTS_COUNT
        self.assertEqual(posts_count_from_context, posts_on_second_page)

    def test_profile_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице
           posts/profile.html равно 10.
        """
        response = self.client.get(
            reverse('posts:profile', kwargs={
                'username': PostPaginatorViewTests.author.username}))
        posts_count_on_first_page = len(response.context['page_obj'])
        self.assertEqual(posts_count_on_first_page, POSTS_COUNT)

    def test_profile_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице
           posts/profile.html равно 3.
        """
        response = self.client.get(
            reverse('posts:profile', kwargs={
                'username': PostPaginatorViewTests.author.username}
            ), {'page': 2})
        posts_count_from_context = len(response.context['page_obj'])
        posts_on_second_page = Post.objects.count() % POSTS_COUNT
        self.assertEqual(posts_count_from_context, posts_on_second_page)
