"""모의 결제 API. 실제 PG는 호출하지 않습니다."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import required_member
from app.core.db import get_db
from app.models import Member
from app.schemas.shop import PaymentInput
from app.services.shop import ShopError, pay_order

router = APIRouter()


@router.post("/api/payments")
def payment(data: PaymentInput, request: Request, member: Member = Depends(required_member), db: Session = Depends(get_db)):
    try:
        result = pay_order(db, member, data)
    except IntegrityError:
        db.rollback()
        raise ShopError("이미 사용된 결제 요청입니다. 주문 결과를 다시 확인해 주세요.", code="idempotency_conflict")
    if result["status"] == "SUCCEEDED":
        request.session["payment_complete"] = True
    return JSONResponse(result, status_code=200 if result["status"] == "SUCCEEDED" else 409)
