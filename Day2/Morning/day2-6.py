# 딕셔녀리
# key-value 한 쌍이 하나의 값

# 리스트 vs 딕셔너리
list_1 = [10,20,30,[1,2,3]]
dict_1 = {'kor':80,'eng':80,'math':90}

# dict.keys()
# dict.values()
# dict.items() # .이 붙어 있으면 객체로 생각

for i in list_1:
    print(i)

for i in dict_1: # key 값만 가지고 옴
    print(i)

for i in dict_1.values():
    print(i)

for i in dict_1.values():
    print(i,i[0]) # 변수에서의 []는 index

for i,j in dict_1.items():
    print(i,j)

# number1,number2=(10,20)와 같은 개념

for key,value in dict_1.items():
    print(f"key = {key} value={value}")

# 공부는 codex와 함께
