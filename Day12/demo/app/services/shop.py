"""소유권·행 잠금·서명된 가격 확인을 적용하는 구매 서비스."""

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.auth import LoginRequired
from app.models import Member, Order, OrderItem, Payment, Product

PAGE_SIZE = 12


class ShopError(Exception):
    def __init__(self, detail: str, status_code: int = 409, code: str = "conflict"):
        self.detail, self.status_code, self.code = detail, status_code, code


def public_image(path: str | None) -> str:
    if path and path.startswith("/static/images/") and ".." not in path and "\\" not in path:
        return path
    return "/static/images/placeholder.svg"


def product_data(product: Product) -> dict:
    return {
        "id": str(product.id), "name": product.name, "description": product.description,
        "price": product.price, "stock": product.stock, "image_path": public_image(product.image_path),
    }


def catalog(db: Session, page: int) -> dict:
    total = db.scalar(select(func.count()).select_from(Product).where(Product.is_active.is_(True)))
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    if page > pages:
        raise ShopError("존재하지 않는 상품 페이지입니다.", 404, "not_found")
    products = db.scalars(select(Product).where(Product.is_active.is_(True))
                          .order_by(Product.created_at.desc(), Product.id.desc())
                          .offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)).all()
    return {"products": [product_data(item) for item in products], "page": page, "pages": pages, "total": total}


def find_product(db: Session, product_id: UUID) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id, Product.is_active.is_(True)))
    if product is None:
        raise ShopError("상품을 찾을 수 없습니다.", 404, "not_found")
    return product


def lock_member(db: Session, member: Member) -> Member:
    expected_version = member.auth_version
    current = db.scalar(select(Member).where(Member.id == member.id).with_for_update()
                        .execution_options(populate_existing=True))
    if current is None or current.status != "ACTIVE" or current.auth_version != expected_version:
        raise LoginRequired()
    return current


def owned_order(db: Session, member_id: UUID, order_id: UUID, *, lock=False) -> Order:
    statement = select(Order).where(Order.id == order_id, Order.member_id == member_id)
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    order = db.scalar(statement)
    if order is None:
        raise ShopError("주문을 찾을 수 없습니다.", 404, "not_found")
    return order


def cart_order(db: Session, member_id: UUID, *, lock=False) -> Order | None:
    statement = select(Order).where(Order.member_id == member_id, Order.status == "CART")
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    return db.scalar(statement)


def cart_rows(db: Session, order_id: UUID):
    return db.execute(select(OrderItem, Product).join(Product, Product.id == OrderItem.product_id)
                      .where(OrderItem.order_id == order_id).order_by(Product.id)).all()


