"""인증 의존성. 모든 요청에서 회원 상태와 인증 버전을 검증합니다."""

from uuid import UUID

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_optional_db
from app.models import Member


class LoginRequired(Exception):
    pass


def optional_member(request: Request, db: Session | None = Depends(get_optional_db)) -> Member | None:
    member_id = request.session.get("member_id")
    if member_id is None:
        return None
    try:
        member_uuid = UUID(member_id)
    except (ValueError, TypeError, AttributeError):
        request.session.clear()
        return None
    if db is None:
        raise HTTPException(status_code=503, detail="현재 서비스를 이용할 수 없습니다. 잠시 후 다시 시도하세요.")
    member = db.get(Member, member_uuid)
    version = request.session.get("auth_version")
    if member is None or member.status != "ACTIVE" or type(version) is not int or member.auth_version != version:
        request.session.clear()
        return None
    request.state.member = member
    return member


def required_member(member: Member | None = Depends(optional_member)) -> Member:
    if member is None:
        raise LoginRequired()
    return member
