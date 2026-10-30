"""실행: python -m unittest discover -s tests -v. 실제 DB는 변경하지 않습니다."""

import re
import unittest

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import make_url

from app.core.config import PROJECT_ROOT, Settings
from app.core.db import Base, Database
from app.main import create_app
from app.models import Product


def local_settings(**overrides):
    values = {
        "app_env": "development",
        "app_base_url": "http://127.0.0.1:8000",
        "allowed_hosts": ["testserver", "127.0.0.1"],
        "database_url": None,
        "session_secret": "test-only-session-secret-32-characters-minimum",
        "cookie_secure": True,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


class ConfigurationTests(unittest.TestCase):
    def test_split_database_settings_preserve_reserved_password(self):
        settings = local_settings(
            host="db.example.com", port=5432, dbname="postgres", user="postgres", password="p@ss:/?#%"
        )
        url = make_url(settings.database_url.get_secret_value())
        self.assertEqual(url.password, "p@ss:/?#%")
        self.assertEqual(url.query["sslmode"], "require")
        self.assertNotIn("p@ss", repr(settings))

    def test_incomplete_split_settings_rejected(self):
        with self.assertRaises(ValidationError):
            local_settings(host="db.example.com")

    def test_production_rejects_unsafe_configuration(self):
        production = {
            "app_env": "production",
            "app_base_url": "https://shop.example.com",
            "database_url": "postgresql://user:password@db.example.com:5432/postgres",
            "session_secret": "a" * 40,
        }
        for unsafe in (
            {"cookie_secure": False},
            {"app_base_url": "http://shop.example.com"},
            {"session_secret": "short"},
            {"database_url": None},
        ):
            with self.subTest(unsafe=list(unsafe)):
                with self.assertRaises(ValidationError):
                    local_settings(**(production | unsafe))
        self.assertEqual(local_settings(**production).app_env, "production")

    def test_database_validation_hides_secret(self):
        secret_url = "postgresql://user:do-not-leak@db.example.com/postgres?sslmode=disable"
        with self.assertRaises(ValidationError) as error:
            local_settings(database_url=secret_url)
        self.assertNotIn("do-not-leak", str(error.exception))

    def test_origin_rejects_credentials_and_paths(self):
        for invalid in ("https://user:secret@example.com", "https://example.com/cart", "https://example.com?next=x"):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                local_settings(app_base_url=invalid)

    def test_no_credentials_does_not_connect(self):
        database = Database(local_settings())
        self.assertIsNone(database.engine)
        with self.assertRaises(RuntimeError):
            database.check_schema()


class FoundationTests(unittest.TestCase):
    def test_layout_static_files_and_host_validation(self):
        with TestClient(create_app(local_settings())) as client:
            response = client.get("/", follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/products")
            page = client.get("/products")
            self.assertEqual(page.status_code, 503)
            self.assertIn('name="viewport"', page.text)
            self.assertIn('lang="ko"', page.text)
            self.assertIn("상품 목록을 불러올 수 없습니다", page.text)
            self.assertNotIn("DATABASE_URL", page.text)
            self.assertNotIn("SESSION_SECRET", page.text)
            self.assertEqual(client.get("/static/css/style.css").status_code, 200)
            self.assertEqual(client.get("/static/../core/config.py").status_code, 404)
            self.assertEqual(client.get("/products", headers={"host": "evil.example"}).status_code, 400)

    def test_jinja_escapes_display_name(self):
        with TestClient(create_app(local_settings(app_name='<script>alert("x")</script>'))) as client:
            page = client.get("/products")
            self.assertNotIn('<script>alert("x")</script>', page.text)
            self.assertIn("&lt;script&gt;", page.text)

    def test_orm_matches_sql_columns_and_schema(self):
        ddl = (PROJECT_ROOT / "db" / "schema.sql").read_text(encoding="utf-8-sig")
        tables = re.findall(r"CREATE TABLE shoppingmall\.(\w+) \((.*?)\n\);", ddl, re.S)
        self.assertEqual(len(tables), 5)
        self.assertEqual(len(Base.metadata.tables), 5)
        for name, definition in tables:
            expected = set(re.findall(
                r"^    (\w+) (?:uuid|varchar\(\d+\)|text|integer|bigint|boolean|timestamptz)\b",
                definition, re.M,
            ))
            # varchar 괄호 뒤에는 단어 경계가 없으므로 별도로 수집합니다.
            expected.update(re.findall(r"^    (\w+) varchar\(\d+\)", definition, re.M))
            table = Base.metadata.tables[f"shoppingmall.{name}"]
            self.assertEqual(set(table.columns.keys()), expected)
            for foreign_key in table.foreign_keys:
                self.assertEqual(foreign_key.column.table.schema, "shoppingmall")
        query = str(select(Product).compile(dialect=postgresql.dialect()))
        self.assertIn("shoppingmall.products", query)
        self.assertNotIn("public.products", query)


if __name__ == "__main__":
    unittest.main()
