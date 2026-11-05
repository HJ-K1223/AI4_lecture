"""Supabase 구매·동시성 검증. 생성한 검증용 행만 롤백 또는 정리합니다."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.db import Database, get_optional_db
from app.main import create_app
from app.models import Member, Order, OrderItem, Payment, Product
from app.schemas.shop import PaymentInput
from app.services.auth import DUMMY_PASSWORD_HASH
from app.services.shop import pay_order
from tests.auth_support import TEST_ORIGIN, login_form, register_form, token_from


def rollback_purchase(engine, settings):
    email = "shopcheck+" + uuid4().hex + "@example.com"
    product_id = uuid4()
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                session.add(Product(id=product_id, sku="CHECK-" + uuid4().hex, name="구매검증 상품", price=10000, stock=5))
                session.commit()

            def test_session():
                with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as session:
                    yield session

            app = create_app(settings)
            app.dependency_overrides[get_optional_db] = test_session
            with TestClient(app, base_url=TEST_ORIGIN) as client:
                next_path = f"/checkout?product_id={product_id}&quantity=2"
                redirect = client.get(next_path, follow_redirects=False)
                assert redirect.status_code == 303 and "quantity%3D2" in redirect.headers["location"]
                assert register_form(client, email=email, next_path=next_path).status_code == 303
                assert login_form(client, email=email, next_path=next_path).headers["location"] == next_path
                assert client.get(next_path).status_code == 200

                def post(path, data):
                    token = token_from(client.get("/products"))
                    return client.post(path, json=data, headers={"origin": TEST_ORIGIN, "x-csrf-token": token})

                assert post("/api/cart/items", {"product_id": str(product_id), "quantity": 2}).status_code == 201
                cart = client.get("/api/cart").json()
                order = post("/api/orders", {"cart_id": cart["id"], "quote": cart["quote"],
                    "recipient_name": "구매검증회원", "recipient_phone": "010-0000-0000", "shipping_address": "검증 주소"})
                assert order.status_code == 201
                data = {"order_id": order.json()["id"], "idempotency_key": str(uuid4())}
                first, replay = post("/api/payments", data), post("/api/payments", data)
                assert first.status_code == 200 and replay.status_code == 200
                assert first.json()["id"] == replay.json()["id"]
                assert client.get(order.json()["checkout_url"]).status_code == 200
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                assert session.get(Product, product_id).stock == 3
                order_row = session.scalar(select(Order).join(Member).where(Member.email == email))
                assert order_row.status == "PAID" and order_row.total_amount == 20000
                assert session.scalar(select(func.count()).select_from(Payment).where(Payment.order_id == order_row.id)) == 1
        finally:
            transaction.rollback()
        assert connection.scalar(select(func.count()).select_from(Product).where(Product.id == product_id)) == 0
        assert connection.scalar(select(func.count()).select_from(Member).where(Member.email == email)) == 0


def concurrency_purchase(engine):
    # 별도 연결이 서로의 행을 볼 수 있도록 검증용 행만 커밋하고 finally에서 제거합니다.
    member_ids, product_ids, order_ids = [uuid4(), uuid4()], [uuid4(), uuid4(), uuid4()], [uuid4() for _ in range(4)]
    try:
        with Session(engine) as session:
            session.add_all(Member(id=mid, email=f"concurrency+{mid.hex}@example.com", name="동시성검증",
                                   password_hash=DUMMY_PASSWORD_HASH) for mid in member_ids)
            session.add_all(Product(id=pid, sku="CONCURRENT-" + pid.hex, name="동시성검증 상품", price=1000,
                                    stock=1 if index == 0 else 2) for index, pid in enumerate(product_ids))
            session.flush()
            specifications = [(member_ids[0], product_ids[0]), (member_ids[1], product_ids[0]),
                              (member_ids[0], product_ids[1]), (member_ids[0], product_ids[2])]
            for order_id, (member_id, product_id) in zip(order_ids, specifications):
                session.add(Order(id=order_id, member_id=member_id, status="PENDING", total_amount=1000,
                                  ordered_at=datetime.now(timezone.utc), recipient_name="검증", recipient_phone="000", shipping_address="검증"))
            session.flush()
            for order_id, (_, product_id) in zip(order_ids, specifications):
                session.add(OrderItem(order_id=order_id, product_id=product_id, product_name="동시성검증 상품", unit_price=1000, quantity=1))
            session.commit()

        def race(specifications):
            barrier = Barrier(2)

            def worker(spec):
                member_id, order_id, key = spec
                with Session(engine, expire_on_commit=False) as session:
                    member = session.get(Member, member_id)
                    barrier.wait(timeout=15)
                    return pay_order(session, member, PaymentInput(order_id=order_id, idempotency_key=key))

            with ThreadPoolExecutor(max_workers=2) as executor:
                return list(executor.map(worker, specifications))

        last_stock = race([(member_ids[0], order_ids[0], uuid4()), (member_ids[1], order_ids[1], uuid4())])
        assert sorted(result["status"] for result in last_stock) == ["FAILED", "SUCCEEDED"]
        key = uuid4()
        duplicate = race([(member_ids[0], order_ids[2], key), (member_ids[0], order_ids[2], key)])
        assert duplicate[0]["id"] == duplicate[1]["id"]
        different_keys = race([(member_ids[0], order_ids[3], uuid4()), (member_ids[0], order_ids[3], uuid4())])
        assert different_keys[0]["id"] == different_keys[1]["id"]
        with Session(engine) as session:
            assert [session.get(Product, pid).stock for pid in product_ids] == [0, 1, 1]
            assert session.scalar(select(func.count()).select_from(Payment).where(
                Payment.order_id.in_(order_ids), Payment.status == "SUCCEEDED")) == 3
    finally:
        with Session(engine) as session:
            # 사용자 데이터에는 접근하지 않고 위에서 생성한 UUID만 정확히 지정합니다.
            session.execute(delete(Payment).where(Payment.order_id.in_(order_ids)))
            session.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
            session.execute(delete(Order).where(Order.id.in_(order_ids), Order.member_id.in_(member_ids)))
            session.execute(delete(Product).where(Product.id.in_(product_ids)))
            session.execute(delete(Member).where(Member.id.in_(member_ids)))
            session.commit()
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(Member).where(Member.id.in_(member_ids))) == 0
            assert session.scalar(select(func.count()).select_from(Product).where(Product.id.in_(product_ids))) == 0
            assert session.scalar(select(func.count()).select_from(Order).where(Order.id.in_(order_ids))) == 0


def main() -> int:
    database = None
    try:
        settings = Settings(app_base_url=TEST_ORIGIN, allowed_hosts=["testserver"], cookie_secure=True)
        database = Database(settings)
        if database.engine is None:
            raise RuntimeError("DB 설정 없음")
        rollback_purchase(database.engine, settings)
        print("Supabase 구매 확인 완료: 로그인 복귀·주문·결제·재시도·재고 차감. 테스트 트랜잭션 롤백 완료.")
        concurrency_purchase(database.engine)
        print("Supabase 동시성 확인 완료: 마지막 재고 경쟁·같은 키·다른 키의 동시 결제. 검증용 행 정리 확인 완료.")
    except Exception:
        print("구매 검증 실패. 비밀값 보호를 위해 예외 원문은 출력하지 않습니다.")
        return 1
    finally:
        if database is not None:
            database.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
