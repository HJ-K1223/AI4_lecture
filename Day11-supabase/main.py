"""HTML 폼과 SQLite 한 테이블로 만드는 작은 방명록."""

import os
import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent
PAGE_SIZE = 20
MAX_ENTRIES = 1000
MAX_BODY_BYTES = 16384
TEMPLATE = (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


class EntryInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=30)
    message: str = Field(min_length=1, max_length=1000)


def connect(db_path: Path):
    connection = sqlite3.connect(db_path, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(db_path)) as connection, connection:
        # AUTOINCREMENT를 생략하므로 별도의 sqlite_sequence 테이블도 생기지 않습니다.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 30),
                message TEXT NOT NULL CHECK(length(message) BETWEEN 1 AND 1000),
                created_at TEXT NOT NULL
            )
        """)


def render_page(db_path: Path, page=1, error="", name="", message="", status=200):
    with closing(connect(db_path)) as connection:
        total = connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        last_page = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(page, last_page)
        records = connection.execute(
            "SELECT id, name, message, created_at FROM entries "
            "ORDER BY id DESC LIMIT ? OFFSET ?",
            (PAGE_SIZE, (page - 1) * PAGE_SIZE),
        ).fetchall()

    cards = []
    for record in records:
        cards.append(
            '<article class="entry"><header>'
            f'<strong>{escape(record["name"])}</strong>'
            f'<time datetime="{escape(record["created_at"])}">'
            f'{escape(record["created_at"].replace("T", " ").replace("+00:00", " UTC"))}'
            '</time></header>'
            f'<p class="message">{escape(record["message"])}</p></article>'
        )
    if not cards:
        cards.append('<p class="empty">아직 남겨진 인사가 없어요. 첫 번째 인사를 남겨 주세요.</p>')

    navigation = []
    if page > 1:
        navigation.append(f'<a href="/?page={page - 1}">← 이전</a>')
    navigation.append(f'<span>{page} / {last_page}</span>')
    if page < last_page:
        navigation.append(f'<a href="/?page={page + 1}">다음 →</a>')

    # split 후 한 번만 치환하여 사용자 글 속의 자리표시자는 다시 처리하지 않습니다.
    values = {
        "total": str(total),
        "error": f'<p class="error" role="alert">{escape(error)}</p>' if error else "",
        "name": escape(name, quote=True),
        "message": escape(message),
        "entries": "".join(cards),
        "navigation": "".join(navigation),
    }
    parts = TEMPLATE.split("@@")
    html = "".join(values.get(part, part) if i % 2 else part for i, part in enumerate(parts))
    return HTMLResponse(html, status_code=status)


def save_entry(db_path: Path, entry: EntryInput):
    with closing(connect(db_path)) as connection, connection:
        # 글 수 확인과 저장을 한 트랜잭션으로 묶어 동시 요청도 한도를 지킵니다.
        connection.execute("BEGIN IMMEDIATE")
        total = connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        if total >= MAX_ENTRIES:
            return False
        connection.execute(
            "INSERT INTO entries (name, message, created_at) VALUES (?, ?, ?)",
            (entry.name, entry.message, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
    return True


def submit_entry(db_path: Path, body: bytes):
    name, message = "", ""
    try:
        fields = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=2, errors="strict")
        if set(fields) != {"name", "message"} or any(len(v) != 1 for v in fields.values()):
            raise ValueError("잘못된 폼")
        name, message = fields["name"][0], fields["message"][0]
        entry = EntryInput(name=name, message=message)
    except (ValueError, ValidationError):
        return render_page(
            db_path, error="이름은 1~30자, 내용은 1~1,000자로 입력해 주세요. 공백만 입력할 수 없습니다.",
            name=name, message=message, status=422,
        )
    if not save_entry(db_path, entry):
        return render_page(
            db_path, error="방명록이 가득 찼습니다. 지금은 새 글을 받을 수 없습니다.",
            name=name, message=message, status=409,
        )
    # 작성 후 GET으로 이동하므로 새로고침해도 같은 POST가 반복되지 않습니다.
    return RedirectResponse("/", status_code=303)


def create_app(db_path: Path | None = None):
    database = Path(db_path) if db_path is not None else Path(
        os.environ.get("GUESTBOOK_DB_PATH", str(BASE_DIR / "data" / "guestbook.db"))
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await run_in_threadpool(init_db, database)
        yield

    application = FastAPI(title="작은 방명록", lifespan=lifespan, docs_url=None, redoc_url=None)

    @application.middleware("http")
    async def response_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
            "frame-ancestors 'none'; base-uri 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @application.exception_handler(sqlite3.Error)
    async def database_error(request: Request, error: sqlite3.Error):
        return HTMLResponse(
            '<!doctype html><html lang="ko"><meta charset="utf-8">'
            '<title>잠시 후 다시 시도해 주세요</title><h1>저장소에 연결할 수 없습니다.</h1>'
            '<p>잠시 후 다시 시도해 주세요.</p><a href="/">방명록으로 돌아가기</a></html>',
            status_code=503,
        )

    @application.get("/", response_class=HTMLResponse)
    def home(page: int = Query(default=1, ge=1, le=1000000)):
        return render_page(database, page=page)

    @application.post("/entries")
    async def create_entry(request: Request):
        if request.headers.get("sec-fetch-site") == "cross-site":
            return HTMLResponse("다른 사이트에서는 글을 작성할 수 없습니다.", status_code=403)
        content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type != "application/x-www-form-urlencoded":
            return HTMLResponse("HTML 폼으로 작성해 주세요.", status_code=415)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_BODY_BYTES:
                return HTMLResponse("입력한 내용이 너무 큽니다.", status_code=413)
        return await run_in_threadpool(submit_entry, database, bytes(body))

    @application.get("/health")
    def health():
        with closing(connect(database)) as connection:
            connection.execute("SELECT id FROM entries LIMIT 1").fetchone()
        return {"status": "ok"}

    return application


app = create_app()
