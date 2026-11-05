import sqlite3

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(tmp_path):
    with TestClient(main.create_app(tmp_path / "guestbook.db")) as connection:
        yield connection


def test_empty_and_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "아직 남겨진 인사가 없어요" in response.text
    assert '<form action="/entries" method="post"' in response.text
    assert "<script" not in response.text
    assert client.get("/health").json() == {"status": "ok"}


def test_write_redirect_and_refresh(client):
    response = client.post("/entries", data={"name": "  방문자  ", "message": "  안녕하세요\n반가워요  "}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    for _ in range(2):
        page = client.get("/").text
        assert "총 1개의 인사" in page
        assert "<strong>방문자</strong>" in page
        assert "안녕하세요\n반가워요" in page


@pytest.mark.parametrize("data", [
    {"name": " ", "message": "인사"},
    {"name": "방문자", "message": "\n\t "},
    {"name": "가" * 31, "message": "인사"},
    {"name": "방문자", "message": "가" * 1001},
    {"name": "방문자"},
    {"name": "방문자", "message": "인사", "extra": "x"},
])
def test_invalid_input_does_not_write(client, data):
    response = client.post("/entries", data=data)
    assert response.status_code == 422
    assert "총 0개의 인사" in client.get("/").text


def test_maximum_korean_input(client):
    response = client.post("/entries", data={"name": "가" * 30, "message": "나" * 1000})
    assert response.status_code == 200
    assert "나" * 1000 in response.text


def test_escape_sql_and_template_placeholders(client):
    message = "<script>alert('x')</script> @@name@@ '); DROP TABLE entries; --"
    response = client.post("/entries", data={"name": '<b>"별명"</b>', "message": message})
    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text
    assert "@@name@@" in response.text
    assert "&lt;b&gt;&quot;별명&quot;&lt;/b&gt;" in response.text
    assert client.get("/health").status_code == 200
    error = client.post("/entries", data={"name": '<img src=x onerror="x">', "message": " "})
    assert error.status_code == 422
    assert '<img src=x' not in error.text


def test_persistence_and_single_table(tmp_path):
    path = tmp_path / "nested" / "book.db"
    with TestClient(main.create_app(path)) as first:
        first.post("/entries", data={"name": "다시", "message": "재시작 후에도 남아요"})
    with TestClient(main.create_app(path)) as second:
        assert "재시작 후에도 남아요" in second.get("/").text
    with sqlite3.connect(path) as database:
        assert database.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [("entries",)]


def test_pagination_and_order(client):
    for number in range(21):
        client.post("/entries", data={"name": "방문자", "message": f"글번호-{number:02d}"}, follow_redirects=False)
    first = client.get("/").text
    assert "글번호-20" in first and "글번호-00" not in first
    assert first.index("글번호-20") < first.index("글번호-19")
    assert "글번호-00" in client.get("/?page=2").text
    assert "글번호-00" in client.get("/?page=1000000").text
    assert client.get("/?page=0").status_code == 422


def test_capacity_limit_preserves_existing_entries(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_ENTRIES", 1)
    client.post("/entries", data={"name": "첫째", "message": "보존"})
    response = client.post("/entries", data={"name": "둘째", "message": "한도 초과"})
    assert response.status_code == 409
    assert "방명록이 가득" in response.text
    page = client.get("/").text
    assert "총 1개의 인사" in page and "<strong>첫째</strong>" in page


def test_protocol_and_size_limits(client):
    assert client.post("/entries", json={"name": "a", "message": "b"}).status_code == 415
    headers = {"content-type": "application/x-www-form-urlencoded"}
    assert client.post("/entries", content="name=a&name=b", headers=headers).status_code == 422
    assert client.post("/entries", content=b"name=%FF&message=x", headers=headers).status_code == 422
    assert client.post("/entries", content="x" * 16385, headers=headers).status_code == 413
    assert client.post("/entries", data={"name": "a", "message": "b"}, headers={"sec-fetch-site": "cross-site"}).status_code == 403


def test_database_error_does_not_expose_path(client, monkeypatch):
    def broken_connection(path):
        raise sqlite3.OperationalError("private database path")

    monkeypatch.setattr(main, "connect", broken_connection)
    response = client.get("/")
    assert response.status_code == 503
    assert "private database path" not in response.text
