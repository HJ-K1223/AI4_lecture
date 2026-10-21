# pydantic
# 데이터의 유효성 및 타입을 체크
# 기능이 구현된 클래스를 상속받아 pydantic 클래스 또는 모델을 만들 수 있음
from pydantic import BaseModel, ValidationError

# 일반 python class
class NormalClass:
    def __init__(self,name:str,age:int):
        self.name = name
        self.age = age
        print(f'{self.name} : 나이 {self.age}')

params = {'age':20,'name':'홍길동'}
user1 = NormalClass(**params)

# pydantic class
class PydanticUser(BaseModel):
    name : str
    age : int

user2 = PydanticUser(**params)

try:
    user3=PydanticUser(**params)
    print('일반 클래스',user3.age)
    print('데이터 클래스',type(user3.age))
except ValidationError as e:
    print('에러')



    
    