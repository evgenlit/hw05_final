import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='test_user')

        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Новая тестовая группа'
        )

        post_text = 'Тест пост'
        cls.post = Post.objects.create(
            text=post_text,
            author=cls.author,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_test.gif',
            content=small_gif,
            content_type='image/gif'
        )

        post_text = 'Тестовый пост из формы'
        form_data = {
            'text': post_text,
            'group': PostFormTests.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': PostFormTests.author.username}))

        self.assertEqual(Post.objects.count(), posts_count + 1)

        last_post = Post.objects.order_by('-id')[:1].get()

        self.assertEqual(
            last_post.text,
            post_text)
        self.assertEqual(
            last_post.group.slug,
            PostFormTests.group.slug)
        self.assertEqual(
            last_post.author.username,
            PostFormTests.author.username)
        self.assertEqual(
            last_post.image,
            'posts/' + uploaded.name)

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        post_text = 'Новое значение для редактируемого поста!'

        form_data = {
            'text': post_text,
            'group': PostFormTests.group.pk
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostFormTests.post.pk}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': PostFormTests.post.pk}))

        self.assertEqual(Post.objects.count(), posts_count)

        editable_post = Post.objects.get(pk=PostFormTests.post.pk)

        self.assertEqual(editable_post.text, post_text)

    def test_auth_user_can_create_comments_for_posts(self):
        """Только авторизованные пользоваетли
           могут оставлять комментарии к постам."""
        comments_count = Comment.objects.count()
        comment_text = 'Тестовый комментарий'
        form_data = {
            'text': comment_text
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': PostFormTests.post.pk}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': PostFormTests.post.pk}))

        self.assertEqual(Comment.objects.count(), comments_count + 1)

        last_comment = Comment.objects.order_by('-id')[:1].get()

        self.assertEqual(
            last_comment.text,
            comment_text)
        self.assertEqual(
            last_comment.author.username,
            PostFormTests.author.username)

        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostFormTests.post.id})
        )

        text_from_context = response.context.get('post').text
        text_from_created_post = PostFormTests.post.text
        author_from_context = response.context.get('post').author
        author_from_created_post = PostFormTests.post.author
        comment = response.context['comments'][0]

        self.assertEqual(text_from_context, text_from_created_post)
        self.assertEqual(author_from_context, author_from_created_post)
        self.assertEqual(comment, last_comment)
