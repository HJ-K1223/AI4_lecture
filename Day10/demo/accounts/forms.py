from django import forms
from django.contrib.auth import authenticate, password_validation
from .models import Member

class SignupForm(forms.ModelForm):
    password = forms.CharField(label="비밀번호 (10자 이상)", strip=False, widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="비밀번호 확인", strip=False, widget=forms.PasswordInput)
    class Meta:
        model = Member
        fields = ["email", "nickname"]
        labels = {"email": "이메일", "nickname": "닉네임"}
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Member.objects.filter(email=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email
    def clean(self):
        data = super().clean()
        if data.get("password") != data.get("password_confirm"):
            self.add_error("password_confirm", "비밀번호가 일치하지 않습니다.")
        if data.get("password"):
            try:
                password_validation.validate_password(data["password"], Member(email=data.get("email", ""), nickname=data.get("nickname", "")))
            except forms.ValidationError as error:
                self.add_error("password", error)
        return data
    def save(self):
        return Member.objects.create_user(self.cleaned_data["email"], self.cleaned_data["password"], nickname=self.cleaned_data["nickname"])

class LoginForm(forms.Form):
    email = forms.EmailField(label="이메일")
    password = forms.CharField(label="비밀번호", strip=False, widget=forms.PasswordInput)
    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)
    def clean(self):
        data = super().clean()
        if data.get("email") and data.get("password"):
            self.user = authenticate(self.request, email=data["email"].strip().lower(), password=data["password"])
            if self.user is None:
                raise forms.ValidationError("이메일 또는 비밀번호를 확인해 주세요.")
        return data

