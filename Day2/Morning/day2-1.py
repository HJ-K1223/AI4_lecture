#if-elif-else
score = int(input('점수 : '))
if score >=90:
    print('A')
elif score >=80:
    print('B')
elif score >=70:
    print('C')
else:
    print('F')

# 조건문 안에 조건문도 가능하지만
# 가독성이 떨어지고 복잡해짐

# 점수 제한 등 디테일한 조건을 걸어줄 수도 있음