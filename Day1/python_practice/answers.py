"""실습 문제의 정답 예제입니다. 먼저 exercises.py에서 풀어 보세요."""

import random


def answer_1():
    number1 = 100
    number2 = 200
    print("number1 + number2 =", number1 + number2)


def answer_2():
    score = int(input("점수를 입력하세요 : "))
    if score >= 60:
        print("합격")
    else:
        print("불합격")


def answer_3():
    scores = []
    for i in range(5):
        score = int(input(f"{i + 1}번째 숫자를 입력하세요 : "))
        scores.append(score)
    print(scores)

    for score in scores:
        if score % 2 == 0:
            print(score)


def answer_4():
    for multiplier in range(1, 5):
        for table in range(2, 5):
            print(f"{table} x {multiplier} = {table * multiplier}", end="\t")
        print()


def answer_5():
    com_number = random.randint(1, 100)
    count = 0

    while True:
        user_number = int(input("1~100 : "))
        count += 1
        if user_number > com_number:
            print("컴퓨터보다 큽니다.")
        elif user_number < com_number:
            print("컴퓨터보다 작습니다.")
        else:
            print(f"정답입니다. 총 시도 횟수는 : {count}")
            break



