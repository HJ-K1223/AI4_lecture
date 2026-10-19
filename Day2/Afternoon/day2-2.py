# zip
list_1 = ['a','b','c']
list_2 = [100,200,300]
result = zip(list_1,list_2) # 순서대로 묶어주는 역할
for i in result:            # 계속 사용하고 싶으면 리스트로 묶어주면 된다
    print(i)

for i in result: # zip으로 만든 객체는 한 번 사용하면 다시 사용할 수 없는
    print(i)     # 이터레이터(iterator)이기 때문에 조건문 이후에 딕셔너리가 만들어지지 않는 것

# zip으로 생성한 객체를 딕셔너리로 변환
result = dict(result)
print(result)

