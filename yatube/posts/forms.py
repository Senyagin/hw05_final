from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        labels = {'group': 'Группа', 'text': 'Сообщение',
                  'image': 'Изображение'}
        help_texts = {'group': 'Выберите группу',
                      'text': 'Введите ссообщение',
                      'image': 'Выберите изображение'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}