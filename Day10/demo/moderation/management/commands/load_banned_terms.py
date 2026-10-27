import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from moderation.services import add_terms

class Command(BaseCommand):
    help = "명시적으로 seed를 로드합니다. 중복은 건너뛰며 자동 실행하지 않습니다."
    def add_arguments(self, parser):
        parser.add_argument("path")
    def handle(self, *args, **options):
        try:
            rows = json.loads(Path(options["path"]).read_text(encoding="utf-8"))
            if not isinstance(rows, list) or len(rows) > 200:
                raise ValueError("초기 seed는 배열이며 200개 이하여야 합니다.")
            validated = []
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("pattern"), str):
                    raise ValueError("각 규칙에 문자열 pattern이 필요합니다.")
                item = {key: row.get(key) for key in ("pattern", "source_url", "source_note")}
                item["match_type"] = row.get("match_type", "KEYWORD")
                stamp = row.get("source_checked_at")
                item["source_checked_at"] = parse_datetime(stamp) if stamp else None
                if stamp and item["source_checked_at"] is None:
                    raise ValueError("출처 조회일은 ISO datetime 형식이어야 합니다.")
                validated.append(item)
            count = add_terms(validated)
        except (OSError, ValueError, TypeError, ValidationError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"{count}개 추가, 중복은 건너뛰었습니다."))

