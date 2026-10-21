"""불변 주문 객체와 등급별 할인 정책."""

from dataclasses import dataclass
from typing import ClassVar


class InvalidOrderError(ValueError):
    """주문 데이터가 유효하지 않을 때 발생하는 예외."""


@dataclass(frozen=True)
class Order:
    # 등급 이름은 예시이며 실제 서비스의 명칭에 맞게 변경할 수 있습니다.
    SILVER: ClassVar[int] = 1
    GOLD: ClassVar[int] = 2
    VIP: ClassVar[int] = 3
    DISCOUNT_RATES: ClassVar[dict[int, float]] = {
        SILVER: 0.05,
        GOLD: 0.10,
        VIP: 0.20,
    }
    COUPON_DISCOUNT: ClassVar[int] = 3000

    u_type: int
    price: float
    qty: int
    coupon: str = "NO"

    def __post_init__(self) -> None:
        if self.price < 0:
            raise InvalidOrderError("가격은 0 이상이어야 합니다.")
        if self.qty < 0:
            raise InvalidOrderError("수량은 0 이상이어야 합니다.")
        if self.u_type not in self.DISCOUNT_RATES:
            raise InvalidOrderError(f"미등록 등급입니다: {self.u_type}")

    def calculate_total(self) -> int:
        total = self.price * self.qty
        total *= 1 - self.DISCOUNT_RATES[self.u_type]
        if self.coupon == "YES":
            total -= self.COUPON_DISCOUNT
        return int(max(total, 0))


if __name__ == "__main__":
    order = Order(u_type=Order.GOLD, price=10000, qty=2, coupon="YES")
    print(order.calculate_total())  # 15000
