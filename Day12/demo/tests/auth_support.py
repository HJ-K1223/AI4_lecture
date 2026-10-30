"""인증 테스트용 독립 DB와 공통 도우미."""

import re
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.auth import required_member
from app.core.db import Base, get_optional_db
from app.main import create_app
from app.models import Member
from tests.test_foundation import local_settings

TEST_PASSWORD = "test-only-password-1234"
TEST_ORIGIN = "https://testserver"


def sqlite_database():
    engine = create_engine(
        "sqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        execution_options={"schema_translate_map": {"shoppingmall": None}},
    )

    @event.listens_for(engine, "connect")
    def sqlite_uuid(connection, record):
        connection.create_function("gen_random_uuid", 0, lambda: uuid4().hex)
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE UNIQUE INDEX members_email_test_idx ON members (email)")
        connection.exec_driver_sql("CREATE UNIQUE INDEX products_sku_test_idx ON products (sku)")
        connection.exec_driver_sql("CREATE UNIQUE INDEX orders_cart_test_idx ON orders (member_id) WHERE status='CART'")
        connection.exec_driver_sql("CREATE UNIQUE INDEX order_items_test_idx ON order_items (order_id, product_id)")
        connection.exec_driver_sql("CREATE UNIQUE INDEX payments_key_test_idx ON payments (idempotency_key)")
        connection.exec_driver_sql("CREATE UNIQUE INDEX payments_success_test_idx ON payments (order_id) WHERE status='SUCCEEDED'")
        connection.exec_driver_sql("CREATE UNIQUE INDEX payments_tx_test_idx ON payments (provider, transaction_id)")
    return engine


def auth_app(session_dependency):
    app = create_app(local_settings(app_base_url=TEST_ORIGIN))
    app.dependency_overrides[get_optional_db] = session_dependency

    @app.get("/protected")
    def protected(member=Depends(required_member)):
        return {"name": member.name}

    @app.post("/api/test/write")
    def protected_write(member=Depends(required_member)):
        return {"ok": True}

    return app


def token_from(response):
    match = re.search(r'name="csrf-token" content="([^"]+)"', response.text)
    if match is None:
        raise AssertionError("CSRF 메타 태그가 없습니다.")
    return match.group(1)


def register_form(client, *, email="buyer@example.com", next_path="/products"):
    token = token_from(client.get("/register"))
    return client.post("/register", headers={"origin": TEST_ORIGIN}, follow_redirects=False, data={
        "csrf_token": token, "next": next_path, "email": email, "name": "테스트회원",
        "password": TEST_PASSWORD, "password_confirm": TEST_PASSWORD,
    })


def login_form(client, *, email="buyer@example.com", password=TEST_PASSWORD, next_path="/products"):
    token = token_from(client.get("/login"))
    return client.post("/login", headers={"origin": TEST_ORIGIN}, follow_redirects=False, data={
        "csrf_token": token, "next": next_path, "email": email, "password": password,
    })
