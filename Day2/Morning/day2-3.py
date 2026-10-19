# 변수와 함수를 하나의 집합으로 관리하는 것이 class
# class를 활성화시켜주는 것이 객체
# 객체는 변수가 됨

class SafeProfile: # 객체의 설계도로 이해 가능
    def __init__(self):
        pass
    def get(self,key):
        return True
    def set(self,key):
        return True

user_profile = SafeProfile() # 같은 class로 여러 개를 만들 수 있음
user_profile2 = SafeProfile()
user_profile3 = SafeProfile()

print(user_profile.get('is_verified')) # get을 호출

if user_profile and user_profile.get('is_verified'): # get을 이용하기 위한 user_profile을 체크 및 실행 방어
    print('성공')
else:
    print('실패')

# 여러 개의 함수를 묶을 경우 class 사용