from django.conf import settings
from django.core.paginator import Paginator


def get_paginator(data, request):
    paginator = Paginator(data, settings.POSTS_COUNT)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    return posts
