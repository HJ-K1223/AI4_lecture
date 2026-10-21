"""리스트에서 '불량'을 모두 제거하는 예제."""


def remove_defective_items(items: list[str]) -> list[str]:
    # 원본을 순회하면서 삭제하면 다음 항목을 건너뛸 수 있습니다.
    # '불량'이 아닌 항목만 순서대로 모아 새 리스트를 만듭니다.
    return [item for item in items if item != "불량"]


if __name__ == "__main__":
    items = ["정상", "불량", "불량", "정상"]

    # 불량을 제외한 새 리스트를 items에 저장합니다.
    items = remove_defective_items(items)
    print(f"검수결과 : {items}")

    # 연속된 불량, 전체 불량, 불량 없음, 빈 리스트 등을 확인합니다.
    assert items == ["정상", "정상"]
    assert remove_defective_items(["불량", "불량"]) == []
    assert remove_defective_items(["정상", "정상"]) == ["정상", "정상"]
    assert remove_defective_items([]) == []
    assert remove_defective_items(["불량", "정상", "불량"]) == ["정상"]
    assert remove_defective_items(["정상", "보류", "불량"]) == ["정상", "보류"]
    print("6개 테스트 모두 통과!")
