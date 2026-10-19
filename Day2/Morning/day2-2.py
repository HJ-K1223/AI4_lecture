# 논리연산자
isSuccess = True # is가 붙는경우 보통 가능한지를 묻고 있는 상태
isPass = False # 문법은 아니고 권장하는 규칙

if isSuccess or isPass:
    print('A')
else:
    print('B')

# 단락 평가(Short-circuit)
# 전체를 해석하지 않고 결과가 나오면 중간에 끊음
# and의 경우 False, or의 경우 True가 나오면 끊는 개념

if isSuccess and isPass: # 변수는 논리연산자로 길게 연결 가능
    print('성공')

def expensive_check():
    print("시간이 오래 걸리는 함수 실행")
    return True

is_active = False

if is_active and expensive_check(): # 단락 평가에 의해 expensive_check 함수가 실행되지 않음
    print('통과')
else:
    print('차단 (expensive_check 실행 안됨)')


# or 연산자일때의 단락평가
# is_active = True

# if is_active or expensive_check(): # 단락 평가에 의해 expensive_check 함수가 실행되지 않음
#     print('통과')
# else:
#     print('차단 (expensive_check 실행 안됨)')


# 객체가 생성되지 않은 경우(null/none)를 방어
user_profile = None

if user_profile is not None and user_profile.get('is_verified'): # None이 아니면 True
    print('인증된 사용자')
else:
    print('비인증된 사용자')