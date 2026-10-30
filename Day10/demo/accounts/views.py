from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from urllib.parse import urlsplit
from config.http import see_other, site_path
from .forms import SignupForm, LoginForm

@sensitive_post_parameters("password", "password_confirm")
@never_cache
@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return see_other("/posts/")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error("email", "이미 사용 중인 이메일입니다.")
        else:
            return see_other("/accounts/login/")
    return render(request, "form.html", {"form": form, "title": "회원가입"}, status=400 if request.method == "POST" else 200)

@sensitive_post_parameters("password")
@never_cache
@require_http_methods(["GET", "POST"])
def signin(request):
    if request.user.is_authenticated:
        return see_other("/posts/")
    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        target = request.POST.get("next") or site_path("/posts/")
        in_mount = not settings.APP_URL_PREFIX or urlsplit(target).path.startswith(settings.APP_URL_PREFIX + "/")
        if not in_mount or not url_has_allowed_host_and_scheme(target, {request.get_host()}, require_https=request.is_secure()):
            target = site_path("/posts/")
        return see_other(target)
    target = request.POST.get("next", "") if request.method == "POST" else request.GET.get("next", "")
    return render(request, "accounts/login.html", {"form": form, "next": target}, status=400 if request.method == "POST" else 200)

@require_POST
@login_required
def signout(request):
    logout(request)
    return see_other("/accounts/login/")

@require_http_methods(["GET", "POST"])
def password_help(request):
    return render(request, "accounts/password_help.html")

