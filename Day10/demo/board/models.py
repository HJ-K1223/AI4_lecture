from django.conf import settings
from django.db import models
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "posts"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["-created_at", "-id"], name="post_latest_idx")]
        constraints = [models.CheckConstraint(condition=~models.Q(title__regex=r"^\s*$"), name="post_title_not_blank"),
                       models.CheckConstraint(condition=~models.Q(content__regex=r"^\s*$"), name="post_content_not_blank"),
                       models.CheckConstraint(condition=LessThanOrEqual(Length("content"), 20000), name="post_content_length")]

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, db_index=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "comments"
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["post", "created_at", "id"], name="comment_post_order_idx")]
        constraints = [models.CheckConstraint(condition=~models.Q(content__regex=r"^\s*$"), name="comment_content_not_blank")]

