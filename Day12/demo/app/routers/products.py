"""비로그인 상태에서도 접근할 수 있는 상품 화면."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import optional_member
from app.core.db import get_optional_db
from app.core.templates import render
from app.models import Member
from app.services.shop import ShopError, catalog, find_product, product_data

router = APIRouter()


@router.get("/products")
def products(request: Request, page: int = Query(default=1, ge=1, le=1000000),
             member: Member | None = Depends(optional_member), db: Session | None = Depends(get_optional_db)):
    if db is None:
        raise ShopError("상품 목록을 불러올 수 없습니다. 잠시 후 다시 확인해 주세요.", 503, "unavailable")
    return render(request, "products.html", member=member, active_page="products", **catalog(db, page),
                  paid=request.session.pop("payment_complete", False))


@router.get("/products/{product_id}")
def product_detail(request: Request, product_id: UUID, quantity: int = Query(default=1, ge=1, le=99),
                   member: Member | None = Depends(optional_member), db: Session | None = Depends(get_optional_db)):
    if db is None:
        raise ShopError("상품을 불러올 수 없습니다.", 503, "unavailable")
    return render(request, "product_detail.html", member=member, active_page="products",
                  product=product_data(find_product(db, product_id)), quantity=quantity)
