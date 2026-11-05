from django.conf import settings
from django.db import models

class BannedTerm(models.Model):
    pattern = models.CharField(max_length=500)
    match_type = models.CharField(max_length=10, default="KEYWORD")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    source_url = models.TextField(null=True, blank=True)
    source_note = models.TextField(null=True, blank=True)
    source_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "banned_terms"
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["match_type", "pattern"], name="term_type_pattern_unique"),
                       models.CheckConstraint(condition=models.Q(match_type="KEYWORD"), name="term_keyword_only"),
                       models.CheckConstraint(condition=~models.Q(pattern__regex=r"^\s*$"), name="term_pattern_not_blank")]

