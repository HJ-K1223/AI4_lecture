# 방명록 UI 변경 내역

## 요청 반영

| 위치 | 변경 전 | 변경 후 |
| --- | --- | --- |
| 흰색 입력 박스 상단 제목 | 인사 남기기 | 방명록에 인사를 남겨주세요 |
| 글 남기기 버튼 배경 | 진한 초록 `#345b43` | 연파랑 `#b9e2f7` |
| 버튼에 마우스를 올렸을 때 | 진한 초록 `#254832` | 조금 진한 연파랑 `#a2d5ef` |
| 버튼 글자 | 흰색 | 가독성을 위한 짙은 남색 `#203d50` |

수정 파일은 `templates/index.html`, `static/style.css`입니다. 참고 이미지의 연파랑 느낌을 버튼에 반영했으며 이미지를 복사하거나 외부 이미지·라이브러리를 추가하지 않았습니다. 사용자가 지정한 두 가지 변경에 맞춰 기존 배치와 방명록 기능을 유지했습니다.

## 확인

로컬 파일의 제목 문구, 버튼 기본·hover 배경색, 글자색을 확인했습니다. 실제 브라우저 화면과 배포 사이트 적용 여부는 확인하지 않았습니다.

## 서버 반영 방법

Windows PowerShell에서 아래 명령을 한 줄씩 실행합니다.

```powershell
cd C:\AI4
```

```powershell
C:\Windows\System32\OpenSSH\scp.exe -r .\Day1_Day8\templates .\Day1_Day8\static hjk@ssh-hjk.alwaysdata.net:/home/hjk/guestbook/
```

SSH 계정 비밀번호를 입력합니다. 업로드 후 alwaysdata 관리자 `Web > Sites`에서 해당 사이트를 재시작합니다. HTML 템플릿은 서버 시작 시 읽으므로 재시작이 필요합니다.

https://hjk.alwaysdata.net/ 에서 Ctrl+F5로 새로고침한 뒤 새 제목과 연파랑 버튼을 확인합니다. 이번 변경에 Python 코드·DB·라이브러리 재설치는 필요 없습니다.
