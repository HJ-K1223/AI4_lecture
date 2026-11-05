"""인증 시나리오와 보안 회귀 검증. 원격 DB는 사용하지 않습니다."""

from base64 import b64encode
import json
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import SESSION_COOKIE, SESSION_MAX_AGE, safe_next, verify_password
from app.models import Member
from tests.auth_support import TEST_ORIGIN, TEST_PASSWORD, auth_app, login_form, register_form, sqlite_database, token_from


class RedirectTests(unittest.TestCase):
    def test_internal_path_preserved(self):
        self.assertEqual(safe_next("/checkout?product_id=abc&quantity=2"), "/checkout?product_id=abc&quantity=2")

    def test_redirect_attacks_rejected(self):
        for path in (
            None, "", "https://evil.example", "//evil.example", "///evil.example",
            "/\\evil.example", "/%5cevil.example", "/%2fevil.example", "/%252fevil.example",
            "/%0d%0aLocation:https://evil.example", "/login", "/register?next=/login",
            "/a/../login", "/%2e%2e/login", "/\tevil", "/%255cevil.example",
        ):
            with self.subTest(path=path):
                self.assertEqual(safe_next(path), "/products")


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.engine = sqlite_database()

        def session_dependency():
            with Session(self.engine, expire_on_commit=False) as session:
                yield session

        self.app = auth_app(session_dependency)
        self.client = TestClient(self.app, base_url=TEST_ORIGIN)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.engine.dispose()

    def test_registration_hash_normalization_and_duplicate(self):
        registered = register_form(self.client, email=" BUYER@EXAMPLE.COM ", next_path="/protected?item=2")
        self.assertEqual(registered.status_code, 303)
        self.assertIn("registered=1", registered.headers["location"])
        with Session(self.engine) as session:
            member = session.scalar(select(Member))
            self.assertEqual(member.email, "buyer@example.com")
            self.assertTrue(member.password_hash.startswith("$argon2id$"))
            self.assertTrue(verify_password(member.password_hash, TEST_PASSWORD))
        self.assertEqual(register_form(self.client).status_code, 409)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_invalid_registration_does_not_echo_password(self):
        token = token_from(self.client.get("/register"))
        response = self.client.post("/register", headers={"origin": TEST_ORIGIN}, data={
            "csrf_token": token, "email": "bad", "name": " ", "password": "secret-leak-test",
            "password_confirm": "different-password",
        })
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("secret-leak-test", response.text)

    def test_protected_redirect_and_login_return(self):
        redirect = self.client.get("/protected?item=2", follow_redirects=False)
        self.assertEqual(redirect.status_code, 303)
        self.assertEqual(redirect.headers["location"], "/login?next=%2Fprotected%3Fitem%3D2")
        register_form(self.client)
        response = login_form(self.client, next_path="/protected?item=2")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/protected?item=2")
        self.assertEqual(self.client.get(response.headers["location"]).json()["name"], "테스트회원")
        self.assertEqual(self.client.get("/api/auth/me").json()["email"], "buyer@example.com")

    def test_cookie_flags_and_csrf_rotation(self):
        register_form(self.client)
        old = token_from(self.client.get("/login"))
        response = login_form(self.client)
        cookie = response.headers["set-cookie"].lower()
        for flag in ("httponly", "secure", "samesite=lax", "path=/", "max-age=7200"):
            self.assertIn(flag, cookie)
        new = token_from(self.client.get("/products"))
        self.assertNotEqual(old, new)
        self.assertEqual(self.client.post("/logout", headers={"origin": TEST_ORIGIN}, data={"csrf_token": old}).status_code, 403)

    def test_csrf_rejects_missing_bad_origin_and_wrong_token(self):
        token = token_from(self.client.get("/login"))
        for headers, data in (
            ({"origin": TEST_ORIGIN}, {}),
            ({"origin": "https://evil.example"}, {"csrf_token": token}),
            ({}, {"csrf_token": token}),
            ({"origin": "null", "referer": TEST_ORIGIN}, {"csrf_token": token}),
            ({"origin": TEST_ORIGIN}, {"csrf_token": "invalid"}),
        ):
            response = self.client.post("/login", headers=headers, data=data)
            self.assertEqual(response.status_code, 403)

    def test_referer_fallback_and_json_csrf(self):
        register_form(self.client)
        token = token_from(self.client.get("/login"))
        login = self.client.post("/login", follow_redirects=False, headers={"referer": TEST_ORIGIN + "/login"}, data={
            "csrf_token": token, "email": "buyer@example.com", "password": TEST_PASSWORD,
        })
        self.assertEqual(login.status_code, 303)
        token = token_from(self.client.get("/products"))
        self.assertEqual(self.client.post("/api/test/write", json={}, headers={
            "origin": TEST_ORIGIN, "x-csrf-token": token,
        }).status_code, 200)

    def test_wrong_password_and_unknown_email_share_error(self):
        register_form(self.client)
        wrong = login_form(self.client, password="incorrect-password")
        unknown = login_form(self.client, email="unknown@example.com")
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(unknown.status_code, 401)
        self.assertIn("이메일 또는 비밀번호를 확인하세요.", wrong.text)
        self.assertIn("이메일 또는 비밀번호를 확인하세요.", unknown.text)

    def test_next_checked_on_post(self):
        register_form(self.client)
        response = login_form(self.client, next_path="//evil.example")
        self.assertEqual(response.headers["location"], "/products")

    def test_logout_and_old_cookie_replay(self):
        register_form(self.client)
        login_form(self.client)
        old_cookie = self.client.cookies.get(SESSION_COOKIE)
        token = token_from(self.client.get("/products"))
        self.assertEqual(self.client.get("/logout").status_code, 405)
        response = self.client.post("/logout", follow_redirects=False, headers={"origin": TEST_ORIGIN}, data={"csrf_token": token})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        with TestClient(self.app, base_url=TEST_ORIGIN) as other:
            other.cookies.set(SESSION_COOKIE, old_cookie)
            self.assertEqual(other.get("/api/auth/me").status_code, 401)

    def test_withdrawn_member_invalidates_existing_login(self):
        register_form(self.client)
        login_form(self.client)
        with Session(self.engine) as session:
            member = session.scalar(select(Member))
            member.status = "WITHDRAWN"
            session.commit()
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(login_form(self.client).status_code, 401)

    def test_tampered_and_expired_session(self):
        register_form(self.client)
        login_form(self.client)
        cookie = self.client.cookies.get(SESSION_COOKIE)
        with TestClient(self.app, base_url=TEST_ORIGIN) as other:
            other.cookies.set(SESSION_COOKIE, cookie + "tampered")
            self.assertEqual(other.get("/api/auth/me").status_code, 401)
        with Session(self.engine) as session:
            member = session.scalar(select(Member))
            data = b64encode(json.dumps({"member_id": str(member.id), "auth_version": 1, "csrf": "test"}).encode())
        with patch.object(TimestampSigner, "get_timestamp", return_value=int(time.time()) - SESSION_MAX_AGE - 1):
            expired = TimestampSigner(self.app.state.settings.session_secret.get_secret_value()).sign(data).decode()
        with TestClient(self.app, base_url=TEST_ORIGIN) as other:
            other.cookies.set(SESSION_COOKIE, expired)
            self.assertEqual(other.get("/api/auth/me").status_code, 401)


if __name__ == "__main__":
    unittest.main()
