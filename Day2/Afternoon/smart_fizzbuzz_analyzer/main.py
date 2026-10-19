"""1부터 limit까지의 숫자를 FizzBuzz 규칙으로 분류하고 개수를 반환한다."""

import json
import sys


def analyze_fizzbuzz(limit: int) -> dict:
    counts = {"FizzBuzz": 0, "Fizz": 0, "Buzz": 0, "Number": 0}

    if limit < 1:
        return counts

    for number in range(1, limit + 1):
        if number % 3 == 0 and number % 5 == 0:
            counts["FizzBuzz"] += 1
        elif number % 3 == 0:
            counts["Fizz"] += 1
        elif number % 5 == 0:
            counts["Buzz"] += 1
        else:
            counts["Number"] += 1

    return counts


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else int(input())
    print(json.dumps(analyze_fizzbuzz(limit)))
