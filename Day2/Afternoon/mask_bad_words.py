import re #


def mask_bad_words(chat_message: str, bad_words: list[str]) -> str: # python은 강제성이 없어서 지금의 str의 경우는 문법이 아니라 정보제공 측면
    # 문자열을 글자별 리스트로 바꾸면 특정 위치의 글자를 수정할 수 있습니다.
    masked_characters = list(chat_message)

    for word in bad_words:
        # 빈 문자열은 금지어 검사에서 제외합니다.
        if not word:
            continue

        # 특수문자를 글자 그대로 찾고, 영어 대소문자는 구분하지 않습니다.
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        start = 0

        while True:
            # 원본에서 검색해야 앞서 마스킹한 부분과 겹치는 금지어도 찾습니다.
            match = pattern.search(chat_message, start)
            if match is None:
                break

            # 찾은 구간의 각 글자를 별표 하나로 바꿉니다.
            for index in range(match.start(), match.end()):
                masked_characters[index] = "*"

            # 한 칸만 이동하여 겹치는 금지어도 검색합니다.
            start = match.start() + 1

    # 수정한 글자들을 하나의 문자열로 합쳐 반환합니다.
    return "".join(masked_characters)


def run_tests() -> None:
    # 기본 동작과 대소문자 처리
    assert mask_bad_words("너는 바보야", ["바보"]) == "너는 **야"
    assert mask_bad_words("BAD Bad bad", ["bad"]) == "*** *** ***"
    assert mask_bad_words("good", ["bad"]) == "good"

    # 빈 메시지, 빈 목록, 빈 금지어
    assert mask_bad_words("", ["bad"]) == ""
    assert mask_bad_words("hello", []) == "hello"
    assert mask_bad_words("hello", [""]) == "hello"
    assert mask_bad_words("bad", ["", "bad"]) == "***"

    # 반복되는 금지어와 중복 목록
    assert mask_bad_words("badbad", ["bad"]) == "******"
    assert mask_bad_words("bad!", ["bad", "bad"]) == "***!"

    # 정규식 특수문자도 글자 그대로 처리
    assert mask_bad_words("a.b aXb", ["a.b"]) == "*** aXb"
    assert mask_bad_words("[bad] +", ["[bad]", "+"]) == "***** *"

    # 겹치는 금지어와 목록 순서
    assert mask_bad_words("ababa", ["aba"]) == "*****"
    assert mask_bad_words("abcde", ["abc", "cde"]) == "*****"
    assert mask_bad_words("abcde", ["cde", "abc"]) == "*****"

    # 단어 내부의 금지어 처리 및 다른 문자 보존
    assert mask_bad_words("badly", ["bad"]) == "***ly"
    assert mask_bad_words("Hi,\tBAD!\nOK 😀", ["bad"]) == "Hi,\t***!\nOK 😀"

    print("16개 테스트 모두 통과!")


# 직접 실행할 때만 테스트를 수행합니다.
if __name__ == "__main__":
    run_tests()
