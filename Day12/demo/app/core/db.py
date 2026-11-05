"""서버 전용 PostgreSQL 연결. 시작 시 테이블을 자동 생성하지 않습니다."""

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings

DB_SCHEMA = "shoppingmall"


class Base(DeclarativeBase):
    metadata = MetaData(schema=DB_SCHEMA)


class Database:
    def __init__(self, settings: Settings):
        self.engine = None
        self.session_factory = None
        if settings.database_url is not None:
            url = make_url(settings.database_url.get_secret_value()).set(drivername="postgresql+psycopg")
            self.engine = create_engine(
                url,
                pool_pre_ping=True,
                pool_size=3,
                max_overflow=2,
                pool_timeout=5,
                hide_parameters=True,
                connect_args={
                    "sslmode": url.query.get("sslmode", "require"),
                    "connect_timeout": 5,
                    "prepare_threshold": None,
                    "application_name": "shoppingmall",
                },
            )
            self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def check_schema(self) -> None:
        """연결·스키마·필수 테이블의 읽기 권한을 데이터 반환 없이 확인합니다."""
        if self.engine is None:
            raise RuntimeError("DATABASE_URL이 설정되지 않았습니다.")
        with self.engine.connect() as connection:
            # 고정된 SQL만 사용하며 실제 회원·상품 데이터는 가져오지 않습니다.
            connection.execute(text("SELECT 1"))
            for statement in (
                "SELECT id FROM shoppingmall.members LIMIT 0",
                "SELECT id FROM shoppingmall.products LIMIT 0",
                "SELECT id FROM shoppingmall.orders LIMIT 0",
                "SELECT id FROM shoppingmall.order_items LIMIT 0",
                "SELECT id FROM shoppingmall.payments LIMIT 0",
            ):
                connection.execute(text(statement))

    def dispose(self) -> None:
        if self.engine is not None:
            self.engine.dispose()


def get_optional_db(request: Request) -> Iterator[Session | None]:
    factory = request.app.state.database.session_factory
    if factory is None:
        yield None
    else:
        with factory() as session:
            yield session


def get_db(db: Session | None = Depends(get_optional_db)) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="현재 서비스를 준비하고 있습니다.")
    # 같은 요청의 인증 검사와 서비스가 동일한 세션을 사용합니다.
    # 커밋은 서비스가 명시적으로 수행하고 미완료 변경은 종료 시 롤백됩니다.
    return db
