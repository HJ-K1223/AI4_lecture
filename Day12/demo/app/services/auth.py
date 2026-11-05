"""회원가입·로그인 비즈니스 로직."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import PASSWORD_HASHER, hash_password, verify_password
from app.models import Member
from app.schemas.auth import RegisterInput

# 없는 이메일에도 동일한 해시 검증을 수행해 응답 시간 차이를 줄입니다.
DUMMY_PASSWORD_HASH = hash_password("dummy-password-not-used-for-login")


def register_member(db: Session, data: RegisterInput) -> Member:
    member = Member(
        email=str(data.email), password_hash=hash_password(data.password.get_secret_value()),
        name=data.name, phone=data.phone or None, address=data.address or None,
    )
    db.add(member)
    db.commit()
    return member


def authenticate_member(db: Session, email: str, password: str) -> Member | None:
    member = db.scalar(select(Member).where(Member.email == email).with_for_update())
    valid = verify_password(member.password_hash if member else DUMMY_PASSWORD_HASH, password)
    if not valid or member is None or member.status != "ACTIVE":
        return None
    if PASSWORD_HASHER.check_needs_rehash(member.password_hash):
        member.password_hash = hash_password(password)
    db.commit()
    return member