def quote_payload(member_id, cart_id, rows) -> dict:
    content = [[str(product.id), item.quantity, product.price, product.name] for item, product in rows]
    digest = hashlib.sha256(json.dumps(content, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return {"member": str(member_id), "cart": str(cart_id), "digest": digest}


def quote_signer(secret: str):
    return URLSafeTimedSerializer(secret, salt="shoppingmall-cart-quote")


def cart_snapshot(db: Session, member_id: UUID, secret: str) -> dict:
    order = cart_order(db, member_id)
    rows = cart_rows(db, order.id) if order else []
    items = [{
        "id": str(item.id), "product_id": str(product.id), "name": product.name,
        "unit_price": product.price, "quantity": item.quantity, "line_total": product.price * item.quantity,
        "stock": product.stock, "is_active": product.is_active, "image_path": public_image(product.image_path),
    } for item, product in rows]
    return {
        "id": str(order.id) if order else None, "items": items,
        "total_amount": sum(item["line_total"] for item in items),
        "quote": quote_signer(secret).dumps(quote_payload(member_id, order.id, rows)) if order and rows else None,
    }


def refresh_cart_total(db: Session, order: Order) -> None:
    db.flush()
    order.total_amount = db.scalar(select(func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0))
                                  .where(OrderItem.order_id == order.id))


def check_product_quantity(product: Product, quantity: int) -> None:
    if not product.is_active:
        raise ShopError("판매가 종료된 상품입니다.", code="unavailable")
    if quantity > 99:
        raise ShopError("같은 상품은 최대 99개까지 담을 수 있습니다.", code="quantity_limit")
    if product.stock < quantity:
        raise ShopError("선택한 수량만큼 재고가 없습니다. 수량을 확인해 주세요.", code="out_of_stock")


def add_item(db: Session, member: Member, product_id: UUID, quantity: int) -> None:
    lock_member(db, member)
    order = cart_order(db, member.id, lock=True)
    if order is None:
        order = Order(member_id=member.id)
        db.add(order)
        db.flush()
    product = db.scalar(select(Product).where(Product.id == product_id).with_for_update()
                        .execution_options(populate_existing=True))
    if product is None:
        raise ShopError("상품을 찾을 수 없습니다.", 404, "not_found")
    item = db.scalar(select(OrderItem).where(OrderItem.order_id == order.id, OrderItem.product_id == product.id))
    new_quantity = (item.quantity if item else 0) + quantity
    check_product_quantity(product, new_quantity)
    if item is None:
        item = OrderItem(order_id=order.id, product_id=product.id, quantity=new_quantity,
                         product_name=product.name, unit_price=product.price)
        db.add(item)
    else:
        item.quantity, item.unit_price, item.product_name = new_quantity, product.price, product.name
    refresh_cart_total(db, order)
    db.commit()


def change_item(db: Session, member: Member, item_id: UUID, quantity: int | None) -> None:
    lock_member(db, member)
    order = cart_order(db, member.id, lock=True)
    item = db.scalar(select(OrderItem).where(OrderItem.id == item_id, OrderItem.order_id == order.id)) if order else None
    if item is None:
        raise ShopError("장바구니 상품을 찾을 수 없습니다.", 404, "not_found")
    if quantity is None:
        db.delete(item)
    else:
        product = db.scalar(select(Product).where(Product.id == item.product_id).with_for_update()
                            .execution_options(populate_existing=True))
        check_product_quantity(product, quantity)
        item.quantity, item.unit_price, item.product_name = quantity, product.price, product.name
    refresh_cart_total(db, order)
    db.commit()


def create_order(db: Session, member: Member, data, secret: str) -> Order:
    lock_member(db, member)
    try:
        signed = quote_signer(secret).loads(data.quote, max_age=1800)
    except BadSignature:
        raise ShopError("장바구니 확인 시간이 지났습니다. 새로고침 후 다시 확인해 주세요.", code="cart_changed")
    if not isinstance(signed, dict) or signed.get("member") != str(member.id) or signed.get("cart") != str(data.cart_id):
        raise ShopError("장바구니 확인값이 올바르지 않습니다.", 403, "invalid_quote")
    order = owned_order(db, member.id, data.cart_id, lock=True)
    if order.status in ("PENDING", "PAID"):
        return order
    if order.status != "CART":
        raise ShopError("주문할 수 없는 장바구니입니다.")
    # 모든 쓰기 서비스에서 회원 → 주문 → 상품 ID 오름차순 잠금 순서를 지킵니다.
    product_ids = db.scalars(select(OrderItem.product_id).where(OrderItem.order_id == order.id)).all()
    if not product_ids:
        raise ShopError("장바구니에 상품을 담아 주세요.", code="empty_cart")
    db.scalars(select(Product).where(Product.id.in_(product_ids)).order_by(Product.id).with_for_update()
               .execution_options(populate_existing=True)).all()
    rows = cart_rows(db, order.id)
    if signed != quote_payload(member.id, order.id, rows):
        raise ShopError("상품·수량·가격이 변경되었습니다. 장바구니를 다시 확인해 주세요.", code="cart_changed")
    for item, product in rows:
        check_product_quantity(product, item.quantity)
        item.unit_price, item.product_name = product.price, product.name
    order.total_amount = sum(product.price * item.quantity for item, product in rows)
    order.recipient_name, order.recipient_phone = data.recipient_name, data.recipient_phone
    order.shipping_address = data.shipping_address
    order.status, order.ordered_at = "PENDING", datetime.now(timezone.utc)
    db.commit()
    return order


def order_snapshot(db: Session, member_id: UUID, order_id: UUID) -> dict:
    order = owned_order(db, member_id, order_id)
    if order.status == "CART":
        raise ShopError("아직 생성되지 않은 주문입니다.", 404, "not_found")
    rows = cart_rows(db, order.id)
    return {
        "id": str(order.id), "status": order.status, "total_amount": order.total_amount,
        "recipient_name": order.recipient_name, "recipient_phone": order.recipient_phone,
        "shipping_address": order.shipping_address,
        "items": [{"name": item.product_name, "unit_price": item.unit_price, "quantity": item.quantity,
                   "line_total": item.unit_price * item.quantity, "image_path": public_image(product.image_path)}
                  for item, product in rows],
    }


class MockPaymentProvider:
    def charge(self, *, amount: int, currency: str, request_id: UUID) -> dict:
        # 실제 카드 정보나 외부 결제 API를 사용하지 않습니다.
        return {"succeeded": True, "transaction_id": "MOCK-" + str(request_id)}


def payment_result(payment: Payment) -> dict:
    succeeded = payment.status == "SUCCEEDED"
    return {
        "id": str(payment.id), "order_id": str(payment.order_id), "status": payment.status,
        "amount": payment.amount, "code": payment.failure_code,
        "detail": "결제가 완료되었습니다." if succeeded else "결제하지 못했습니다. 상품과 재고를 확인한 뒤 다시 시도하세요.",
        "redirect_url": "/products" if succeeded else None,
    }


def pay_order(db: Session, member: Member, data, provider=None) -> dict:
    lock_member(db, member)
    order = owned_order(db, member.id, data.order_id, lock=True)
    previous = db.scalar(select(Payment).where(Payment.idempotency_key == data.idempotency_key))
    if previous:
        if previous.order_id != order.id or previous.amount != order.total_amount or previous.method != data.method:
            raise ShopError("다른 결제 요청에 사용된 재시도 키입니다.", code="idempotency_conflict")
        return payment_result(previous)
    if order.status == "PAID":
        successful = db.scalar(select(Payment).where(Payment.order_id == order.id, Payment.status == "SUCCEEDED"))
        if successful is None:
            raise ShopError("주문 결제 기록을 확인할 수 없습니다.")
        return payment_result(successful)
    if order.status != "PENDING":
        raise ShopError("결제할 수 없는 주문 상태입니다.")
    items = db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    if not items or sum(item.unit_price * item.quantity for item in items) != order.total_amount:
        raise ShopError("주문 금액을 확인할 수 없습니다.", code="invalid_amount")
    products = db.scalars(select(Product).where(Product.id.in_([item.product_id for item in items]))
                          .order_by(Product.id).with_for_update().execution_options(populate_existing=True)).all()
    by_id = {product.id: product for product in products}
    payment = Payment(order_id=order.id, amount=order.total_amount, method=data.method,
                      idempotency_key=data.idempotency_key)
    db.add(payment)
    # 전역 멱등키 충돌은 재고 변경 전에 DB 제약조건으로 감지합니다.
    db.flush()
    if any(item.product_id not in by_id or not by_id[item.product_id].is_active
           or by_id[item.product_id].stock < item.quantity for item in items):
        payment.status, payment.failure_code = "FAILED", "OUT_OF_STOCK"
        db.commit()
        return payment_result(payment)
    try:
        result = (provider or MockPaymentProvider()).charge(
            amount=order.total_amount, currency=order.currency, request_id=data.idempotency_key
        )
    except Exception:
        raise ShopError("결제 처리 중 오류가 발생했습니다. 같은 요청으로 다시 시도해 주세요.", 503, "payment_unavailable")
    if not result["succeeded"]:
        payment.status, payment.failure_code = "FAILED", "MOCK_DECLINED"
        db.commit()
        return payment_result(payment)
    for item in items:
        changed = db.execute(update(Product).where(Product.id == item.product_id, Product.stock >= item.quantity)
                             .values(stock=Product.stock - item.quantity))
        if changed.rowcount != 1:
            raise ShopError("재고가 변경되었습니다. 다시 시도해 주세요.", code="out_of_stock")
    now = datetime.now(timezone.utc)
    payment.status, payment.transaction_id, payment.paid_at = "SUCCEEDED", result["transaction_id"], now
    order.status, order.paid_at = "PAID", now
    db.commit()
    return payment_result(payment)
