# 디버깅
items = ['정상','불량','불량','정상']
for item in items:
    if item == '불량':
        items.remove('불량') # index가 꼬여서 정상적인 동작을 하지 않음

print(f'검수결과 : {items}')

# 원본은 건드리지 않고 새 리스트를 만들어서 변환하는 방식

# 리스트 컴프리헨션
items = ['정상','불량','불량','정상']
filtered_items = [item for item in items if item == '정상']
print(f'검수결과 : {filtered_items}')
