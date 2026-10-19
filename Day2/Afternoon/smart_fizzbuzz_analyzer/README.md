# Mission 1: Smart FizzBuzz Analyzer

## 1. 문제 정의

1부터 limit까지의 정수를 순회하며 각 숫자를 FizzBuzz 규칙에 따라
정확히 하나의 항목으로 분류하고, 항목별 개수를 계산한다.

## 2. 입력값

- 함수: `analyze_fizzbuzz(limit: int) -> dict`
- `limit`: 순회 범위의 끝을 나타내는 정수. 범위에 limit 자체도 포함한다.
- 정수가 아닌 입력은 이 문제의 처리 범위에 포함하지 않는다.

## 3. 출력값

다음 네 개의 키와 정수 카운트를 가진 딕셔너리를 반환한다.

```python
{"FizzBuzz": int, "Fizz": int, "Buzz": int, "Number": int}
```

예: `analyze_fizzbuzz(15)`의 반환값은 다음과 같다.

```python
{"FizzBuzz": 1, "Fizz": 4, "Buzz": 2, "Number": 8}
```

## 4. 제약조건

- `for` 문으로 1부터 limit까지 순회한다.
- `if` / `elif` / `else`로 다음 순서에 따라 분류한다.
  1. 3과 5의 공통 배수: FizzBuzz
  2. 나머지 3의 배수: Fizz
  3. 나머지 5의 배수: Buzz
  4. 그 외: Number
- 공통 배수를 먼저 검사하여 중복 집계하지 않는다.
- limit가 1 미만이면 모든 카운트를 0으로 반환한다.
- 카운트 합은 `max(limit, 0)`과 같아야 한다.
- 시간 복잡도는 O(limit), 추가 공간 복잡도는 O(1)이다
  (limit가 1 미만인 경우 시간 복잡도도 O(1)).

## 5. assert 테스트 케이스

`test_main.py`에서 Python의 `assert` 문으로 다음 입력을 검증한다.

| 입력 | FizzBuzz | Fizz | Buzz | Number | 검증 목적 |
| ---: | ---: | ---: | ---: | ---: | --- |
| -10 | 0 | 0 | 0 | 0 | 음수 |
| 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 0 | 0 | 1 | 최소 양수 |
| 3 | 0 | 1 | 0 | 2 | 첫 Fizz |
| 5 | 0 | 1 | 1 | 3 | 첫 Buzz |
| 14 | 0 | 4 | 2 | 8 | 공통 배수 직전 |
| 15 | 1 | 4 | 2 | 8 | 첫 FizzBuzz와 상한 포함 |
| 16 | 1 | 4 | 2 | 9 | 공통 배수 직후 |
| 30 | 2 | 8 | 4 | 16 | 여러 공통 배수 |
| 100 | 6 | 27 | 14 | 53 | 더 큰 범위 |

각 결과의 정확한 값, 카운트 합계, 카운트의 정수 여부 및 음수 여부도 검사한다.
`assert`가 활성화되도록 `-O` 옵션 없이 테스트를 실행한다.

## 6. 실행 방법

이 폴더에서 Python으로 실행한다.

```powershell
python main.py 15
python test_main.py
```

인수를 생략하여 `python main.py`로 실행하면 표준 입력으로 정수를 받는다.
