list_1 = [1,2,3,4,5]
list_2 = [10,20,30,40,50]
print(*list_1)

print([*list_1,*list_2])

# list는 * 1개, dictionary는 * 2개로 내부 데이터를 풀어서 사용

dict_1 = {'a':1,'b':2,'c':3}

# dict_1['a']=0
# dict_1['c']=100
dict_1.update({'a':0,'c':100})

# 1. 데이터 조회 get(/tasks)
# 2. 데이터 추가 post(/tasks)
# 3. 특정번호의 데이터 조회 get(/tasks/{task_id})
# 4. 특정번호의 데이터를 전부 교체 put(/tasks/{task_id})
# 5. 특정번호의 데이터를 일부 수정 patch(/tasks/{task_id})
