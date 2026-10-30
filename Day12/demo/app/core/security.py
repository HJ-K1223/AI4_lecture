"""비밀번호·내부 복귀 경로·CSRF 공통 처리."""

import re
from secrets import compare_digest, token_urlsafe
from urllib.parse import parse_qs, unquote, urlencode, urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

PASSWORD_HASHER = PasswordHasher()
SESSION_COOKIE = "shoppingmall_session"
SESSION_MAX_AGE = 7200
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def hash_password(password: str) -> str:
    return PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def safe_next(value: str | None) -> str:
    """위험한 인코딩·슬래시 우회와 인증 화면 복귀 루프를 차단합니다."""
    if not value or len(value) > 2048:
        return "/products"
    decoded = value
    for _ in range(8):
        if (
            not decoded.startswith("/") or decoded.startswith("//")
            or "\\" in decoded or re.search(r"[\x00-\x20\x7f]", decoded)
        ):
            return "/products"
        try:
            parts = urlsplit(decoded)
        except ValueError:
            return "/products"
        # 점 경로도 금지해 브라우저 정규화 후 인증 화면으로 돌아가는 것을 막습니다.
        if parts.scheme or parts.netloc or any(segment in (".", "..") for segment in parts.path.split("/")):
            return "/products"
        if parts.path.rstrip("/").lower() in ("/login", "/register", "/logout"):
            return "/products"
        next_decoded = unquote(decoded)
        if next_decoded == decoded:
            return value
        decoded = next_decoded
    return "/products"


def login_url(next_path: str) -> str:
    return "/login?" + urlencode({"next": safe_next(next_path)})


def csrf_token(request) -> str:
    if not isinstance(request.session.get("csrf"), str):
        request.session["csrf"] = token_urlsafe(32)
    return request.session["csrf"]


def establish_login(request, member) -> None:
    request.session.clear()
    request.session.update({
        "member_id": str(member.id), "auth_version": member.auth_version, "csrf": token_urlsafe(32)
    })


def normalized_origin(value: str) -> tuple | None:
    try:
        parts = urlsplit(value)
        if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password:
            return None
        return parts.scheme.lower(), parts.hostname.lower(), parts.port or (443 if parts.scheme == "https" else 80)
    except ValueError:
        return None


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/static/"):
            return await call_next(request)
        if request.method in UNSAFE_METHODS:
            # 만료된 세션은 변경을 실행하지 않고 먼저 인증을 요구합니다.
            # 로그인·가입 폼은 익명 요청에도 아래 CSRF 검사를 그대로 적용합니다.
            if not request.session.get("member_id"):
                if request.url.path.startswith("/api/"):
                    return JSONResponse({"detail": "로그인이 필요합니다."}, status_code=401,
                                        headers={"Cache-Control": "no-store"})
                if request.url.path == "/logout":
                    return RedirectResponse(login_url("/products"), status_code=303)
            expected_origin = normalized_origin(str(request.app.state.settings.app_base_url))
            supplied_origin = request.headers.get("origin")
            source = supplied_origin if supplied_origin is not None else request.headers.get("referer", "")
            candidate = request.headers.get("x-csrf-token", "")
            if normalized_origin(source) != expected_origin:
                return self.rejected()
            if not candidate and request.headers.get("content-type", "").split(";")[0].strip() == "application/x-www-form-urlencoded":
                # body()를 먼저 캐시하여 이후 폼 처리에도 같은 본문이 전달되도록 합니다.
                chunks = []
                size = 0
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 16384:
                        return JSONResponse({"detail": "입력 내용이 너무 큽니다."}, status_code=413)
                    chunks.append(chunk)
                request._body = b"".join(chunks)
                try:
                    values = parse_qs(request._body.decode("utf-8"), max_num_fields=20)
                    tokens = values.get("csrf_token", [])
                    candidate = tokens[0] if len(tokens) == 1 else ""
                except (ValueError, UnicodeDecodeError):
                    return self.rejected()
            expected = request.session.get("csrf", "")
            if not (
                isinstance(expected, str) and expected and candidate and candidate.isascii()
                and len(candidate) <= 128 and compare_digest(expected, candidate)
            ):
                return self.rejected()
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @staticmethod
    def rejected():
        return JSONResponse(
            {"detail": "요청을 확인할 수 없습니다. 화면을 새로고침한 뒤 다시 시도하세요."},
            status_code=403, headers={"Cache-Control": "no-store"},
        )
