"""Day8 방식으로 실제 HTTP 계약과 SQLite 저장 결과를 함께 검증한다."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import importlib.util
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

# 다른 수업의 main.py와 충돌하지 않도록 이 폴더의 파일을 직접 읽는다.
SPEC = importlib.util.spec_from_file_location("guestbook_main", Path(__file__).with_name("main.py"))
guestbook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guestbook)


@pytest.fixture
def database(tmp_path):
    return tmp_path / "guestbook.db"


@pytest.fixture
def client(database):
    with TestClient(guestbook.create_app(database)) as active_client:
        yield active_client


def row_count(database):
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]


def test_empty_page_and_single_table(client, database):
    page = client.get("/")
    assert page.status_code == 200
    assert 'lang="ko"' in page.text
    assert "아직 남겨진 글이 없습니다" in page.text
    assert "<script" not in page.text
    assert client.get("/static/style.css").status_code == 200
    assert "form-action 'self'" in page.headers["content-security-policy"]
    with closing(sqlite3.connect(database)) as connection:
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert tables == [("guestbook",)]
        assert connection.execute("PRAGMA foreign_key_list(guestbook)").fetchall() == []


def test_create_redirect_and_persistence(client, database):
    response = client.post("/entries", data={"name": "  방문자  ", "message": "안녕하세요\n반갑습니다"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/?saved=true"
    assert "글을 등록했습니다" in client.get(response.headers["location"]).text
    assert row_count(database) == 1
    # 같은 파일로 새 앱을 시작해도 기존 글이 보존된다.
    with TestClient(guestbook.create_app(database)) as restarted:
        page = restarted.get("/")
        assert "방문자" in page.text and "안녕하세요\n반갑습니다" in page.text
    assert row_count(database) == 1


@pytest.mark.parametrize("name,message", [("", "안녕"), (" \t", "안녕"), ("가" * 21, "안녕"),
                                             ("이름", ""), ("이름", " \n"), ("이름", "가" * 501),
                                             ("이름", "a\x00b")])
def test_invalid_input_does_not_write(client, database, name, message):
    response = client.post("/entries", data={"name": name, "message": message})
    assert response.status_code == 422
    assert "이름은 1~20자" in response.text
    assert row_count(database) == 0


def test_maximum_lengths_and_html_sql_escaping(client, database):
    assert client.post("/entries", data={"name": "가" * 20, "message": "😀" * 500}).status_code == 200
    payload = "<script>alert('x')</script> & </textarea>"
    sql_name = "' OR 1=1; --"
    assert client.post("/entries", data={"name": sql_name, "message": payload}).status_code == 200
    page = client.get("/").text
    assert "&lt;script&gt;" in page and "<script>" not in page
    assert "&lt;/textarea&gt;" in page
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT name,message FROM guestbook ORDER BY id DESC LIMIT 1").fetchone() == (sql_name, payload)
    assert row_count(database) == 2


def test_latest_first_and_pagination(client):
    for index in range(12):
        client.post("/entries", data={"name": f"방문-{index:02}", "message": f"내용-{index:02}"})
    page1 = client.get("/").text
    assert page1.index("방문-11") < page1.index("방문-10")
    assert "방문-02" in page1 and "방문-01" not in page1
    page2 = client.get("/?page=2").text
    assert "방문-01" in page2 and "방문-00" in page2
    assert "방문-02" not in page2
    assert "2 / 2" in client.get("/?page=100").text


@pytest.mark.parametrize("page", ["0", "-1", "101", "abc", "1.5"])
def test_invalid_page_returns_html(client, page):
    response = client.get("/", params={"page": page})
    assert response.status_code == 422
    assert "text/html" in response.headers["content-type"]


@pytest.mark.parametrize("body", ["name=a&name=b&message=c", "name=a", "name=a&message=b&other=c", "name=%FF&message=b", "invalid"])
def test_malformed_form_does_not_write(client, database, body):
    response = client.post("/entries", content=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 422
    assert row_count(database) == 0


def test_body_limit_and_content_type(client, database):
    assert client.post("/entries", json={"name": "a", "message": "b"}).status_code == 415
    response = client.post("/entries", content="name=a&message=" + "b" * guestbook.MAX_BODY_BYTES,
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 413
    # Content-Length 없이 전송해도 실제 받은 바이트로 제한한다.
    response = client.post("/entries", content=iter([b"name=a&message=", b"x" * guestbook.MAX_BODY_BYTES]),
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 413
    assert row_count(database) == 0


def test_capacity_preserves_existing_entries(client, database, monkeypatch):
    monkeypatch.setattr(guestbook, "MAX_ENTRIES", 1)
    assert client.post("/entries", data={"name": "첫째", "message": "보존할 글"}).status_code == 200
    response = client.post("/entries", data={"name": "둘째", "message": "거절할 글"})
    assert response.status_code == 409
    assert "가득 찼습니다" in response.text
    assert row_count(database) == 1
    assert "보존할 글" in client.get("/").text


def test_concurrent_writes_respect_capacity(database, monkeypatch):
    guestbook.init_database(database)
    monkeypatch.setattr(guestbook, "MAX_ENTRIES", 3)

    def write(index):
        try:
            guestbook.save_entry(database, f"이름{index}", "동시 요청")
            return 201
        except guestbook.HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(write, range(6)))
    assert results.count(201) == 3 and results.count(409) == 3
    assert row_count(database) == 3


def test_database_failure_returns_service_unavailable(client, monkeypatch):
    def unavailable(path):
        raise sqlite3.OperationalError("internal path must not be exposed")

    monkeypatch.setattr(guestbook, "connect", unavailable)
    response = client.get("/")
    assert response.status_code == 503
    assert "internal path" not in response.text
    assert response.headers["retry-after"] == "5"
