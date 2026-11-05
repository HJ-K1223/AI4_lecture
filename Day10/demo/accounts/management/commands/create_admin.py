import getpass
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from accounts.models import Member

class Command(BaseCommand):
    help = "숨김 비밀번호 입력으로 ADMIN 계정을 생성합니다. 기존 계정을 승격하지 않습니다."
    def add_arguments(self, parser):
        parser.add_argument("--email")
        parser.add_argument("--nickname")
    def handle(self, *args, **options):
        email = (options["email"] or input("Email: ")).strip().lower()
        nickname = (options["nickname"] or input("Nickname: ")).strip()
        try:
            validate_email(email)
            if not nickname or len(nickname) > 50 or Member.objects.filter(email=email).exists():
                raise CommandError("이메일이 중복되었거나 닉네임이 잘못되었습니다.")
            password = getpass.getpass("Password: ")
            if password != getpass.getpass("Password again: "):
                raise CommandError("비밀번호가 일치하지 않습니다.")
            validate_password(password, Member(email=email, nickname=nickname))
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error
        Member.objects.create_user(email, password, nickname=nickname, role="ADMIN")
        self.stdout.write(self.style.SUCCESS("관리자를 생성했습니다."))

