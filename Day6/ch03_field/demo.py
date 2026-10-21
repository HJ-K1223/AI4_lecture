# Field : 범위, 길이, 패턴에 대해서 엄격하게 검사
from pydantic import BaseModel, Field, ValidationError, EmailStr, ConfigDict
from typing import Literal

class Registration(BaseModel):
    # 좌우 공백을 줄이는 명령 # extra = 'forbid' : 만든 변수 이외에는 추가 x
    model_config = ConfigDict(str_strip_whitespace=True,extra='forbid') 
    # 최소, 최대 길이 제한
    name : str = Field(min_length=2, max_length=20)
    age : int = Field(ge=14, le=100)
    # Email의 경우 EmailStr을 사용하여 특유의 형태를 바로 사용 가능
    email : EmailStr
    # 미리 지정한 값만 사용 가능
    level : Literal['basic','premium'] = 'basic' # Union 기능과 비슷(Union : 타입별 / Literal : 값별)
    # 특정 패턴만 인식
    code : str = Field(pattern=r'STU-[0-9]{4}$') #STU-0001
    # 자동으로 변환하지 않고 엄격하게
    agreed : bool=Field(strict=True)

def main()->None:
    user1 = Registration(name='lee',age='50',email='lee@abc.com',code='STU-0001',agreed=True)
    print('검증성공 :', user1.model_dump())
    print('오류 확인')
    try:
        user2 = Registration(name='lee',age='500',email='lee@abccom',code='STU-001')
        print(user2.age)
    except ValidationError as e:
        print(e.errors()[0]['loc'],e.errors()[0]['type'])

if __name__ =='__main__':
    main()