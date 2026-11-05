import unicodedata
import regex
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from .models import BannedTerm

MAX_TERMS = 500

def normalize(value):
    return unicodedata.normalize("NFKC", value).casefold()

def normalized_with_positions(value):
    parts, positions = [], []
    # Grapheme clusters preserve the original span when NFKC composes/expands characters.
    for match in regex.finditer(r"\X", value):
        part = normalize(match.group())
        parts.append(part)
        positions.extend([(match.start(), match.end())] * len(part))
    return "".join(parts), positions

class Masker:
    def __init__(self, patterns):
        self.patterns = [normalize(p) for p in patterns if p]
    @classmethod
    def from_db(cls):
        return cls(list(BannedTerm.objects.values_list("pattern", flat=True)))
    def mask(self, value):
        normalized, positions = normalized_with_positions(value)
        spans = []
        for pattern in self.patterns:
            start = 0
            while True:
                found = normalized.find(pattern, start)
                if found < 0:
                    break
                spans.append((positions[found][0], positions[found + len(pattern) - 1][1]))
                start = found + 1
        if not spans:
            return value
        merged = []
        for start, end in sorted(spans):
            if merged and start < merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        output, cursor = [], 0
        for start, end in merged:
            output.extend([value[cursor:start], "***"])
            cursor = end
        return "".join(output) + value[cursor:]

@transaction.atomic
def add_terms(rows, creator=None):
    # All registration paths share a transaction lock, including empty-table inserts.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [72401321])
    existing = set(BannedTerm.objects.values_list("pattern", flat=True))
    pending = {}
    for row in rows:
        if row.get("match_type", "KEYWORD") != "KEYWORD":
            raise ValidationError("KEYWORD 유형만 지원합니다.")
        pattern = normalize(row["pattern"].strip())
        if not pattern or len(pattern) > 500:
            raise ValidationError("키워드는 공백이 아닌 1~500자여야 합니다.")
        if pattern not in existing:
            pending[pattern] = {**row, "pattern": pattern, "match_type": "KEYWORD"}
    if len(existing) + len(pending) > MAX_TERMS:
        raise ValidationError("금칙어는 최대 500개까지 등록할 수 있습니다.")
    for row in pending.values():
        BannedTerm.objects.create(created_by=creator, **row)
    return len(pending)

