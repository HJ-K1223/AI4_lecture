# 사용자로부터 데이터를 입력받아서 리스트에 저장하고 -> 변수가 많은 경우 하나씩 지정해주기 힘듦
# 저장된 리스트의 값 중에서 짝수만 출력해보기

scores = []
for i in range(5):
    score = int(input(f"{i+1}번째 숫자를 입력하세요 : ")) # f(format)는 출력의 형태를 조절
    scores.append(score)
print(scores)

for i in scores:
    if i % 2 == 0:
        print(i)

# 순환문은 비슷한 패턴이 반복될 때 사용