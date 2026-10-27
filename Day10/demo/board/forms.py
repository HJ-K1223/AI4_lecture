from django import forms
from .models import Post, Comment
class PostForm(forms.ModelForm):
    content = forms.CharField(label="내용", max_length=20000, widget=forms.Textarea)
    class Meta:
        model = Post
        fields = ["title", "content"]
        labels = {"title": "제목"}
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        labels = {"content": "댓글"}
        widgets = {"content": forms.Textarea(attrs={"rows": 3})}

