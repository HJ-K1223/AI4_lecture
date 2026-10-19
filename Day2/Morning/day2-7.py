# 시나리오
# 백엔드 api에서 요청을 보낸 사용자 정보(dict)를 검증해서 접근 가능 여부와
# 부여할 기능을 판별하는 분기 로직을 작성

# 요구사항
# 1. 사용자 정보는 user_role(문자열)과 is_suspended(정지계정여부)
# 2. is_suspended가 True이면 즉시 "정지된 계정입니다."를 출력하고 검사를 종료
# 3. 역할은 admin, manager, user, guest 중 하나
# admin: "전체 시스템 관리 및 데이터 수정 권한 부여"
# manager: "팀 데이터 조회 및 수정 권한 부여"
# user: "개인 데이터 조회 권한 부여"
# guest: "게스트 권한 (읽기 전용 일부 허용)"
# 4. 정의되지 않은 역할일 경우 : [오류] 알 수 없는 권한입니다.

test_users = [
    {"username": "alpha", "user_role": "admin", "is_suspended": False},
    {"username": "bravo", "user_role": "user", "is_suspended": True},
    {"username": "charlie", "user_role": "manager", "is_suspended": False},
    {"username": "delta", "user_role": "hacker", "is_suspended": False},
]

# 내가 구성한 코드
# 대충 기능은 맞았지만 사용자명이 뜨지 않는 단점 발생
for user in test_users:
    username = user["username"] # value 뽑아내기
    role = user["user_role"]
    suspended = user["is_suspended"]
    if suspended == True:
        print('정지된 계정입니다.')
    elif role == "admin":
        print("전체 시스템 관리 및 데이터 수정 권한 부여")
    elif role == "user":
        print("개인 데이터 조회 권한 부여")
    elif role == "guest":
        print("게스트 권한 (읽기 전용 일부 허용)")
    else:
        print("[오류] 알 수 없는 권한입니다.")

# 강사님 코드
for user in test_users:
    username = user["username"] # value 뽑아내기
    role = user["user_role"]
    suspended = user["is_suspended"]

    print(f'username = {username}', end="\t")
    if user['is_suspended']:
        print('정지된 계정입니다.')
        continue

    if role == "admin":
        print("전체 시스템 관리 및 데이터 수정 권한 부여")
    elif role == "user":
        print("개인 데이터 조회 권한 부여")
    elif role == "guest":
        print("게스트 권한 (읽기 전용 일부 허용)")
    else:
        print("[오류] 알 수 없는 권한입니다.")

# GPT가 구성한 코드 1 (for문 활용 -> 내가 배운 선 내에서의 코드)
# continue 활용으로 가독성 증가 및 사용자명도 띄우게 함
for user in test_users:
    print(f"[{user['username']}]")

    # 정지 계정이면 현재 사용자의 검사를 종료하고 다음 사용자로 이동
    if user["is_suspended"]:
        print("정지된 계정입니다.")
        continue # 조건에 걸리면 아래 코드는 스킵하고 되돌아감

    role = user["user_role"]

    if role == "admin":
        print("전체 시스템 관리 및 데이터 수정 권한 부여")
    elif role == "manager":
        print("팀 데이터 조회 및 수정 권한 부여")
    elif role == "user":
        print("개인 데이터 조회 권한 부여")
    elif role == "guest":
        print("게스트 권한 (읽기 전용 일부 허용)")
    else:
        print("[오류] 알 수 없는 권한입니다.")

# GPT가 구성한 코드 2 (내가 아직 배우지 않은 내용 포함)
# 함수 사용으로 조금 더 깔끔하고 범용적인 코드
def check_user_access(user):
    # 정지 계정이면 현재 사용자의 검사를 즉시 종료
    if user["is_suspended"]:
        print("정지된 계정입니다.")
        return

    permissions = {
        "admin": "전체 시스템 관리 및 데이터 수정 권한 부여",
        "manager": "팀 데이터 조회 및 수정 권한 부여",
        "user": "개인 데이터 조회 권한 부여",
        "guest": "게스트 권한 (읽기 전용 일부 허용)",
    }

    message = permissions.get(
        user["user_role"],
        "[오류] 알 수 없는 권한입니다."
    )
    print(message)

for user in test_users:
    print(f"[{user['username']}]")
    check_user_access(user)

# 검색 프로그램 방식
search_name = input("검색할 사용자 이름을 입력하세요: ").strip() # strip은 공백을 줄여주는 기능

for user in test_users:
    if user["username"] == search_name:
        print(f"[{user['username']}]")
        check_user_access(user)
        break
else:
    print("해당 사용자를 찾을 수 없습니다.")