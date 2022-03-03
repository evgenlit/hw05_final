from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", 'image',)

        labels = {
            "text": "Текст",
            "group": "Группа",
        }

        help_texts = {
            'text': 'Напишите сюда текст поста',
            'group': 'Выберите группу для поста',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
