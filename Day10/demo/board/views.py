from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from config.http import page_for, see_other
from moderation.services import Masker
from .models import Post, Comment
from .forms import PostForm, CommentForm

@never_cache
@login_required
@require_GET
def post_list(request):
    page = page_for(request, Post.objects.only("id", "title", "created_at"), 10)
    if page is None:
        return HttpResponseBadRequest("잘못된 페이지 번호입니다.")
    masker = Masker.from_db()
    for post in page:
        post.title = masker.mask(post.title)
    return render(request, "board/list.html", {"page": page})

@never_cache
@login_required
@require_GET
def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = page_for(request, Comment.objects.filter(post=post), 20, "comment_page")
    if comments is None:
        return HttpResponseBadRequest("잘못된 댓글 페이지 번호입니다.")
    masker = Masker.from_db()
    post.title, post.content = masker.mask(post.title), masker.mask(post.content)
    for comment in comments:
        comment.content = masker.mask(comment.content)
    return render(request, "board/detail.html", {"post": post, "comments": comments, "form": CommentForm()})

@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def edit(request, pk=None):
    # Lock updates so a concurrent delete cannot recreate a removed post.
    with transaction.atomic():
        post = get_object_or_404(Post.objects.select_for_update(), pk=pk) if pk else None
        if post and post.author_id != request.user.pk:
            raise PermissionDenied
        form = PostForm(request.POST or None, instance=post)
        if request.method == "POST" and form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            return see_other(f"/posts/{obj.pk}/")
    return render(request, "form.html", {"form": form, "title": "글 수정" if pk else "글 작성"}, status=400 if request.method == "POST" else 200)

@login_required
@require_POST
def delete_post(request, pk):
    with transaction.atomic():
        post = get_object_or_404(Post.objects.select_for_update(), pk=pk)
        if post.author_id != request.user.pk:
            raise PermissionDenied
        post.delete()
    return see_other("/posts/")

@login_required
@require_POST
def add_comment(request, pk):
    with transaction.atomic():
        post = get_object_or_404(Post.objects.select_for_update(), pk=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post, comment.author = post, request.user
            comment.save()
            return see_other(f"/posts/{pk}/")
    return render(request, "form.html", {"form": form, "title": "댓글 작성"}, status=400)

@login_required
@require_POST
def delete_comment(request, pk):
    with transaction.atomic():
        comment = get_object_or_404(Comment.objects.select_for_update(), pk=pk)
        if comment.author_id != request.user.pk:
            raise PermissionDenied
        post_id = comment.post_id
        comment.delete()
    return see_other(f"/posts/{post_id}/")

