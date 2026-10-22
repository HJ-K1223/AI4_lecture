"""06장 학생 실습: 부분수정과 직렬화 차이 확인."""
from pydantic import BaseModel


class Profile(BaseModel):
    nickname: str
    bio: str | None = None
    active: bool = True


class ProfilePatch(BaseModel):
    nickname: str | None = None
    bio: str | None = None
    active: bool | None = None


def main() -> None:
    stored = Profile(nickname='old', bio='소개 글', active=True)
    patch = ProfilePatch(nickname='new')
    # TODO 1: exclude_unset=True로 실제 변경 필드만 출력
    # TODO 2: dict 병합 후 Profile.model_validate 호출
    # TODO 3: ProfilePatch(bio=None)과 ProfilePatch()의 차이 출력
    print('기존:', stored.model_dump(), '패치:', patch)


if __name__ == '__main__':
    main()