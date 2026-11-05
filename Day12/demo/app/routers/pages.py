"""기본 진입 경로를 상품 목록으로 이동합니다."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/products", status_code=303)


