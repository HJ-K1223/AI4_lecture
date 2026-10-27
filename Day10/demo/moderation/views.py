from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from config.http import page_for, see_other
from django.http import HttpResponseBadRequest
from .forms import TermForm
from .models import BannedTerm
from .services import add_terms

def admin_required(view):
    @login_required
    @wraps(view)
    def inner(request, *args, **kwargs):
        if request.user.role != "ADMIN":
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return inner

@admin_required
@require_http_methods(["GET", "POST"])
def terms(request):
    form = TermForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if request.POST.get("match_type", "KEYWORD") != "KEYWORD":
            form.add_error(None, "KEYWORD 유형만 지원합니다.")
        else:
            try:
                count = add_terms([{"pattern": form.cleaned_data["pattern"]}], request.user)
                if count:
                    return see_other("/moderation/terms/")
                form.add_error("pattern", "이미 등록된 키워드입니다.")
            except ValidationError as error:
                form.add_error(None, error)
    page = page_for(request, BannedTerm.objects.all(), 20)
    if page is None:
        return HttpResponseBadRequest("잘못된 페이지 번호입니다.")
    return render(request, "moderation/terms.html", {"form": form, "page": page}, status=400 if request.method == "POST" else 200)

@admin_required
@require_POST
def delete_term(request, pk):
    with transaction.atomic():
        get_object_or_404(BannedTerm, pk=pk).delete()
    return see_other("/moderation/terms/")

