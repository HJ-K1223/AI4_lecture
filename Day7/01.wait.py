# 비동기
import asyncio # 비동기를 위한 호출x
import time
from time import perf_counter

async def make_drink(name): # 비동기인 경우 함수에도 비동기(async)를 표시해줘야함
    print(f'{name} 만들기 시작')
    # time.sleep(2) # 동기의 경우
    await asyncio.sleep(2) # 비동기 작업 : await로 기다림 부여
    print(f'{name} 완성')
    return name

async def main(): # 동기와 비동기 비교
    start = perf_counter()
    await make_drink('커피')
    await make_drink('차')
    print(f'순서대로 기다림 : {perf_counter() - start:.2f}초\n')

    start = perf_counter()
    result = await asyncio.gather(make_drink('커피'),make_drink('차'))
    print(f'함께 기다림 : {perf_counter() - start:.2f}초\n')
    print('결과',result)

if __name__ == '__main__':
    asyncio.run(main()) # 비동기함수 실행을 위해서는 이런 형태로 실행해야함