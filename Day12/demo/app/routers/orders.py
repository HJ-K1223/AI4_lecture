"""상품 선택 복귀·주문 생성·결제 확인 화면."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import required_member
from app.core.db import get_db
from app.core.templates import render
from app.models import Member
from app.schemas.shop import OrderInput
from app.services.shop import create_order, find_product, order_snapshot, product_data

router = APIRouter()


@router.get("/checkout")
def selected_product(request: Request, product_id: UUID, quantity: int = Query(default=1, ge=1, le=99),
                     member: Member = Depends(required_member), db: Session = Depends(get_db)):
    return render(request, "selection.html", member=member, product=product_data(find_product(db, product_id)), quantity=quantity)


@router.post("/api/orders", status_code=201)
def submit_order(data: OrderInput, request: Request, member: Member = Depends(required_member), db: Session = Depends(get_db)):
    order = create_order(db, member, data, request.app.state.settings.session_secret.get_secret_value())
    return {"id": str(order.id), "status": order.status, "checkout_url": "/checkout/" + str(order.id)}


@router.get("/checkout/{order_id}")
def checkout_page(request: Request, order_id: UUID, member: Member = Depends(required_member), db: Session = Depends(get_db)):
    return render(request, "checkout.html", member=member, order=order_snapshot(db, member.id, order_id), payment_key=str(uuid4()))
