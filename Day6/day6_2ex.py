from pydantic import BaseModel, ValidationError

# TODO : Book 모델의 필드를 정의하시오
# title:str(필수), price:int(필수), in_stock:bool=True, note:str|None=None

class Book(BaseModel):
    title:str
    price:int
    in_stock:bool=True
    note:str|None=None

def main()->None:
    # TODO : Book(title='파이썬 기초',price='19000') 만들기
    book1 = Book(title='파이썬 기초',price='19000')
    print(book1)
    # TODO : model_dump() 호출, 가격이 int로 변환되었는지 확인하기
    print('model_dump() 호출 :',book1.model_dump())
    print('type 확인 :',type(book1.price).__name__)
    # TODO : title 누락 시 ValidationError 확인
    try:
            book2 = Book(price=20000)
            print(book2)
    except ValidationError as e:
            print(e.errors()[0]['loc'], e.errors()[0]['type'])
    # print('TODO를 완성하세요.')

if __name__ == '__main__':
    main()