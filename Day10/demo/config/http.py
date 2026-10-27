from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage
from django.conf import settings


def site_path(url):
    prefix = settings.APP_URL_PREFIX
    if prefix and url.startswith("/") and not url.startswith("//") and url != prefix and not url.startswith(prefix + "/"):
        return prefix + url
    return url

def see_other(url):
    response = HttpResponseRedirect(site_path(url))
    response.status_code = 303
    return response

def page_for(request, queryset, size, key="page"):
    raw = request.GET.get(key, "1")
    if len(raw) > 9 or not raw.isascii() or not raw.isdigit() or int(raw) < 1:
        return None
    try:
        return Paginator(queryset, size).page(int(raw))
    except EmptyPage:
        raise Http404("페이지가 없습니다.")

