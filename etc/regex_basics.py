r"""Python 표준 라이브러리 re로 배우는 정규표현식 기본 예제.

자주 쓰는 기호
    r"..."   : 역슬래시를 그대로 전달하는 원시 문자열
    \d       : 숫자 한 글자 (유니코드 숫자도 포함)
    [0-9]    : 0부터 9까지의 숫자 한 글자
    \s       : 공백, 탭, 줄바꿈 등의 공백 문자 한 글자
    .        : 줄바꿈을 제외한 임의의 한 글자 (기본 설정)
    [a-z]    : 소문자 알파벳 한 글자
    [가-힣]  : 완성형 한글 음절 한 글자
    +        : 바로 앞 패턴이 1번 이상 반복
    *        : 바로 앞 패턴이 0번 이상 반복
    ?        : 바로 앞 패턴이 0번 또는 1번 등장
    {3}      : 바로 앞 패턴이 정확히 3번 반복
    ^ / $    : 문자열 시작 / 끝 위치 ($는 마지막 줄바꿈 앞에도 일치 가능)
    (...)    : 일치한 내용을 그룹으로 묶기
    |        : 여러 패턴 중 하나 선택
"""

import re


def run_examples() -> None:
    # 1. search: 문자열 어디에서든 첫 번째 일치 구간을 찾습니다.
    # 일치하면 Match 객체, 없으면 None을 반환합니다.
    found = re.search(r"\d+", "레벨 25 달성!")
    assert found is not None
    assert found.group() == "25"  # group()으로 찾은 문자열을 꺼냅니다.
    assert re.search(r"\d+", "숫자 없음") is None
    print("1. 첫 숫자:", found.group())

    # 2. findall: 일치한 문자열을 모두 리스트로 반환합니다.
    numbers = re.findall(r"\d+", "물약 3개, 골드 150개")
    assert numbers == ["3", "150"]
    assert re.findall(r"\d+", "숫자 없음") == []
    print("2. 모든 숫자:", numbers)

    # 3. match: 문자열 시작 위치에서만 패턴을 검사합니다.
    assert re.match(r"Hello", "Hello, player!") is not None
    assert re.match(r"Hello", "Say Hello!") is None
    print("3. 시작에서 찾기:", bool(re.match(r"Hello", "Hello, player!")))

    # 4. fullmatch: 문자열 전체가 패턴과 일치하는지 검사합니다.
    # [0-9]{3}은 숫자 3개, 하이픈은 실제 '-' 문자를 뜻합니다.
    phone_pattern = r"010-[0-9]{4}-[0-9]{4}"
    assert re.fullmatch(phone_pattern, "010-1234-5678") is not None
    assert re.fullmatch(phone_pattern, "010-123-5678") is None
    assert re.fullmatch(phone_pattern, "연락처: 010-1234-5678") is None
    print("4. 전화번호 형식:", bool(re.fullmatch(phone_pattern, "010-1234-5678")))

    # 5. sub: 일치하는 부분을 다른 문자열로 치환합니다.
    # flags=re.IGNORECASE를 지정하면 대소문자를 구분하지 않습니다.
    masked = re.sub(r"bad", "***", "BAD player, bad chat", flags=re.IGNORECASE)
    assert masked == "*** player, *** chat"
    print("5. 치환:", masked)

    # 6. split: 패턴을 구분자로 사용하여 문자열을 나눕니다.
    # 대괄호는 그 안의 문자 중 하나, +는 연속된 구분자도 묶어서 처리합니다.
    words = re.split(r"[,;\s]+", "사과,배;포도 바나나")
    assert words == ["사과", "배", "포도", "바나나"]
    print("6. 나누기:", words)

    # 7. 그룹: 날짜의 연도, 월, 일을 각각 꺼냅니다.
    # 형식만 검사하므로 실제 달력에 존재하는 날짜인지는 별도 확인이 필요합니다.
    date = re.fullmatch(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", "2026-10-15")
    assert date is not None
    assert date.groups() == ("2026", "10", "15")
    assert date.group(1) == "2026"
    print("7. 날짜 그룹:", date.groups())

    # 8. compile: 같은 패턴을 여러 번 사용할 때 재사용할 객체를 만듭니다.
    # |는 '또는'을 뜻하며, [가-힣]+는 연속된 한글 음절을 찾습니다.
    language_pattern = re.compile(r"[가-힣]+|[a-z]+", re.IGNORECASE)
    tokens = language_pattern.findall("안녕 Python 123!")
    assert tokens == ["안녕", "Python"]
    print("8. 한글과 영문:", tokens)

    # 9. escape: 특수문자가 포함된 사용자 입력을 문자 그대로 검색합니다.
    # '.'은 원래 임의의 글자지만 escape를 거치면 실제 마침표를 뜻합니다.
    literal_pattern = re.escape("a.b")
    assert re.findall(literal_pattern, "a.b aXb") == ["a.b"]
    print("9. 특수문자 그대로 찾기:", re.findall(literal_pattern, "a.b aXb"))

    print("모든 assert 테스트 통과!")


# 다른 파일에서 import하면 실행되지 않고, 직접 실행할 때만 예제와 테스트를 실행합니다.
if __name__ == "__main__":
    run_examples()
