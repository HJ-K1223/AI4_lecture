"""점수 범위를 검증하고 정규화합니다. 오류 발생 시 부분 결과를 반환하지 않습니다."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import isfinite


class InvalidScoreError(ValueError):
    """입력 구조 또는 점수가 유효하지 않을 때 발생합니다."""


@dataclass(frozen=True)
class ScorePreprocessor:
    max_score: float = 100.0
    precision: int = 4

    def __post_init__(self) -> None:
        if isinstance(self.max_score, bool) or not isinstance(self.max_score, (int, float)):
            raise ValueError("만점은 숫자여야 합니다.")
        try:
            valid_max = isfinite(self.max_score) and self.max_score > 0
        except OverflowError:
            valid_max = False
        if not valid_max:
            raise ValueError("만점은 유한한 양수여야 합니다.")
        if isinstance(self.precision, bool) or not isinstance(self.precision, int):
            raise ValueError("반올림 자릿수는 정수여야 합니다.")
        if self.precision < 0:
            raise ValueError("반올림 자릿수는 0 이상이어야 합니다.")

    def _parse_score(self, row: object, row_number: int) -> float:
        if not isinstance(row, Mapping):
            raise InvalidScoreError(f"{row_number}행: 행은 딕셔너리 형태여야 합니다.")
        if "score" not in row:
            raise InvalidScoreError(f"{row_number}행: 'score' 키가 없습니다.")

        value = row["score"]
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise InvalidScoreError(f"{row_number}행: 점수는 숫자 또는 숫자 문자열이어야 합니다: {value!r}")
        try:
            score = float(value)
        except (ValueError, OverflowError) as exc:
            raise InvalidScoreError(f"{row_number}행: 숫자로 변환할 수 없는 점수입니다: {value!r}") from exc

        if not isfinite(score):
            raise InvalidScoreError(f"{row_number}행: 점수는 유한한 숫자여야 합니다: {value!r}")
        if not 0 <= score <= self.max_score:
            raise InvalidScoreError(f"{row_number}행: 점수는 0~{self.max_score} 범위여야 합니다: {value!r}")
        return score

    def preprocess(self, data: Iterable[Mapping[str, object]]) -> list[float]:
        if isinstance(data, (str, bytes, Mapping)):
            raise InvalidScoreError("입력은 행들의 반복 가능한 컬렉션이어야 합니다.")
        try:
            rows = iter(data)
        except TypeError as exc:
            raise InvalidScoreError("입력은 행들의 반복 가능한 컬렉션이어야 합니다.") from exc

        result: list[float] = []
        for row_number, row in enumerate(rows, start=1):
            score = self._parse_score(row, row_number)
            result.append(round(score / self.max_score, self.precision))
        return result


def preprocess(data: Iterable[Mapping[str, object]]) -> list[float]:
    """100점 만점, 소수점 넷째 자리 반올림을 기본으로 적용합니다."""
    return ScorePreprocessor().preprocess(data)


def main() -> None:
    """터미널에서 점수를 입력받고 정규화 결과를 출력합니다."""
    print("점수 정규화 프로그램 (100점 만점)")
    print("점수를 쉼표 또는 공백으로 구분해 입력하세요. 예: 85, 92.5, 100")
    print("종료하려면 q를 입력하세요.")

    while True:
        try:
            user_input = input("\n점수 입력: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n프로그램을 종료합니다.")
            return

        if user_input.lower() == "q":
            print("프로그램을 종료합니다.")
            return
        if not user_input:
            print("점수를 하나 이상 입력해 주세요.")
            continue

        # 쉼표를 사용한 경우 빈 항목도 검증하여 입력 누락을 알립니다.
        if "," in user_input:
            groups = user_input.split(",")
            if any(not group.strip() for group in groups):
                print("오류: 쉼표 사이에 빠진 점수가 있습니다. 다시 입력해 주세요.")
                continue
        values = user_input.replace(",", " ").split()
        rows: list[Mapping[str, object]] = [{"score": value} for value in values]

        try:
            results = preprocess(rows)
        except InvalidScoreError as exc:
            print(f"오류: {exc}")
            print("0~100 사이의 숫자로 다시 입력해 주세요.")
            continue

        print(f"정규화 결과: {results}")
        for value, result in zip(values, results):
            print(f"  {value}점 -> {result}")


if __name__ == "__main__":
    main()

