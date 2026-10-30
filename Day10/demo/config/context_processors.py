from django.conf import settings


def site_paths(request):
    return {"site_root": settings.APP_URL_PREFIX}
