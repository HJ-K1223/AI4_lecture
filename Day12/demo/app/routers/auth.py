"""회원가입·로그인·로그아웃 화면과 폼 처리."""

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.auth import optional_member, required_member
from app.core.db import get_db
from app.core.security import establish_login, safe_next
from app.core.templates import render
from app.models import Member
from app.schemas.auth import LoginInput, RegisterInput
from app.services.auth import authenticate_member, register_member

router = APIRouter()


@router.get("/register")
def register_page(request: Request, member: Member | None = Depends(optional_member)):
    next_path = safe_next(request.query_params.get("next"))
    if member:
        return RedirectResponse(next_path, status_code=303)
    return render(request, "register.html", next_path=next_path, error=None, values={})


@router.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    next_path = safe_next(form.get("next"))
    values = {key: str(form.get(key, "")) for key in ("email", "name", "phone", "address")}
    try:
        data = RegisterInput.model_validate({
            **values, "password": form.get("password"), "password_confirm": form.get("password_confirm")
        })
    except ValidationError:
        return render(request, "register.html", status_code=422, next_path=next_path, values=values,
                      error="이메일·이름·입력 길이를 확인하고, 같은 비밀번호를 12~128자로 입력하세요.")
    # 해시·DB 작업은 워커 스레드에서 수행하여 이벤트 루프를 막지 않습니다.
    try:
        await run_in_threadpool(register_member, db, data)
    except IntegrityError:
        await run_in_threadpool(db.rollback)
        return render(request, "register.html", status_code=409, next_path=next_path, values=values,
                      error="사용할 수 없는 이메일입니다. 다른 이메일을 입력하거나 로그인하세요.")
    request.session.clear()
    return RedirectResponse("/login?" + urlencode({"next": next_path, "registered": "1"}), status_code=303)


@router.get("/login")
def login_page(request: Request, member: Member | None = Depends(optional_member)):
    next_path = safe_next(request.query_params.get("next"))
    if member:
        return RedirectResponse(next_path, status_code=303)
    return render(request, "login.html", next_path=next_path, error=None, email="",
                  registered=request.query_params.get("registered") == "1")


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    next_path = safe_next(form.get("next"))
    email = str(form.get("email", ""))
    try:
        data = LoginInput.model_validate({"email": email, "password": form.get("password")})
    except ValidationError:
        return render(request, "login.html", status_code=422, next_path=next_path, email=email,
                      registered=False, error="올바른 이메일과 비밀번호를 입력하세요.")
    member = await run_in_threadpool(authenticate_member, db, str(data.email), data.password.get_secret_value())
    if member is None:
        return render(request, "login.html", status_code=401, next_path=next_path, email=email,
                      registered=False, error="이메일 또는 비밀번호를 확인하세요.")
    establish_login(request, member)
    return RedirectResponse(safe_next(next_path), status_code=303)


@router.post("/logout")
def logout(request: Request, member: Member = Depends(required_member), db: Session = Depends(get_db)):
    current = db.scalar(select(Member).where(Member.id == member.id).with_for_update())
    # 서명 쿠키가 재사용되어도 로그인할 수 없도록 모든 기존 세션의 버전을 폐기합니다.
    current.auth_version += 1
    db.commit()
    request.session.clear()
    return RedirectResponse("/products", status_code=303)


@router.get("/api/auth/me")
def me(member: Member = Depends(required_member)):
    return {"id": str(member.id), "email": member.email, "name": member.name}
