"""브라우저 미리보기용 샘플. 실제 Supabase에는 쓰지 않습니다."""

from uuid import UUID
from sqlalchemy.orm import Session
from app.models import Product


def seed_preview(engine):
    samples = (
        ("크림 머그컵", 10000, "mug"), ("데일리 에코백", 15000, "bag"),
        ("포레스트 노트", 6500, "notebook"), ("우드향 캔들", 18000, "candle"),
        ("데일리 보틀", 14000, "bottle"), ("오트밀 볼", 12000, "bowl"),
        ("라떼 머그컵", 12000, "mug"), ("산책 에코백", 13000, "bag"),
        ("오늘의 노트", 4500, "notebook"), ("포근한 캔들", 14500, "candle"),
        ("산책 보틀", 11000, "bottle"), ("작은 요거트 볼", 9000, "bowl"),
    )
    with Session(engine) as session:
        session.add_all(Product(
            id=UUID(f"10000000-0000-4000-8000-{index:012d}"), sku=f"PREVIEW-{index}",
            name=name, description="일상에서 편하게 사용하는 소담상점 샘플 상품입니다.",
            price=price, stock=30, image_path=f"/static/images/{image}.svg",
        ) for index, (name, price, image) in enumerate(samples, start=1))
        session.commit()
