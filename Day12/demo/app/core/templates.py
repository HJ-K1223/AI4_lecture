"""모든 HTML 화면에 공통 인증·CSRF 정보를 전달합니다."""

from app.core.security import csrf_token, login_url


def render(request, name, *, member=None, status_code=200, **context):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name=name,
        status_code=status_code,
        context={
            "app_name": request.app.state.settings.app_name,
            "member": member,
            "csrf_token": csrf_token(request),
            "login_href": login_url(request.url.path + ("?" + request.url.query if request.url.query else "")),
            **context,
        },
    )
