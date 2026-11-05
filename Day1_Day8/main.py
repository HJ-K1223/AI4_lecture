"""HTML 폼과 Supabase PostgreSQL을 사용하는 작은 방명록."""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from html import escape
import os
import json
from pathlib import Path
from string import Template
from urllib.parse import parse_qs

import psycopg
from psycopg.rows import dict_row

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
PAGE = Template((BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8"))
PAGE_SIZE = 10
MAX_ENTRIES = 1000
MAX_BODY_BYTES = 16 * 1024
KST = timezone(timedelta(hours=9))


def load_database_config(config_path: Path) -> dict:
    try:
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        required = ("host", "port", "dbname", "user", "password")
        if not isinstance(config, dict) or any(key not in config for key in required):
            raise ValueError
        settings = {key: config[key] for key in required}
        if any(not isinstance(settings[key], str) or not settings[key].strip()
               for key in ("host", "dbname", "user", "password")):
            raise ValueError
        settings["port"] = int(settings["port"])
        if not 1 <= settings["port"] <= 65535:
            raise ValueError
        return settings
    except (OSError, ValueError, TypeError):
        raise RuntimeError("DB 설정을 읽을 수 없습니다. config.json의 필수 항목을 확인해 주세요.") from None


def connect(database: dict) -> psycopg.Connection:
    return psycopg.connect(
        **database, sslmode="require", connect_timeout=5,
        options="-c search_path=public -c statement_timeout=10000 -c lock_timeout=5000",
        prepare_threshold=None, row_factory=dict_row,
    )


def init_database(database: dict) -> None:
    """SQL Editor에서 만든 테이블의 연결과 열을 읽기 전용으로 확인한다."""
    with connect(database) as connection:
        connection.execute("SELECT id, name, message, created_at FROM guestbook LIMIT 0")


def save_entry(database: dict, name: str, message: str) -> None:
    with connect(database) as connection:
        # 개수 검사와 저장을 하나의 쓰기 트랜잭션에 묶어 동시 요청에도 한도를 지킨다.
        connection.execute("LOCK TABLE guestbook IN SHARE ROW EXCLUSIVE MODE")
        count = connection.execute("SELECT COUNT(*) AS total FROM guestbook").fetchone()["total"]
        if count >= MAX_ENTRIES:
            raise HTTPException(409, "방명록이 가득 찼습니다. 새 글을 등록할 수 없습니다.")
        connection.execute(
            "INSERT INTO guestbook (name, message) VALUES (%s, %s)",
            (name, message),
        )


def render_page(database: dict, page: int = 1, name: str = "", message: str = "",
                notice: str = "", status_code: int = 200) -> HTMLResponse:
    with connect(database) as connection:
        total = connection.execute("SELECT COUNT(*) AS total FROM guestbook").fetchone()["total"]
        last_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(page, last_page)
        rows = connection.execute(
            "SELECT name, message, created_at FROM guestbook ORDER BY id DESC LIMIT %s OFFSET %s",
            (PAGE_SIZE, (page - 1) * PAGE_SIZE),
        ).fetchall()
    cards = []
    for row in rows:
        stamp = row["created_at"].astimezone(KST)
        cards.append(
            '<article class="entry"><header>'
            f'<h3>{escape(row["name"])}</h3>'
            f'<time datetime="{escape(stamp.isoformat(timespec="seconds"), quote=True)}">'
            f'{stamp:%Y.%m.%d %H:%M} · 한국 시간</time></header>'
            f'<p>{escape(row["message"])}</p></article>'
        )
    previous = f'<a href="/?page={page - 1}#entries">이전</a>' if page > 1 else '<span>이전</span>'
    following = f'<a href="/?page={page + 1}#entries">다음</a>' if page < last_page else '<span>다음</span>'
    return HTMLResponse(PAGE.substitute(
        name=escape(name, quote=True), message=escape(message),
        notice=f'<p class="notice" role="alert">{escape(notice)}</p>' if notice else "",
        entries="".join(cards) or '<p class="empty">아직 남겨진 글이 없습니다. 첫 인사를 남겨 주세요.</p>',
        total=total, previous=previous, following=following, page=page, last_page=last_page,
    ), status_code=status_code)


async def read_form(request: Request) -> dict[str, str]:
    """기본 HTML 폼만 받아 추가 폼 라이브러리 없이 제한된 크기로 해석한다."""
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/x-www-form-urlencoded":
        raise HTTPException(415, "기본 방명록 입력 폼을 사용해 주세요.")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_BODY_BYTES:
            raise HTTPException(413, "전송한 내용이 너무 큽니다.")
        body.extend(chunk)
    try:
        fields = parse_qs(body.decode("utf-8"), keep_blank_values=True,
                          strict_parsing=True, errors="strict", max_num_fields=2)
    except (UnicodeError, ValueError):
        raise HTTPException(422, "입력 형식이 올바르지 않습니다.") from None
    if set(fields) != {"name", "message"} or any(len(values) != 1 for values in fields.values()):
        raise HTTPException(422, "이름과 내용을 각각 한 번 입력해 주세요.")
    return {key: values[0].strip() for key, values in fields.items()}


def create_app(config_path: Path | None = None) -> FastAPI:
    config_file = Path(config_path) if config_path is not None else Path(
        os.environ.get("GUESTBOOK_CONFIG_PATH", str(BASE_DIR / "config.json"))
    )
    if not config_file.is_absolute():
        config_file = BASE_DIR / config_file
    database = {}

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        database.update(load_database_config(config_file))
        try:
            init_database(database)
        except psycopg.Error:
            raise RuntimeError("Supabase DB 연결 또는 guestbook 테이블을 확인해 주세요.") from None
        yield

    application = FastAPI(title="작은 방명록", lifespan=lifespan,
                          docs_url=None, redoc_url=None, openapi_url=None)
    application.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    @application.middleware("http")
    async def response_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'self'; form-action 'self'; "
            "base-uri 'none'; frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if response.headers.get("content-type", "").startswith("text/html"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.exception_handler(HTTPException)
    def http_error(request: Request, error: HTTPException):
        return render_page(database, notice=str(error.detail), status_code=error.status_code)

    @application.exception_handler(RequestValidationError)
    def validation_error(request: Request, error: RequestValidationError):
        return render_page(database, notice="페이지는 1~100 사이의 정수로 입력해 주세요.", status_code=422)

    @application.exception_handler(psycopg.Error)
    def database_error(request: Request, error: psycopg.Error):
        # DB 장애 시에는 DB를 다시 조회하지 않고 간단한 HTML만 반환한다.
        return HTMLResponse(
            '<!doctype html><html lang="ko"><meta charset="utf-8">'
            '<title>잠시 후 다시 시도해 주세요</title><h1>저장소를 사용할 수 없습니다.</h1>'
            '<p>잠시 후 다시 시도해 주세요.</p><a href="/">방명록으로</a></html>',
            status_code=503, headers={"Retry-After": "5"},
        )

    @application.get("/", response_class=HTMLResponse)
    def home(page: int = Query(default=1, ge=1, le=100), saved: bool = False):
        return render_page(database, page, notice="글을 등록했습니다." if saved else "")

    @application.post("/entries", response_class=HTMLResponse)
    def create_entry(form: dict = Depends(read_form)):
        name, message = form["name"], form["message"]
        if not 1 <= len(name) <= 20 or not 1 <= len(message) <= 500 or "\x00" in name + message:
            return render_page(
                database, name=name[:20], message=message[:500], status_code=422,
                notice="이름은 1~20자, 내용은 1~500자로 입력해 주세요. 공백만 입력하거나 널 문자는 사용할 수 없습니다.",
            )
        save_entry(database, name, message)
        return RedirectResponse("/?saved=true", status_code=303)

    return application


app = create_app()
