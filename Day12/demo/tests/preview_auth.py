"""브라우저 검증 전용. 메모리 SQLite를 쓰며 Supabase에는 접속하지 않습니다."""

from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.db import get_optional_db
from app.core.security import csrf_token
from app.main import create_app
from tests.auth_support import sqlite_database
from tests.test_foundation import local_settings
from tests.demo_data import seed_preview

engine = sqlite_database()
seed_preview(engine)
app = create_app(local_settings(
    app_base_url="http://127.0.0.1:8013", cookie_secure=False, allowed_hosts=["127.0.0.1", "localhost"]
))


def test_session():
    with Session(engine, expire_on_commit=False) as session:
        yield session


app.dependency_overrides[get_optional_db] = test_session


@app.get("/auth-test/fetch", response_class=HTMLResponse)
def fetch_test(request: Request):
    token = csrf_token(request)
    return HTMLResponse(
        '<html lang="ko"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta name="csrf-token" content="{token}"><title>인증 복귀 검증</title></head>'
        '<body><h1>공통 fetch 401 복귀 검증</h1><button id="check">인증 API 호출</button>'
        '<script src="/static/js/common.js"></script><script>'
        'document.querySelector("#check").addEventListener("click", () => {'
        'window.apiFetch("/api/auth/me").catch(() => {});});'
        '</script></body></html>'
    )
