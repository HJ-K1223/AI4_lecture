"""로그인 회원의 장바구니 화면 및 JSON API."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import required_member
from app.core.db import get_db
from app.core.templates import render
from app.models import Member
from app.schemas.shop import CartItemInput, QuantityInput
from app.services.shop import add_item, cart_snapshot, change_item

router = APIRouter()


def current_cart(request, member, db):
    return cart_snapshot(db, member.id, request.app.state.settings.session_secret.get_secret_value())


@router.get("/cart")
def cart_page(request: Request, member: Member = Depends(required_member), db: Session = Depends(get_db)):
    return render(request, "cart.html", member=member, active_page="cart", cart=current_cart(request, member, db))


@router.get("/api/cart")
def cart_api(request: Request, member: Member = Depends(required_member), db: Session = Depends(get_db)):
    return current_cart(request, member, db)


@router.post("/api/cart/items", status_code=201)
def add_cart_item(data: CartItemInput, request: Request, member: Member = Depends(required_member), db: Session = Depends(get_db)):
    add_item(db, member, data.product_id, data.quantity)
    return current_cart(request, member, db)


@router.put("/api/cart/items/{item_id}")
def update_cart_item(item_id: UUID, data: QuantityInput, request: Request,
                     member: Member = Depends(required_member), db: Session = Depends(get_db)):
    change_item(db, member, item_id, data.quantity)
    return current_cart(request, member, db)


@router.delete("/api/cart/items/{item_id}")
def delete_cart_item(item_id: UUID, request: Request, member: Member = Depends(required_member), db: Session = Depends(get_db)):
    change_item(db, member, item_id, None)
    return current_cart(request, member, db)
