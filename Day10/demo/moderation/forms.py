from django import forms
from .services import normalize
from .models import BannedTerm
class TermForm(forms.Form):
    pattern = forms.CharField(label="금칙어", max_length=500)
    def clean_pattern(self):
        pattern = normalize(self.cleaned_data["pattern"].strip())
        if not pattern or len(pattern) > 500:
            raise forms.ValidationError("정규화한 키워드는 1~500자여야 합니다.")
        if BannedTerm.objects.filter(pattern=pattern).exists():
            raise forms.ValidationError("이미 등록된 키워드입니다.")
        return pattern

