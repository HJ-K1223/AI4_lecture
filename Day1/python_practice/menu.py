"""주제와 실행 모드를 선택하는 콘솔 메뉴."""

from .exercises import practice_1, practice_2, practice_3, practice_4, practice_5
from .answers import answer_1, answer_2, answer_3, answer_4, answer_5


# 아래는 실습 실행용 메뉴입니다. 첫 복습에서는 수정하지 않아도 됩니다.
def main():
    practices = [practice_1, practice_2, practice_3, practice_4, practice_5]
    answers = [answer_1, answer_2, answer_3, answer_4, answer_5]
    while True:
        print("\n===== Python 1일 차 복습 =====")
        print("1. 변수와 출력")
        print("2. 입력과 조건문")
        print("3. 리스트와 반복문")
        print("4. 중첩 반복문과 구구단")
        print("5. 숫자 맞추기 게임")
        print("0. 종료")
        choice = input("주제 선택: ").strip()
        if choice == "0":
            break
        if choice not in ("1", "2", "3", "4", "5"):
            print("0~5 중에서 선택하세요.")
            continue

        mode = input("1. 직접 작성한 코드 / 2. 정답 예제: ").strip()
        if mode not in ("1", "2"):
            print("1 또는 2를 선택하세요.")
            continue

        try:
            index = int(choice) - 1
            if mode == "1":
                print("practice 함수에 코드를 작성한 뒤 실행하세요.")
                practices[index]()
            else:
                answers[index]()
        except ValueError:
            print("숫자 입력에는 정수를 입력하세요. 메뉴로 돌아갑니다.")


if __name__ == "__main__":
    main()

