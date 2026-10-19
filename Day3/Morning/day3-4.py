from abc import abstractmethod # abc는 추상 기본 클래스

class PaymentGateway: # 추상 클래스는 객체가 되지는 못함
    @abstractmethod
    def process_payment(self, item:str, amount:int) -> str:
         pass

class CreditCardGateway(PaymentGateway):
     def process_payment(self, item:str, amount:int) -> str:
            return f'구매 품목2 : {item}, 수량2 : {amount}'

class BankGateway(PaymentGateway): # 추상 클래스를 상속받은 자식 클래스는 반드시 메서드를 구현해야 함
    pass

for obj in [CreditCardGateway(), BankGateway()]:
    print(obj.process_payment('식료품', 100))

