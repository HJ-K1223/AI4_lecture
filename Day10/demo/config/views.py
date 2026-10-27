from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from .http import site_path


@never_cache
@require_GET
def home(request):
    return redirect(site_path("/posts/" if request.user.is_authenticated else "/accounts/login/"))
