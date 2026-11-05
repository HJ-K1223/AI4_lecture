"""설정·화면·오류 처리 검증. 실제 PostgreSQL 동작은 별도 연결 검증이 필요하다."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

from fastapi.testclient import TestClient
import psycopg
import pytest

SPEC = importlib.util.spec_from_file_location("guestbook_main", Path(__file__).with_name("main.py"))
guestbook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guestbook)


def test_config_validation_hides_secrets(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"password":"test-secret",bad}', encoding="utf-8")
    with pytest.raises(RuntimeError) as error:
        guestbook.load_database_config(path)
    assert "test-secret" not in str(error.value)
    path.write_text(json.dumps(dict(host="example", port=5432, dbname="postgres",
                                   user="tester", password="test-secret")), encoding="utf-8")
    assert guestbook.load_database_config(path)["port"] == 5432


def test_page_timezone_and_escaping(monkeypatch):
    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, *args):
            return self

        def fetchone(self):
            return {"total": 1}

        def fetchall(self):
            return [dict(name="<script>", message="<b>안녕</b>",
                         created_at=datetime(2026, 10, 29, tzinfo=timezone.utc))]

    monkeypatch.setattr(guestbook, "connect", lambda _: Connection())
    page = guestbook.render_page({}).body.decode()
    assert "2026.10.29 09:00" in page
    assert '2026-10-29T09:00:00+09:00' in page
    assert "&lt;script&gt;" in page and "<script>" not in page
    assert "&lt;b&gt;안녕&lt;/b&gt;" in page


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(guestbook, "load_database_config", lambda _: {})
    monkeypatch.setattr(guestbook, "init_database", lambda _: None)
    monkeypatch.setattr(guestbook, "render_page", lambda *args, **kw:
                        guestbook.HTMLResponse("test page", status_code=kw.get("status_code", 200)))
    with TestClient(guestbook.create_app()) as active:
        yield active


def test_post_redirect_and_input_trimming(client, monkeypatch):
    saved = []
    monkeypatch.setattr(guestbook, "save_entry", lambda db, name, message: saved.append((name, message)))
    response = client.post("/entries", data=dict(name=" 방문자 ", message=" 안녕\n반가워 "),
                           follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/?saved=true"
    assert saved == [("방문자", "안녕\n반가워")]


@pytest.mark.parametrize("name,message", [("", "안녕"), ("가" * 21, "안녕"),
                                             ("이름", " "), ("이름", "가" * 501), ("이름", "a\x00b")])
def test_invalid_input_does_not_write(client, monkeypatch, name, message):
    def unexpected_write(*args):
        pytest.fail("잘못된 입력이 DB로 전달됨")
    monkeypatch.setattr(guestbook, "save_entry", unexpected_write)
    assert client.post("/entries", data=dict(name=name, message=message)).status_code == 422


@pytest.mark.parametrize("page", ["0", "-1", "101", "abc", "1.5"])
def test_invalid_page(client, page):
    assert client.get("/", params=dict(page=page)).status_code == 422


def test_form_limits(client):
    assert client.post("/entries", json=dict(name="a", message="b")).status_code == 415
    response = client.post("/entries", content="name=a&message=" + "b" * guestbook.MAX_BODY_BYTES,
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 413
    response = client.post("/entries", content="name=a&name=b&message=c",
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 422


def test_database_failure_returns_service_unavailable(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise psycopg.OperationalError("private connection information")
    monkeypatch.setattr(guestbook, "render_page", unavailable)
    response = client.get("/")
    assert response.status_code == 503
    assert "private connection" not in response.text
    assert response.headers["retry-after"] == "5"
