from dataclasses import dataclass

@dataclass
class PaymentReceipt:
    method: str
    buyer: str
    amount: int
    fee: int
    status: str

    @property
    def net_amount(self) -> int:
        return self.amount - self.fee

PaymentReceipt("card", "홍길동", 100, 5, "normal")

obj = PaymentReceipt("card", "홍길동", 100, 5, "normal")
print(obj.net_amount) # 변수처럼 사용하면 class 내부에서는 함수로 작동