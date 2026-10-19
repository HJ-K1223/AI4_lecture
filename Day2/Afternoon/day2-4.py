# 리스트 컴프리헨션
# 리스트를 바로 가공할 때 사용하기 좋음

result = []

list_1 = [1,2,3,4,5]
# for i in list_1:
#     if i % 2 == 0:
#         result.append(i)

result = [i for i in list_1 if i%2 == 0] # 삼항연산자와 비슷

print(result)

list_2 = ['1','2','3','4','5']

result2 = [int(i) for i in list_2 if int(i)>3]

print(result2)

menu = ['아메리카노','라떼','초코']
ice_menu = ['아이스'+i for i in menu]
len_menu = [len(i) for i in menu if len(i)%2==0]

'''
['참' if 조건 else '거짓' for i in 집합] --> if-else 문에서는 for 문이 뒤로 간다
['참' for i in 집합 if 조건]
'''

print(ice_menu)
print(len_menu)

ages = [20,15,60,25,30,45,5]
print([i for i in ages if i>=20])
print(['성인' if i>=20 else '미성년' for i in ages])

print(set([1,2,3,4,5,6,7,8,1,2,3,4,5])) # 중복 제외

bad_words = ['바보','멍충이','멍텅구리','']
words = sorted(set(word for word in bad_words if word), key=len, reverse=True)
print(words)

print("|".join(words))

import re
pattern = "|".join(re.escape(word) for word in words)
re.sub(pattern, lambda match: "*" * len(match.group(0)),
                  chat_message, flags=re.IGNORECASE)