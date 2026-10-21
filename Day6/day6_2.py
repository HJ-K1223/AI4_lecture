# 필수/기본값, 모델 생성/검증
from pydantic import BaseModel, ValidationError

class Member(BaseModel):
    username:str
    age:int
    active:bool = True
    nickname:str|None = None

class MemberOut(Member):
    id:int

def main() -> None:
     member = Member(username = 'lee',age = 20)
     print(member)
     raw = {'username':'kim','age':'34','active':False}
     parsed=Member.model_validate(raw) # 에러가 없으면 할당
     print(parsed, 'age 타입 :', type(parsed.age).__name__)
     print('nickname 기본값',parsed.nickname)

    # 필수 필드 누락
     try:
        Member(username='park',age=20)
        # Member.model_validate({'username':'park'})
        # memberout 객체 생성
        memberout = MemberOut(id=1,username='park',age=20)
        print(memberout)
     except ValidationError as e:
        print(e.errors()[0]['loc'], e.errors()[0]['type'])
    
    
        
if __name__ == '__main__': # 자신이 main이 아닌 곳에서는 실행하지 않게 하는 명령
   main()
    # print(m.username)
    # print(__name__) # 자신이 아닌 곳에서 실행되는 경우, 파일명만 보내줌
