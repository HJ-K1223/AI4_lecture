"""HTML 폼과 SQLite 테이블 하나로 만드는 작은 방명록."""
from contextlib import asynccontextmanager, closing
from datetime import datetime, timedelta, timezone
from html import escape
import os
from pathlib import Path
import sqlite3
from string import Template
from urllib.parse import parse_qs

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


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def init_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(db_path)) as connection, connection:
        # AUTOINCREMENT를 쓰지 않아 sqlite_sequence 등 추가 테이블도 만들지 않는다.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS guestbook (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 20),
                message TEXT NOT NULL CHECK(length(message) BETWEEN 1 AND 500),
                created_at TEXT NOT NULL
            )
        """)


def save_entry(db_path: Path, name: str, message: str) -> None:
    with closing(connect(db_path)) as connection, connection:
        # 개수 검사와 저장을 하나의 쓰기 트랜잭션에 묶어 동시 요청에도 한도를 지킨다.
        connection.execute("BEGIN IMMEDIATE")
        count = connection.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]
        if count >= MAX_ENTRIES:
            raise HTTPException(409, "방명록이 가득 찼습니다. 새 글을 등록할 수 없습니다.")
        connection.execute(
            "INSERT INTO guestbook (name, message, created_at) VALUES (?, ?, ?)",
            (name, message, datetime.now(KST).isoformat(timespec="seconds")),
        )


def render_page(db_path: Path, page: int = 1, name: str = "", message: str = "",
                notice: str = "", status_code: int = 200) -> HTMLResponse:
    with closing(connect(db_path)) as connection:
        total = connection.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]
        last_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(page, last_page)
        rows = connection.execute(
            "SELECT name, message, created_at FROM guestbook ORDER BY id DESC LIMIT ? OFFSET ?",
            (PAGE_SIZE, (page - 1) * PAGE_SIZE),
        ).fetchall()
    cards = []
    for row in rows:
        stamp = datetime.fromisoformat(row["created_at"])
        cards.append(
            '<article class="entry"><header>'
            f'<h3>{escape(row["name"])}</h3>'
            f'<time datetime="{escape(row["created_at"], quote=True)}">'
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


def create_app(db_path: Path | None = None) -> FastAPI:
    database = Path(db_path) if db_path is not None else Path(
        os.environ.get("GUESTBOOK_DB_PATH", str(BASE_DIR / "data" / "guestbook.db"))
    )
    if not database.is_absolute():
        database = BASE_DIR / database

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        init_database(database)
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

    @application.exception_handler(sqlite3.Error)
    def database_error(request: Request, error: sqlite3.Error):
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
