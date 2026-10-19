// Python 정답 표시용 데이터 (answers.py 기준)
const PYTHON_ANSWERS = [
  "def answer_1():\n    number1 = 100\n    number2 = 200\n    print(\"number1 + number2 =\", number1 + number2)",
  "def answer_2():\n    score = int(input(\"점수를 입력하세요 : \"))\n    if score >= 60:\n        print(\"합격\")\n    else:\n        print(\"불합격\")",
  "def answer_3():\n    scores = []\n    for i in range(5):\n        score = int(input(f\"{i + 1}번째 숫자를 입력하세요 : \"))\n        scores.append(score)\n    print(scores)\n\n    for score in scores:\n        if score % 2 == 0:\n            print(score)",
  "def answer_4():\n    for multiplier in range(1, 5):\n        for table in range(2, 5):\n            print(f\"{table} x {multiplier} = {table * multiplier}\", end=\"\\t\")\n        print()",
  "def answer_5():\n    com_number = random.randint(1, 100)\n    count = 0\n\n    while True:\n        user_number = int(input(\"1~100 : \"))\n        count += 1\n        if user_number > com_number:\n            print(\"컴퓨터보다 큽니다.\")\n        elif user_number < com_number:\n            print(\"컴퓨터보다 작습니다.\")\n        else:\n            print(f\"정답입니다. 총 시도 횟수는 : {count}\")\n            break"
];
