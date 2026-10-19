"""assert 문으로 경계값과 FizzBuzz 분류 결과를 검증한다."""

from main import analyze_fizzbuzz


def test_analyze_fizzbuzz():
    cases = [
        (-10, {"FizzBuzz": 0, "Fizz": 0, "Buzz": 0, "Number": 0}),
        (0, {"FizzBuzz": 0, "Fizz": 0, "Buzz": 0, "Number": 0}),
        (1, {"FizzBuzz": 0, "Fizz": 0, "Buzz": 0, "Number": 1}),
        (3, {"FizzBuzz": 0, "Fizz": 1, "Buzz": 0, "Number": 2}),
        (5, {"FizzBuzz": 0, "Fizz": 1, "Buzz": 1, "Number": 3}),
        (14, {"FizzBuzz": 0, "Fizz": 4, "Buzz": 2, "Number": 8}),
        (15, {"FizzBuzz": 1, "Fizz": 4, "Buzz": 2, "Number": 8}),
        (16, {"FizzBuzz": 1, "Fizz": 4, "Buzz": 2, "Number": 9}),
        (30, {"FizzBuzz": 2, "Fizz": 8, "Buzz": 4, "Number": 16}),
        (100, {"FizzBuzz": 6, "Fizz": 27, "Buzz": 14, "Number": 53}),
    ]

    for limit, expected in cases:
        actual = analyze_fizzbuzz(limit)
        assert actual == expected, f"limit={limit}: {actual} != {expected}"
        assert sum(actual.values()) == max(limit, 0)
        assert all(type(count) is int and count >= 0 for count in actual.values())
        print(f"PASS: limit={limit}, result={actual}")

    print(f"All {len(cases)} test cases passed.")


if __name__ == "__main__":
    test_analyze_fizzbuzz()
