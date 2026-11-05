"""구매 기능 검증. 메모리 DB를 사용하며 실제 재고를 변경하지 않습니다."""

from uuid import UUID, uuid4
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import Update

from app.core.db import get_optional_db
from app.main import create_app
from app.models import Member, Order, OrderItem, Payment, Product
from app.services.shop import ShopError
from tests.auth_support import TEST_ORIGIN, login_form, register_form, sqlite_database, token_from
from tests.test_foundation import local_settings


class ShopTests(unittest.TestCase):
    def setUp(self):
        self.engine = sqlite_database()
        with Session(self.engine) as session:
            first = Product(sku="SHOP-1", name="머그컵", description="세라믹 머그컵", price=10000, stock=10)
            second = Product(sku="SHOP-2", name="에코백", description="면 가방", price=15000, stock=5)
            session.add_all([first, second])
            session.commit()
            self.product_id, self.second_id = str(first.id), str(second.id)

        def session_dependency():
            with Session(self.engine, expire_on_commit=False) as session:
                yield session

        self.app = create_app(local_settings(app_base_url=TEST_ORIGIN))
        self.app.dependency_overrides[get_optional_db] = session_dependency
        self.client = TestClient(self.app, base_url=TEST_ORIGIN)
        self.client.__enter__()
        register_form(self.client)
        login_form(self.client)

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.engine.dispose()

    def mutate(self, path, method="POST", data=None, client=None):
        client = client or self.client
        token = token_from(client.get("/products"))
        return client.request(method, path, headers={"origin": TEST_ORIGIN, "x-csrf-token": token},
                              **({"json": data} if data is not None else {}))

    def add(self, quantity=1, product_id=None):
        return self.mutate("/api/cart/items", data={"product_id": product_id or self.product_id, "quantity": quantity})

    def order_payload(self):
        cart = self.client.get("/api/cart").json()
        return {"cart_id": cart["id"], "quote": cart["quote"], "recipient_name": "테스트회원",
                "recipient_phone": "010-0000-0000", "shipping_address": "테스트 주소"}

    def pending_order(self, quantity=1):
        self.assertEqual(self.add(quantity).status_code, 201)
        response = self.mutate("/api/orders", data=self.order_payload())
        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def pay(self, order_id, key=None, **extra):
        return self.mutate("/api/payments", data={"order_id": order_id, "idempotency_key": key or str(uuid4()), **extra})

    def test_public_catalog_detail_and_pagination(self):
        with Session(self.engine) as session:
            session.add_all(Product(sku=f"MORE-{index}", name=f"샘플 {index}", price=1000, stock=1) for index in range(11))
            session.commit()
        with TestClient(self.app, base_url=TEST_ORIGIN) as guest:
            self.assertEqual(guest.get("/products").status_code, 200)
            page = guest.get("/products?page=2")
            self.assertEqual(page.status_code, 200)
            self.assertEqual(page.text.count('class="product-card"'), 1)
            self.assertEqual(guest.get("/products?page=3").status_code, 404)
            self.assertEqual(guest.get("/products?page=0").status_code, 422)
            self.assertIn("머그컵", guest.get("/products/" + self.product_id).text)

    def test_guest_checkout_next_preserves_product_and_quantity(self):
        with TestClient(self.app, base_url=TEST_ORIGIN) as guest:
            path = f"/checkout?product_id={self.product_id}&quantity=2"
            response = guest.get(path, follow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertIn("quantity%3D2", response.headers["location"])
            self.assertEqual(self.mutate("/api/cart/items", data={"product_id": self.product_id, "quantity": 2}, client=guest).status_code, 401)
            login = login_form(guest, next_path=path)
            self.assertEqual(login.headers["location"], path)
            self.assertEqual(guest.get(path).status_code, 200)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Order)), 0)

    def test_cart_merge_update_delete_and_quantity_validation(self):
        self.add(1)
        response = self.add(2)
        self.assertEqual(len(response.json()["items"]), 1)
        item = response.json()["items"][0]
        self.assertEqual(item["quantity"], 3)
        changed = self.mutate("/api/cart/items/" + item["id"], "PUT", {"quantity": 2})
        self.assertEqual(changed.json()["total_amount"], 20000)
        for invalid in (0, -1, 100, True, 1.5):
            self.assertEqual(self.add(invalid).status_code, 422)
        deleted = self.mutate("/api/cart/items/" + item["id"], "DELETE")
        self.assertEqual(deleted.json()["items"], [])
        with Session(self.engine) as session:
            self.assertEqual(session.get(Product, UUID(self.product_id)).stock, 10)
            self.assertEqual(session.scalar(select(Order)).total_amount, 0)

    def test_cart_read_does_not_create_cart(self):
        self.assertEqual(self.client.get("/cart").status_code, 200)
        self.assertIsNone(self.client.get("/api/cart").json()["id"])
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Order)), 0)

    def test_expired_or_missing_session_write_returns_401_before_csrf(self):
        with TestClient(self.app, base_url=TEST_ORIGIN) as guest:
            response = guest.post("/api/cart/items", json={"product_id": self.product_id, "quantity": 1},
                                  headers={"origin": TEST_ORIGIN, "x-csrf-token": "old-page-token"})
            self.assertEqual(response.status_code, 401)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Order)), 0)

    def test_price_change_requires_reconfirmation_and_snapshot_survives(self):
        self.add()
        payload = self.order_payload()
        with Session(self.engine) as session:
            session.get(Product, UUID(self.product_id)).price = 12000
            session.commit()
        response = self.mutate("/api/orders", data=payload)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "cart_changed")
        created = self.mutate("/api/orders", data=self.order_payload())
        order_id = created.json()["id"]
        with Session(self.engine) as session:
            product = session.get(Product, UUID(self.product_id))
            product.price, product.name = 18000, "변경된 상품명"
            session.commit()
        self.assertEqual(self.pay(order_id).json()["amount"], 12000)
        with Session(self.engine) as session:
            item = session.scalar(select(OrderItem))
            self.assertEqual((item.unit_price, item.product_name), (12000, "머그컵"))

    def test_order_creation_is_idempotent_and_quote_tamper_blocked(self):
        self.add()
        payload = self.order_payload()
        tampered = dict(payload, quote=payload["quote"] + "tampered")
        self.assertEqual(self.mutate("/api/orders", data=tampered).status_code, 409)
        first = self.mutate("/api/orders", data=payload)
        second = self.mutate("/api/orders", data=payload)
        self.assertEqual(first.json()["id"], second.json()["id"])
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Order)), 1)
            self.assertEqual(session.get(Product, UUID(self.product_id)).stock, 10)

    def test_payment_success_replay_and_different_key_deduct_once(self):
        order_id = self.pending_order(2)
        key = str(uuid4())
        first, repeated, new_key = self.pay(order_id, key), self.pay(order_id, key), self.pay(order_id)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["id"], repeated.json()["id"])
        self.assertEqual(first.json()["id"], new_key.json()["id"])
        self.assertIn("모의 결제가 완료되었습니다", self.client.get("/products").text)
        self.assertNotIn("모의 결제가 완료되었습니다", self.client.get("/products").text)
        with Session(self.engine) as session:
            self.assertEqual(session.get(Product, UUID(self.product_id)).stock, 8)
            self.assertEqual(session.get(Order, UUID(order_id)).status, "PAID")
            self.assertEqual(session.scalar(select(func.count()).select_from(Payment)), 1)

    def test_stock_failure_record_and_new_attempt(self):
        order_id = self.pending_order(2)
        with Session(self.engine) as session:
            session.get(Product, UUID(self.product_id)).stock = 0
            session.commit()
        key = str(uuid4())
        self.assertEqual(self.pay(order_id, key).status_code, 409)
        self.assertEqual(self.pay(order_id, key).status_code, 409)
        with Session(self.engine) as session:
            self.assertEqual(session.get(Order, UUID(order_id)).status, "PENDING")
            self.assertEqual(session.scalar(select(func.count()).select_from(Payment)), 1)
            session.get(Product, UUID(self.product_id)).stock = 2
            session.commit()
        self.assertEqual(self.pay(order_id).status_code, 200)
        with Session(self.engine) as session:
            self.assertEqual(session.get(Product, UUID(self.product_id)).stock, 0)

    def test_mock_decline_does_not_deduct_stock(self):
        order_id = self.pending_order()
        with patch("app.services.shop.MockPaymentProvider.charge", return_value={"succeeded": False}):
            self.assertEqual(self.pay(order_id).json()["status"], "FAILED")
        with Session(self.engine) as session:
            self.assertEqual(session.get(Product, UUID(self.product_id)).stock, 10)
            self.assertEqual(session.get(Order, UUID(order_id)).status, "PENDING")

    def test_mid_transaction_failure_rolls_back_all_products_and_payment(self):
        self.add(2)
        self.add(1, self.second_id)
        order_id = self.mutate("/api/orders", data=self.order_payload()).json()["id"]
        original = Session.execute
        updates = []

        def failing_execute(session, statement, *args, **kwargs):
            if isinstance(statement, Update) and statement.table.name == "products":
                updates.append(True)
                if len(updates) == 2:
                    raise ShopError("검증용 트랜잭션 중단", 503)
            return original(session, statement, *args, **kwargs)

        with patch.object(Session, "execute", failing_execute):
            self.assertEqual(self.pay(order_id).status_code, 503)
        self.assertEqual(len(updates), 2)
        with Session(self.engine) as session:
            self.assertEqual(session.get(Product, UUID(self.product_id)).stock, 10)
            self.assertEqual(session.get(Product, UUID(self.second_id)).stock, 5)
            self.assertEqual(session.get(Order, UUID(order_id)).status, "PENDING")
            self.assertEqual(session.scalar(select(func.count()).select_from(Payment)), 0)

    def test_client_amount_and_method_tampering_rejected(self):
        order_id = self.pending_order()
        self.assertEqual(self.pay(order_id, amount=1).status_code, 422)
        self.assertEqual(self.pay(order_id, method="REAL_CARD").status_code, 422)

    def test_other_member_cannot_modify_cart_or_pay_order(self):
        cart = self.add().json()
        item_id = cart["items"][0]["id"]
        order_id = self.mutate("/api/orders", data=self.order_payload()).json()["id"]
        with TestClient(self.app, base_url=TEST_ORIGIN) as other:
            register_form(other, email="other@example.com")
            login_form(other, email="other@example.com")
            self.assertEqual(other.get("/checkout/" + order_id).status_code, 404)
            self.assertEqual(self.mutate("/api/cart/items/" + item_id, "DELETE", client=other).status_code, 404)
            self.assertEqual(self.mutate("/api/payments", data={"order_id": order_id, "idempotency_key": str(uuid4())}, client=other).status_code, 404)


if __name__ == "__main__":
    unittest.main()
