from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower, Trim

class MemberManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        user = self.model(email=email.strip().lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

class Member(AbstractBaseUser):
    email = models.EmailField(max_length=254, unique=True)
    nickname = models.CharField(max_length=50)
    password = models.CharField(max_length=255, db_column="password_hash")
    role = models.CharField(max_length=10, choices=[("USER", "회원"), ("ADMIN", "관리자")], default="USER")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]
    objects = MemberManager()
    class Meta:
        db_table = "members"
        constraints = [models.CheckConstraint(condition=models.Q(role__in=["USER", "ADMIN"]), name="member_role_valid"),
                       models.CheckConstraint(condition=~models.Q(nickname__regex=r"^\s*$"), name="member_nickname_not_blank"),
                       models.CheckConstraint(condition=models.Q(email=Lower(Trim("email"))) & ~models.Q(email=""), name="member_email_normalized")]
    def __str__(self):
        return self.nickname

