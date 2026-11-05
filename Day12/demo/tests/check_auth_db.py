"""실제 Supabase 인증 검증. 모든 쓰기는 외부 트랜잭션을 롤백해 제거합니다."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.db import Database, get_optional_db
from app.core.security import SESSION_COOKIE, verify_password
from app.main import create_app
from app.models import Member
from tests.auth_support import TEST_ORIGIN, TEST_PASSWORD, login_form, register_form, token_from


def main() -> int:
    database = None
    try:
        settings = Settings(app_base_url=TEST_ORIGIN, allowed_hosts=["testserver"], cookie_secure=True)
        database = Database(settings)
        if database.engine is None:
            raise RuntimeError("DB 설정 없음")
        email = "authcheck+" + uuid4().hex + "@example.com"
        with database.engine.connect() as connection:
            transaction = connection.begin()
            try:
                def test_session():
                    # 서비스가 commit하더라도 외부 트랜잭션은 커밋되지 않습니다.
                    with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as session:
                        yield session

                app = create_app(settings)
                app.dependency_overrides[get_optional_db] = test_session
                with TestClient(app, base_url=TEST_ORIGIN) as client:
                    assert register_form(client, email=email, next_path="/products?from=auth-check").status_code == 303
                    assert register_form(client, email=email).status_code == 409
                    response = login_form(client, email=email, next_path="/products?from=auth-check")
                    assert response.status_code == 303
                    assert response.headers["location"] == "/products?from=auth-check"
                    assert client.get("/api/auth/me").status_code == 200
                    old_cookie = client.cookies.get(SESSION_COOKIE)
                    token = token_from(client.get("/products"))
                    assert client.post("/logout", headers={"origin": TEST_ORIGIN}, follow_redirects=False,
                                       data={"csrf_token": token}).status_code == 303
                    assert client.get("/api/auth/me").status_code == 401
                    with TestClient(app, base_url=TEST_ORIGIN) as other:
                        other.cookies.set(SESSION_COOKIE, old_cookie)
                        assert other.get("/api/auth/me").status_code == 401
                with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                    member = session.scalar(select(Member).where(Member.email == email))
                    assert member is not None and member.auth_version == 2
                    assert verify_password(member.password_hash, TEST_PASSWORD)
            finally:
                transaction.rollback()
            remaining = connection.scalar(select(func.count()).select_from(Member).where(Member.email == email))
            assert remaining == 0
    except Exception:
        print("Supabase 인증 검증 실패. 비밀값 보호를 위해 예외 원문은 출력하지 않습니다.")
        return 1
    finally:
        if database is not None:
            database.dispose()
    print("Supabase 인증 검증 완료: 가입·중복 방지·로그인·복귀·로그아웃·이전 쿠키 거부 확인.")
    print("테스트 트랜잭션 롤백 완료: 테스트 회원이 DB에 남지 않음을 확인했습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
