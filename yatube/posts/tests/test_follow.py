from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post, User


class FollowTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(
            username='author')
        cls.follower_user = User.objects.create_user(
            username='follower')
        cls.other_user = User.objects.create_user(
            username='other_user')

        cls.post = Post.objects.create(
            text='Новый пост автора',
            author=FollowTests.author,
        )

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(FollowTests.follower_user)

        self.other_user_client = Client()
        self.other_user_client.force_login(FollowTests.other_user)

    def test_auth_user_follow(self):
        """Авторизованный пользователь
           может подписываться на других пользователей.
        """
        self.follower_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': FollowTests.author}))

        follow = Follow.objects.get(user=FollowTests.follower_user)

        self.assertEqual(follow.user_id, FollowTests.follower_user.id)
        self.assertEqual(follow.author_id, FollowTests.author.id)

    def test_auth_user_unfollow(self):
        """Авторизованный пользователь
           может удалять авторов из подписок.
        """
        Follow.objects.create(
            user=FollowTests.follower_user,
            author=FollowTests.author,
        )

        self.follower_client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': FollowTests.author}))

        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 0)

    def test_user_can_view_new_author_posts(self):
        """Новая запись автора появляется в ленте тех,
           кто на него подписан.
        """
        self.follower_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': FollowTests.author}))

        response = self.follower_client.get(
            reverse('posts:follow_index'))
        post = response.context['page_obj'][0]

        self.assertEqual(post.text, FollowTests.post.text)
        self.assertEqual(post.author, FollowTests.post.author)

    def test_another_auth_user_cannot_view_new_author_posts(self):
        """Новая запись автора не появляется в ленте тех,
           кто на него не подписан.
        """
        response = self.other_user_client.get(
            reverse('posts:follow_index'))

        posts_count_from_context = len(response.context['page_obj'])

        self.assertEqual(posts_count_from_context, 0)
