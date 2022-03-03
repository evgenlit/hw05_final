from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

POSTS_COUNT = 10


def get_paginator(data, request):
    paginator = Paginator(data, POSTS_COUNT)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    return posts


def index(request):
    title = 'Последние обновления на сайте'
    post_list = Post.objects.select_related('author', 'group')

    posts = get_paginator(post_list, request)

    context = {
        'page_obj': posts,
        'title': title
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')

    posts = get_paginator(post_list, request)

    context = {
        'group': group,
        'page_obj': posts,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()

    posts = get_paginator(post_list, request)

    following = False
    if request.user.is_authenticated:
        following = user.following.exists()

    context = {
        'author': user,
        'page_obj': posts,
        'following': following,
        'user_posts_count': post_list.count
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    author_posts_count = author.posts.count()
    comments = post.comments.all()
    comments_form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'author_posts_count': author_posts_count,
        'comments': comments,
        'form': comments_form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user)
    context = {
        'form': form,
        'id_edit': False,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    title = 'Подписки на авторов'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_paginator(posts, request)
    context = {
        'page_obj': page_obj,
        'title': title
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    is_follow_exists = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if author != request.user and not is_follow_exists:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user_follows = Follow.objects.filter(user=request.user)
    user_follows.get(author=author).delete()
    return redirect('posts:profile', username=username)
