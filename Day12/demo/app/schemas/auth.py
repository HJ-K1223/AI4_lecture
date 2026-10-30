"""인증 입력값. 비밀번호는 검증 오류·표현에 노출하지 않습니다."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator, model_validator


class LoginInput(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)
    email: EmailStr = Field(max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class RegisterInput(LoginInput):
    password: SecretStr = Field(min_length=12, max_length=128)
    password_confirm: SecretStr = Field(min_length=12, max_length=128)
    name: str = Field(min_length=1, max_length=80)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)

    @field_validator("name", "phone", "address", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password.get_secret_value() != self.password_confirm.get_secret_value():
            raise ValueError("비밀번호 확인이 일치하지 않습니다.")
        return self
